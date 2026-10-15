import datetime
import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.models.manufacturer import Manufacturer
from backend.app.models.retailer import Retailer
from backend.app.models.product import Product
from backend.app.models.scan_history import ScanHistory
from backend.app.models.warranty_registration import WarrantyRegistration


def test_foreign_key_enforcement(db_session):
    """Verify that foreign key constraints are strictly enforced in SQLite."""
    # Attempt to create product with nonexistent manufacturer
    invalid_product = Product(
        product_id="P_ORPHAN",
        product_name="Orphan Product",
        manufacturer_id=99999,  # Nonexistent
        serial_number="SN-ORPHAN",
        external_qr_token="EXT-ORPHAN",
        internal_qr_token="INT-ORPHAN",
    )
    db_session.add(invalid_product)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_manufacturer_products_relationship(db_session):
    """Verify Manufacturer -> Products relationship."""
    mfg = Manufacturer(manufacturer_name="Rel Mfg")
    db_session.add(mfg)
    db_session.flush()

    prod1 = Product(
        product_id="P_REL_1",
        product_name="Product Rel 1",
        manufacturer_id=mfg.manufacturer_id,
        serial_number="SN-REL-1",
        external_qr_token="EXT-REL-1",
        internal_qr_token="INT-REL-1",
    )
    prod2 = Product(
        product_id="P_REL_2",
        product_name="Product Rel 2",
        manufacturer_id=mfg.manufacturer_id,
        serial_number="SN-REL-2",
        external_qr_token="EXT-REL-2",
        internal_qr_token="INT-REL-2",
    )
    db_session.add_all([prod1, prod2])
    db_session.commit()

    assert len(mfg.products) == 2
    assert prod1.manufacturer.manufacturer_name == "Rel Mfg"


def test_scan_history_relationship_and_nullable_product(db_session):
    """Verify ScanHistory links to Product, and supports null product_id for unknown-token attempts."""
    mfg = Manufacturer(manufacturer_name="Scan Mfg")
    db_session.add(mfg)
    db_session.flush()

    prod = Product(
        product_id="P_SCAN",
        product_name="Product Scan",
        manufacturer_id=mfg.manufacturer_id,
        serial_number="SN-SCAN-1",
        external_qr_token="EXT-SCAN-1",
        internal_qr_token="INT-SCAN-1",
    )
    db_session.add(prod)
    db_session.flush()

    # 1. Valid scan linked to product
    scan1 = ScanHistory(
        product_id=prod.product_id,
        scan_type="EXTERNAL_VERIFICATION",
        result="VERIFIED",
    )
    # 2. Unknown-token scan without product_id
    scan_unknown = ScanHistory(
        product_id=None,
        scan_type="EXTERNAL_VERIFICATION",
        result="INVALID",
        risk_reason="Token not found in database",
    )
    db_session.add_all([scan1, scan_unknown])
    db_session.commit()

    assert len(prod.scans) == 1
    assert prod.scans[0].result == "VERIFIED"
    assert scan_unknown.product is None


def test_warranty_registration_one_to_one(db_session):
    """Verify that a product can only have one warranty registration."""
    mfg = Manufacturer(manufacturer_name="Warr Mfg")
    ret = Retailer(retailer_name="Warr Retailer", city="Dallas", state="TX")
    db_session.add_all([mfg, ret])
    db_session.flush()

    prod = Product(
        product_id="P_WARR_1",
        product_name="Product Warr 1",
        manufacturer_id=mfg.manufacturer_id,
        serial_number="SN-WARR-1",
        external_qr_token="EXT-WARR-1",
        internal_qr_token="INT-WARR-1",
        intended_retailer_id=ret.retailer_id,
    )
    db_session.add(prod)
    db_session.flush()

    today = datetime.date.today()
    reg1 = WarrantyRegistration(
        product_id=prod.product_id,
        customer_name="Bob Smith",
        email="bob@example.com",
        retailer_id=ret.retailer_id,
        purchase_price=299.99,
        purchase_date=today,
        warranty_status="ACTIVE",
        warranty_start_date=today,
        warranty_end_date=today + datetime.timedelta(days=365),
    )
    db_session.add(reg1)
    db_session.commit()

    assert prod.warranty_registration is not None
    assert prod.warranty_registration.customer_name == "Bob Smith"

    # Attempt second registration for the same product
    reg2 = WarrantyRegistration(
        product_id=prod.product_id,
        customer_name="Charlie Brown",
        email="charlie@example.com",
        retailer_id=ret.retailer_id,
        purchase_price=250.00,
        purchase_date=today,
        warranty_status="ACTIVE",
        warranty_start_date=today,
        warranty_end_date=today + datetime.timedelta(days=365),
    )
    db_session.add(reg2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
