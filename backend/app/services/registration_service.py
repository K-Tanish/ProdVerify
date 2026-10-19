import datetime
import re
from typing import Any, Dict, Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.config import DEFAULT_WARRANTY_DAYS
from backend.app.models.product import Product
from backend.app.models.retailer import Retailer
from backend.app.models.scan_history import ScanHistory
from backend.app.models.warranty_registration import WarrantyRegistration


class RegistrationError(Exception):
    def __init__(self, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def resolve_internal_token(session: Session, token: str) -> Dict[str, Any]:
    """
    Resolve an internal QR token to its product and check registration eligibility.
    Returns product info, eligibility status, or raises RegistrationError.
    """
    cleaned_token = str(token).strip() if token else ""
    if not cleaned_token:
        raise RegistrationError("No registration token provided.", status_code=400)

    # 1. Check if token matches internal_qr_token
    product = session.query(Product).filter_by(internal_qr_token=cleaned_token).first()

    if not product:
        # Check if external token was erroneously used
        ext_product = session.query(Product).filter_by(external_qr_token=cleaned_token).first()
        if ext_product:
            raise RegistrationError(
                "This code is an external verification code. "
                "Please scan the internal warranty QR code found inside the product packaging or documentation.",
                status_code=400,
                details={"token_type": "EXTERNAL", "product_id": ext_product.product_id},
            )
        raise RegistrationError(
            "The scanned warranty QR code does not match any genuine product record.",
            status_code=404,
            details={"token_type": "UNKNOWN"},
        )

    # 2. Check if product is BLOCKED
    if product.product_status == "BLOCKED":
        raise RegistrationError(
            f"Registration blocked: Product '{product.product_name}' (ID: {product.product_id}) "
            "has been flagged as blocked or compromised by the manufacturer.",
            status_code=403,
            details={"product_id": product.product_id, "status": "BLOCKED"},
        )

    # 3. Check if product already has an active warranty registration
    if product.warranty_registration:
        warr = product.warranty_registration
        raise RegistrationError(
            f"This product is already registered. Warranty is '{warr.warranty_status}' "
            f"for customer '{warr.customer_name}' until {warr.warranty_end_date}.",
            status_code=409,
            details={
                "product_id": product.product_id,
                "already_registered": True,
                "registration_id": warr.registration_id,
                "customer_name": warr.customer_name,
                "warranty_status": warr.warranty_status,
                "warranty_end_date": str(warr.warranty_end_date),
            },
        )

    return {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "serial_number": product.serial_number,
        "manufacturing_location": product.manufacturing_location,
        "intended_retailer_id": product.intended_retailer_id,
        "product_status": product.product_status,
        "eligible": True,
    }


def register_warranty(
    session: Session,
    token: str,
    customer_name: str,
    email: str,
    retailer_id: int,
    purchase_price: Optional[float],
    purchase_date: str,
) -> Dict[str, Any]:
    """
    Execute atomic warranty registration and product status update:
    1. Validates submitted parameters.
    2. Resolves internal token and verifies eligibility.
    3. Validates retailer existence.
    4. Inserts Warranty_Registrations record.
    5. Updates product status to 'SOLD'.
    6. Logs the event in Scan_History.
    7. Commits as a single atomic transaction.
    """
    # Parameter validations
    name_clean = str(customer_name).strip() if customer_name else ""
    if not name_clean:
        raise RegistrationError("Customer name is required and cannot be empty.", status_code=422)

    email_clean = str(email).strip() if email else ""
    if not email_clean or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email_clean):
        raise RegistrationError("A valid email address is required.", status_code=422)

    if purchase_price is not None:
        try:
            purchase_price = float(purchase_price)
            if purchase_price < 0:
                raise RegistrationError("Purchase price cannot be negative.", status_code=422)
        except (ValueError, TypeError):
            raise RegistrationError("Purchase price must be a valid number.", status_code=422)

    try:
        p_date = datetime.date.fromisoformat(str(purchase_date).strip())
    except Exception:
        raise RegistrationError("Purchase date must be in YYYY-MM-DD format.", status_code=422)

    # Future date check
    today = datetime.date.today()
    if p_date > today + datetime.timedelta(days=1):
        raise RegistrationError("Purchase date cannot be in the future.", status_code=422)

    # Retailer check
    retailer = session.query(Retailer).filter_by(retailer_id=retailer_id).first()
    if not retailer:
        raise RegistrationError(f"Selected retailer (ID: {retailer_id}) does not exist.", status_code=404)

    # Resolve internal token
    cleaned_token = str(token).strip() if token else ""
    product = session.query(Product).filter_by(internal_qr_token=cleaned_token).first()
    if not product:
        ext_product = session.query(Product).filter_by(external_qr_token=cleaned_token).first()
        if ext_product:
            raise RegistrationError(
                "This code is an external verification code, not an internal warranty registration code.",
                status_code=400,
            )
        raise RegistrationError("The scanned warranty QR code does not match any known product.", status_code=404)

    if product.product_status == "BLOCKED":
        raise RegistrationError("This product is BLOCKED and cannot be registered.", status_code=403)

    if product.warranty_registration:
        raise RegistrationError(
            f"This product is already registered (Warranty Status: {product.warranty_registration.warranty_status}).",
            status_code=409,
        )

    # Calculate warranty dates
    warranty_start = p_date
    warranty_end = p_date + datetime.timedelta(days=DEFAULT_WARRANTY_DAYS)

    # Perform atomic transaction
    try:
        # 1. Create warranty registration
        warranty = WarrantyRegistration(
            product_id=product.product_id,
            customer_name=name_clean,
            email=email_clean,
            retailer_id=retailer.retailer_id,
            purchase_price=purchase_price,
            purchase_date=p_date,
            warranty_status="ACTIVE",
            warranty_start_date=warranty_start,
            warranty_end_date=warranty_end,
        )
        session.add(warranty)

        # 2. Update product status to SOLD
        product.product_status = "SOLD"

        # 3. Log internal registration in Scan_History
        scan_event = ScanHistory(
            product_id=product.product_id,
            scan_type="INTERNAL_REGISTRATION",
            scan_location=f"{retailer.city}, {retailer.state}",
            result="VERIFIED",
            risk_reason="Successful warranty registration and activation",
        )
        session.add(scan_event)

        session.commit()
    except IntegrityError as e:
        session.rollback()
        raise RegistrationError(
            "This product has already been registered or a concurrent registration conflict occurred.",
            status_code=409,
        ) from e
    except Exception as e:
        session.rollback()
        raise RegistrationError(f"Registration failed: {str(e)}", status_code=500) from e

    return {
        "success": True,
        "message": "Warranty successfully registered and activated.",
        "registration": {
            "registration_id": warranty.registration_id,
            "customer_name": warranty.customer_name,
            "email": warranty.email,
            "purchase_price": warranty.purchase_price,
            "purchase_date": str(warranty.purchase_date),
            "warranty_status": warranty.warranty_status,
            "warranty_start_date": str(warranty.warranty_start_date),
            "warranty_end_date": str(warranty.warranty_end_date),
        },
        "product": {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "serial_number": product.serial_number,
            "product_status": product.product_status,
        },
        "retailer": {
            "retailer_id": retailer.retailer_id,
            "retailer_name": retailer.retailer_name,
            "city": retailer.city,
            "state": retailer.state,
        },
    }
