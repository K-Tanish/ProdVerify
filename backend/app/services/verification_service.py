from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.config import SCAN_ALERT_THRESHOLD
from backend.app.models.product import Product
from backend.app.models.retailer import Retailer
from backend.app.models.scan_history import ScanHistory

DISCLAIMER_TEXT = (
    "Verification is based on recorded manufacturer data and current risk indicators. "
    "A valid match confirms the code exists in the registry, but physical inspection "
    "of tamper-evident security packaging and purchasing from an authorized retailer "
    "remain essential to ensure authenticity."
)


def verify_external_token(
    session: Session,
    token: str,
    reported_retailer_id: Optional[int] = None,
    scan_location: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Perform pre-purchase external QR verification for a given token.
    Resolves external tokens strictly through the database.
    Evaluates:
      - Product status (IN_STOCK vs SOLD / BLOCKED)
      - Existing warranty registration
      - Intended retailer vs customer-reported retailer
      - Scan frequency threshold
    Logs the scan event into Scan_History (including unknown tokens).
    Guarantees the current scan is counted exactly once.
    """
    cleaned_token = str(token).strip() if token else ""
    if not cleaned_token:
        # Log invalid empty token attempt
        scan = ScanHistory(
            product_id=None,
            scan_type="EXTERNAL_VERIFICATION",
            scan_location=scan_location,
            result="INVALID",
            risk_reason="Empty or missing token",
        )
        session.add(scan)
        session.commit()
        return {
            "result": "INVALID",
            "explanation": "No verification token provided.",
            "risk_warnings": ["Missing token"],
            "scan_count": 0,
            "disclaimer": DISCLAIMER_TEXT,
            "product": None,
            "intended_retailer": None,
            "reported_evidence": None,
        }

    # 1. Lookup product by external QR token
    product = session.query(Product).filter_by(external_qr_token=cleaned_token).first()

    # If not found by external token, check if it's an internal token
    if not product:
        internal_product = (
            session.query(Product).filter_by(internal_qr_token=cleaned_token).first()
        )
        if internal_product:
            warning = (
                "Internal registration QR scanned on external verification endpoint. "
                "This code is intended for post-purchase warranty registration, not pre-purchase verification."
            )
            scan = ScanHistory(
                product_id=internal_product.product_id,
                scan_type="EXTERNAL_VERIFICATION",
                scan_location=scan_location,
                result="SUSPICIOUS",
                risk_reason=warning,
            )
            session.add(scan)
            session.commit()

            current_count = (
                session.query(ScanHistory)
                .filter_by(
                    product_id=internal_product.product_id,
                    scan_type="EXTERNAL_VERIFICATION",
                )
                .count()
            )

            ret = internal_product.intended_retailer
            retailer_data = (
                {
                    "retailer_id": ret.retailer_id,
                    "retailer_name": ret.retailer_name,
                    "address": ret.address,
                    "city": ret.city,
                    "state": ret.state,
                }
                if ret
                else None
            )

            return {
                "result": "SUSPICIOUS",
                "explanation": (
                    "This code belongs to a valid product in the registry, but it is an internal warranty code, "
                    "not the external verification code. Please look for the verification code printed outside the packaging."
                ),
                "risk_warnings": [warning],
                "scan_count": current_count,
                "disclaimer": DISCLAIMER_TEXT,
                "product": {
                    "product_id": internal_product.product_id,
                    "product_name": internal_product.product_name,
                    "serial_number": internal_product.serial_number,
                    "product_status": internal_product.product_status,
                    "manufacturing_location": internal_product.manufacturing_location,
                    "registration_status": (
                        "REGISTERED"
                        if internal_product.warranty_registration
                        else "UNREGISTERED"
                    ),
                },
                "intended_retailer": retailer_data,
                "reported_evidence": {
                    "reported_retailer_id": reported_retailer_id,
                    "scan_location": scan_location,
                },
            }

        # Completely unknown token
        scan = ScanHistory(
            product_id=None,
            scan_type="EXTERNAL_VERIFICATION",
            scan_location=scan_location,
            result="INVALID",
            risk_reason="Unrecognized QR token",
        )
        session.add(scan)
        session.commit()

        return {
            "result": "INVALID",
            "explanation": "The scanned QR token does not match any genuine product record in the manufacturer registry.",
            "risk_warnings": ["Unrecognized QR token: this code was not issued by an authorized manufacturer."],
            "scan_count": 0,
            "disclaimer": DISCLAIMER_TEXT,
            "product": None,
            "intended_retailer": None,
            "reported_evidence": {
                "reported_retailer_id": reported_retailer_id,
                "scan_location": scan_location,
            },
        }

    # 2. Valid external product match found - gather risk indicators
    risk_warnings: List[str] = []

    # Check product status
    if product.product_status == "BLOCKED":
        risk_warnings.append(
            "Product status is BLOCKED: The manufacturer has flagged this item as recalled, lost, or compromised."
        )
    elif product.product_status == "SOLD":
        risk_warnings.append(
            "Product status is marked as SOLD: This item has already been purchased previously."
        )

    # Check warranty registration
    if product.warranty_registration:
        risk_warnings.append(
            f"Warranty already active: This unit was registered on {product.warranty_registration.purchase_date} "
            f"under status '{product.warranty_registration.warranty_status}'."
        )

    # Check retailer evidence
    intended_ret = product.intended_retailer
    if reported_retailer_id is not None:
        reported_ret = session.query(Retailer).filter_by(retailer_id=reported_retailer_id).first()
        reported_name = reported_ret.retailer_name if reported_ret else f"Retailer ID {reported_retailer_id}"
        if not intended_ret or intended_ret.retailer_id != reported_retailer_id:
            intended_desc = (
                f"'{intended_ret.retailer_name}' in {intended_ret.city}, {intended_ret.state}"
                if intended_ret
                else "Unassigned"
            )
            risk_warnings.append(
                f"Retailer mismatch (self-reported evidence): You reported scanning this at '{reported_name}', "
                f"but this unit was designated by the manufacturer for authorized distribution at {intended_desc}. "
                "A mismatch can indicate diversion or parallel gray-market importation."
            )

    # Check prior scans before recording the current scan
    prior_scans = (
        session.query(ScanHistory)
        .filter_by(product_id=product.product_id, scan_type="EXTERNAL_VERIFICATION")
        .count()
    )
    current_scan_number = prior_scans + 1

    if current_scan_number > SCAN_ALERT_THRESHOLD:
        risk_warnings.append(
            f"Elevated scan count ({current_scan_number} scans recorded): This QR code has been verified {current_scan_number} times. "
            f"While multiple scans can occur during routine customer browsing or display inspection, "
            f"an unusually high number of scans may indicate that the external packaging QR code has been duplicated or copied."
        )

    # Determine final result categorization
    if risk_warnings:
        result_category = "SUSPICIOUS"
        explanation = (
            "Product record located in manufacturer database, but one or more security indicators require attention."
        )
    else:
        result_category = "VERIFIED"
        explanation = (
            "Valid product record verified against the manufacturer database with no security discrepancies detected."
        )

    # Snapshot attributes before session commit
    prod_id = product.product_id
    prod_name = product.product_name
    prod_serial = product.serial_number
    prod_status = product.product_status
    prod_mfg_loc = product.manufacturing_location
    prod_reg_status = "REGISTERED" if product.warranty_registration else "UNREGISTERED"

    retailer_info = (
        {
            "retailer_id": intended_ret.retailer_id,
            "retailer_name": intended_ret.retailer_name,
            "address": intended_ret.address,
            "city": intended_ret.city,
            "state": intended_ret.state,
        }
        if intended_ret
        else None
    )

    # 3. Record the current scan attempt in Scan_History
    scan = ScanHistory(
        product_id=prod_id,
        scan_type="EXTERNAL_VERIFICATION",
        scan_location=scan_location,
        result=result_category,
        risk_reason="; ".join(risk_warnings) if risk_warnings else None,
    )
    session.add(scan)
    session.commit()

    # 4. Total verification count (counted exactly once)
    total_scans = (
        session.query(ScanHistory)
        .filter_by(product_id=prod_id, scan_type="EXTERNAL_VERIFICATION")
        .count()
    )

    return {
        "result": result_category,
        "explanation": explanation,
        "risk_warnings": risk_warnings,
        "scan_count": total_scans,
        "disclaimer": DISCLAIMER_TEXT,
        "product": {
            "product_id": prod_id,
            "product_name": prod_name,
            "serial_number": prod_serial,
            "product_status": prod_status,
            "manufacturing_location": prod_mfg_loc,
            "registration_status": prod_reg_status,
        },
        "intended_retailer": retailer_info,
        "reported_evidence": {
            "reported_retailer_id": reported_retailer_id,
            "scan_location": scan_location,
        },
    }

