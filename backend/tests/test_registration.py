import datetime
import pytest

from backend.app.models.product import Product
from backend.app.models.retailer import Retailer
from backend.app.models.scan_history import ScanHistory
from backend.app.models.warranty_registration import WarrantyRegistration
from backend.app.seed import seed_database
from backend.app.services.registration_service import (
    RegistrationError,
    register_warranty,
    resolve_internal_token,
)


def test_successful_registration(db_session):
    """
    Verify successful warranty registration:
    - Inserts Warranty_Registrations record.
    - Sets product status to SOLD.
    - Activates warranty with valid start and end dates (365 days).
    - Inserts INTERNAL_REGISTRATION event into Scan_History.
    """
    seed_database(db_session, generate_qrs=False)
    prod = db_session.query(Product).filter_by(product_id="PROD-001").first()
    ret = db_session.query(Retailer).first()

    assert prod.product_status == "IN_STOCK"
    assert prod.warranty_registration is None

    today_str = datetime.date.today().isoformat()
    result = register_warranty(
        session=db_session,
        token=prod.internal_qr_token,
        customer_name="Alice Johnson",
        email="alice@example.com",
        retailer_id=ret.retailer_id,
        purchase_price=499.99,
        purchase_date=today_str,
    )

    assert result["success"] is True
    assert result["registration"]["warranty_status"] == "ACTIVE"
    assert result["registration"]["customer_name"] == "Alice Johnson"
    assert result["registration"]["email"] == "alice@example.com"
    assert result["registration"]["purchase_date"] == today_str
    assert result["registration"]["warranty_start_date"] == today_str

    expected_end = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    assert result["registration"]["warranty_end_date"] == expected_end
    assert result["product"]["product_status"] == "SOLD"

    # Verify DB persistence
    db_session.expire_all()
    updated_prod = db_session.query(Product).filter_by(product_id="PROD-001").first()
    assert updated_prod.product_status == "SOLD"
    assert updated_prod.warranty_registration is not None
    assert updated_prod.warranty_registration.warranty_status == "ACTIVE"

    # Verify ScanHistory
    scan = (
        db_session.query(ScanHistory)
        .filter_by(product_id="PROD-001", scan_type="INTERNAL_REGISTRATION")
        .first()
    )
    assert scan is not None
    assert scan.result == "VERIFIED"


def test_invalid_internal_token(db_session):
    """Verify that unknown tokens and external tokens are rejected."""
    seed_database(db_session, generate_qrs=False)
    prod = db_session.query(Product).filter_by(product_id="PROD-001").first()
    ret = db_session.query(Retailer).first()
    today_str = datetime.date.today().isoformat()

    # 1. Unknown token
    with pytest.raises(RegistrationError) as exc_info:
        register_warranty(
            session=db_session,
            token="completely-fake-internal-token",
            customer_name="Bob",
            email="bob@example.com",
            retailer_id=ret.retailer_id,
            purchase_price=100.0,
            purchase_date=today_str,
        )
    assert exc_info.value.status_code == 404
    assert "not match" in exc_info.value.message.lower()

    # 2. External token on registration endpoint
    with pytest.raises(RegistrationError) as exc_ext:
        register_warranty(
            session=db_session,
            token=prod.external_qr_token,
            customer_name="Bob",
            email="bob@example.com",
            retailer_id=ret.retailer_id,
            purchase_price=100.0,
            purchase_date=today_str,
        )
    assert exc_ext.value.status_code == 400
    assert "external verification code" in exc_ext.value.message.lower()


def test_invalid_registration_data(db_session):
    """Verify validation for missing or invalid form fields."""
    seed_database(db_session, generate_qrs=False)
    prod = db_session.query(Product).filter_by(product_id="PROD-001").first()
    ret = db_session.query(Retailer).first()
    today_str = datetime.date.today().isoformat()

    # Empty name
    with pytest.raises(RegistrationError) as exc:
        register_warranty(db_session, prod.internal_qr_token, "   ", "bob@example.com", ret.retailer_id, 100, today_str)
    assert exc.value.status_code == 422

    # Invalid email
    with pytest.raises(RegistrationError) as exc:
        register_warranty(db_session, prod.internal_qr_token, "Bob", "invalid-email", ret.retailer_id, 100, today_str)
    assert exc.value.status_code == 422

    # Negative price
    with pytest.raises(RegistrationError) as exc:
        register_warranty(db_session, prod.internal_qr_token, "Bob", "bob@example.com", ret.retailer_id, -50.0, today_str)
    assert exc.value.status_code == 422

    # Invalid date format
    with pytest.raises(RegistrationError) as exc:
        register_warranty(db_session, prod.internal_qr_token, "Bob", "bob@example.com", ret.retailer_id, 50.0, "not-a-date")
    assert exc.value.status_code == 422

    # Future date (more than 1 day in the future)
    future_date = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()
    with pytest.raises(RegistrationError) as exc:
        register_warranty(db_session, prod.internal_qr_token, "Bob", "bob@example.com", ret.retailer_id, 50.0, future_date)
    assert exc.value.status_code == 422


def test_duplicate_registration_rejected(db_session):
    """Verify that registering the same product twice is rejected with 409 conflict."""
    seed_database(db_session, generate_qrs=False)
    prod = db_session.query(Product).filter_by(product_id="PROD-002").first()
    ret = db_session.query(Retailer).first()
    today_str = datetime.date.today().isoformat()

    # First registration
    register_warranty(
        session=db_session,
        token=prod.internal_qr_token,
        customer_name="First Owner",
        email="owner1@example.com",
        retailer_id=ret.retailer_id,
        purchase_price=200.0,
        purchase_date=today_str,
    )

    # Second registration attempt
    with pytest.raises(RegistrationError) as exc:
        register_warranty(
            session=db_session,
            token=prod.internal_qr_token,
            customer_name="Second Owner",
            email="owner2@example.com",
            retailer_id=ret.retailer_id,
            purchase_price=200.0,
            purchase_date=today_str,
        )
    assert exc.value.status_code == 409
    assert "already registered" in exc.value.message.lower()

    # Verify only one registration in DB
    reg_count = db_session.query(WarrantyRegistration).filter_by(product_id=prod.product_id).count()
    assert reg_count == 1


def test_blocked_product_cannot_be_registered(db_session):
    """Verify that blocked products cannot be registered."""
    seed_database(db_session, generate_qrs=False)
    prod = db_session.query(Product).filter_by(product_id="PROD-003").first()
    prod.product_status = "BLOCKED"
    db_session.commit()

    ret = db_session.query(Retailer).first()
    today_str = datetime.date.today().isoformat()

    with pytest.raises(RegistrationError) as exc:
        register_warranty(
            session=db_session,
            token=prod.internal_qr_token,
            customer_name="Charlie",
            email="charlie@example.com",
            retailer_id=ret.retailer_id,
            purchase_price=150.0,
            purchase_date=today_str,
        )
    assert exc.value.status_code == 403
    assert "BLOCKED" in exc.value.message


def test_unknown_retailer_rejected(db_session):
    """Verify that nonexistent retailer ID is rejected."""
    seed_database(db_session, generate_qrs=False)
    prod = db_session.query(Product).filter_by(product_id="PROD-001").first()
    today_str = datetime.date.today().isoformat()

    with pytest.raises(RegistrationError) as exc:
        register_warranty(
            session=db_session,
            token=prod.internal_qr_token,
            customer_name="David",
            email="david@example.com",
            retailer_id=99999,  # Unknown retailer
            purchase_price=100.0,
            purchase_date=today_str,
        )
    assert exc.value.status_code == 404
    assert "does not exist" in exc.value.message.lower()


def test_transaction_rollback_on_failure(db_session):
    """Verify that failures leave no partial database changes."""
    seed_database(db_session, generate_qrs=False)
    prod = db_session.query(Product).filter_by(product_id="PROD-001").first()

    # Trigger failure with invalid email
    with pytest.raises(RegistrationError):
        register_warranty(
            session=db_session,
            token=prod.internal_qr_token,
            customer_name="Eva",
            email="not-an-email",
            retailer_id=1,
            purchase_price=100.0,
            purchase_date=datetime.date.today().isoformat(),
        )

    # Verify product is still IN_STOCK and no registrations or scans created
    db_session.expire_all()
    p = db_session.query(Product).filter_by(product_id="PROD-001").first()
    assert p.product_status == "IN_STOCK"
    assert p.warranty_registration is None
    assert db_session.query(ScanHistory).filter_by(product_id="PROD-001").count() == 0


def test_registration_endpoints_via_client(client, db_session):
    """
    Verify FastAPI routes:
    - GET /register/{token} (HTML page)
    - GET /api/register/{token} (Eligibility check)
    - POST /api/register/{token} (Registration API)
    """
    seed_database(db_session, generate_qrs=False)
    prod_a = db_session.query(Product).filter_by(product_id="PROD-001").first()
    ret = db_session.query(Retailer).first()

    # 1. HTML page render
    res_page = client.get(f"/register/{prod_a.internal_qr_token}")
    assert res_page.status_code == 200
    assert "text/html" in res_page.headers["content-type"]
    assert "Warranty Registration" in res_page.text

    # 2. Eligibility info API
    res_info = client.get(f"/api/register/{prod_a.internal_qr_token}")
    assert res_info.status_code == 200
    info = res_info.json()
    assert info["product_id"] == "PROD-001"
    assert info["eligible"] is True

    # 3. Post registration
    today_str = datetime.date.today().isoformat()
    payload = {
        "customer_name": "Frank Castle",
        "email": "frank@example.com",
        "retailer_id": ret.retailer_id,
        "purchase_price": 599.00,
        "purchase_date": today_str,
    }
    res_post = client.post(f"/api/register/{prod_a.internal_qr_token}", json=payload)
    assert res_post.status_code == 200
    reg_data = res_post.json()
    assert reg_data["success"] is True
    assert reg_data["registration"]["customer_name"] == "Frank Castle"
    assert reg_data["product"]["product_status"] == "SOLD"

    # 4. Duplicate submission via API returns 409
    res_dup = client.post(f"/api/register/{prod_a.internal_qr_token}", json=payload)
    assert res_dup.status_code == 409
    assert "already registered" in res_dup.json()["detail"].lower()
