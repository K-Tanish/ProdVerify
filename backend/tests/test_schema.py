import datetime
import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from backend.app.models.manufacturer import Manufacturer
from backend.app.models.retailer import Retailer
from backend.app.models.product import Product
from backend.app.models.scan_history import ScanHistory
from backend.app.models.warranty_registration import WarrantyRegistration


def test_five_tables_exist(engine):
    """Verify that all five specified tables exist in the schema."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    expected = {
        "manufacturers",
        "retailers",
        "products",
        "scan_history",
        "warranty_registrations",
    }
    assert expected.issubset(set(table_names)), f"Missing tables. Found: {table_names}"


def test_primary_keys_and_indexes(engine):
    """Verify primary keys and key indexes on each table."""
    inspector = inspect(engine)

    # Manufacturers
    pk_mfg = inspector.get_pk_constraint("manufacturers")
    assert pk_mfg["constrained_columns"] == ["manufacturer_id"]

    # Retailers
    pk_ret = inspector.get_pk_constraint("retailers")
    assert pk_ret["constrained_columns"] == ["retailer_id"]

    # Products
    pk_prod = inspector.get_pk_constraint("products")
    assert pk_prod["constrained_columns"] == ["product_id"]

    # Scan History
    pk_scan = inspector.get_pk_constraint("scan_history")
    assert pk_scan["constrained_columns"] == ["scan_id"]

    # Warranty Registrations
    pk_warr = inspector.get_pk_constraint("warranty_registrations")
    assert pk_warr["constrained_columns"] == ["registration_id"]


def test_product_unique_constraints(db_session):
    """Verify serial_number, external_qr_token, and internal_qr_token uniqueness."""
    mfg = Manufacturer(manufacturer_name="Test Mfg", status="ACTIVE")
    db_session.add(mfg)
    db_session.flush()

    prod1 = Product(
        product_id="P1",
        product_name="Product 1",
        manufacturer_id=mfg.manufacturer_id,
        serial_number="SN-001",
        external_qr_token="EXT-TOKEN-1",
        internal_qr_token="INT-TOKEN-1",
    )
    db_session.add(prod1)
    db_session.commit()

    # 1. Duplicate serial number
    prod_dup_serial = Product(
        product_id="P2",
        product_name="Product 2",
        manufacturer_id=mfg.manufacturer_id,
        serial_number="SN-001",  # duplicate
        external_qr_token="EXT-TOKEN-2",
        internal_qr_token="INT-TOKEN-2",
    )
    db_session.add(prod_dup_serial)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 2. Duplicate external token
    prod_dup_ext = Product(
        product_id="P3",
        product_name="Product 3",
        manufacturer_id=mfg.manufacturer_id,
        serial_number="SN-003",
        external_qr_token="EXT-TOKEN-1",  # duplicate
        internal_qr_token="INT-TOKEN-3",
    )
    db_session.add(prod_dup_ext)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 3. Duplicate internal token
    prod_dup_int = Product(
        product_id="P4",
        product_name="Product 4",
        manufacturer_id=mfg.manufacturer_id,
        serial_number="SN-004",
        external_qr_token="EXT-TOKEN-4",
        internal_qr_token="INT-TOKEN-1",  # duplicate
    )
    db_session.add(prod_dup_int)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_product_token_difference_constraint(db_session):
    """Verify that external and internal QR tokens must differ."""
    mfg = Manufacturer(manufacturer_name="Test Mfg Difference", status="ACTIVE")
    db_session.add(mfg)
    db_session.flush()

    # Model validation should raise ValueError when internal matches external
    with pytest.raises(ValueError, match="must differ"):
        Product(
            product_id="P_SAME",
            product_name="Product Same",
            manufacturer_id=mfg.manufacturer_id,
            serial_number="SN-SAME",
            external_qr_token="IDENTICAL-TOKEN",
            internal_qr_token="IDENTICAL-TOKEN",
        )


def test_field_validation(db_session):
    """Verify ORM field validation rules."""
    # Manufacturer empty name
    with pytest.raises(ValueError, match="manufacturer_name cannot be empty"):
        Manufacturer(manufacturer_name="   ")

    # Manufacturer invalid email
    with pytest.raises(ValueError, match="Invalid email address"):
        Manufacturer(manufacturer_name="Valid Name", contact_email="not-an-email")

    # Manufacturer invalid status
    with pytest.raises(ValueError, match="status must be one of"):
        Manufacturer(manufacturer_name="Valid Name", status="UNKNOWN")

    # Retailer empty name
    with pytest.raises(ValueError, match="retailer_name cannot be empty"):
        Retailer(retailer_name="", city="SF", state="CA")

    # Product empty serial
    mfg = Manufacturer(manufacturer_name="Valid Mfg", status="ACTIVE")
    db_session.add(mfg)
    db_session.flush()

    with pytest.raises(ValueError, match="serial_number cannot be empty"):
        Product(
            product_id="P1",
            product_name="P1",
            manufacturer_id=mfg.manufacturer_id,
            serial_number="",
            external_qr_token="EXT-T",
            internal_qr_token="INT-T",
        )

    # Product invalid status
    with pytest.raises(ValueError, match="product_status must be one of"):
        Product(
            product_id="P1",
            product_name="P1",
            manufacturer_id=mfg.manufacturer_id,
            serial_number="SN-1",
            external_qr_token="EXT-T",
            internal_qr_token="INT-T",
            product_status="INVALID_STATUS",
        )


def test_warranty_registration_constraints(db_session):
    """Verify warranty dates and status validation."""
    mfg = Manufacturer(manufacturer_name="Mfg Warranties")
    ret = Retailer(retailer_name="Retailer Warranties", city="San Jose", state="CA")
    db_session.add_all([mfg, ret])
    db_session.flush()

    prod = Product(
        product_id="P_WARR",
        product_name="Product Warranties",
        manufacturer_id=mfg.manufacturer_id,
        serial_number="SN-WARR",
        external_qr_token="EXT-WARR",
        internal_qr_token="INT-WARR",
    )
    db_session.add(prod)
    db_session.flush()

    # Invalid email
    with pytest.raises(ValueError, match="Invalid email address"):
        WarrantyRegistration(
            product_id=prod.product_id,
            customer_name="Alice",
            email="invalid_email",
            retailer_id=ret.retailer_id,
            purchase_date=datetime.date.today(),
            warranty_start_date=datetime.date.today(),
            warranty_end_date=datetime.date.today() + datetime.timedelta(days=365),
        )

    # Negative price
    with pytest.raises(ValueError, match="purchase_price cannot be negative"):
        WarrantyRegistration(
            product_id=prod.product_id,
            customer_name="Alice",
            email="alice@example.com",
            retailer_id=ret.retailer_id,
            purchase_price=-10.0,
            purchase_date=datetime.date.today(),
            warranty_start_date=datetime.date.today(),
            warranty_end_date=datetime.date.today() + datetime.timedelta(days=365),
        )
