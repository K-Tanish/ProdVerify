from backend.app.config import SCAN_ALERT_THRESHOLD
from backend.app.models.product import Product
from backend.app.models.scan_history import ScanHistory
from backend.app.seed import seed_database
from backend.app.services.verification_service import verify_external_token


def test_verify_all_three_products(db_session):
    """
    Verify external tokens for all three products (A, B, C):
    - Product A maps to PROD-001, intended retailer ElectroTech Downtown (San Francisco)
    - Product B maps to PROD-002, intended retailer Empire Gadgets (New York)
    - Product C maps to PROD-003, intended retailer ElectroTech Downtown (San Francisco)
    Each must return VERIFIED on initial scan with scan_count = 1.
    """
    seed_database(db_session, generate_qrs=False)

    products = db_session.query(Product).order_by(Product.product_id).all()
    assert len(products) == 3

    # Product A
    res_a = verify_external_token(db_session, products[0].external_qr_token)
    assert res_a["result"] == "VERIFIED"
    assert res_a["product"]["product_id"] == "PROD-001"
    assert res_a["product"]["product_name"] == "Product A"
    assert res_a["intended_retailer"]["retailer_name"] == "ElectroTech Downtown"
    assert res_a["intended_retailer"]["city"] == "San Francisco"
    assert res_a["scan_count"] == 1
    assert "no security discrepancies" in res_a["explanation"].lower()

    # Product B
    res_b = verify_external_token(db_session, products[1].external_qr_token)
    assert res_b["result"] == "VERIFIED"
    assert res_b["product"]["product_id"] == "PROD-002"
    assert res_b["product"]["product_name"] == "Product B"
    assert res_b["intended_retailer"]["retailer_name"] == "Empire Gadgets"
    assert res_b["intended_retailer"]["city"] == "New York"
    assert res_b["scan_count"] == 1

    # Product C
    res_c = verify_external_token(db_session, products[2].external_qr_token)
    assert res_c["result"] == "VERIFIED"
    assert res_c["product"]["product_id"] == "PROD-003"
    assert res_c["product"]["product_name"] == "Product C"
    assert res_c["intended_retailer"]["retailer_name"] == "ElectroTech Downtown"
    assert res_c["intended_retailer"]["city"] == "San Francisco"
    assert res_c["scan_count"] == 1


def test_unknown_token_returns_invalid_and_logs_scan(db_session):
    """
    Verify unknown tokens:
    - Return INVALID
    - Return clear explanation
    - Record attempt in Scan_History with product_id=None
    """
    seed_database(db_session, generate_qrs=False)

    res = verify_external_token(db_session, "nonexistent-token-xyz-999")
    assert res["result"] == "INVALID"
    assert "does not match" in res["explanation"].lower()
    assert res["product"] is None
    assert res["intended_retailer"] is None

    # Check scan history logged
    logged_scan = (
        db_session.query(ScanHistory)
        .filter_by(result="INVALID", scan_type="EXTERNAL_VERIFICATION")
        .first()
    )
    assert logged_scan is not None
    assert logged_scan.product_id is None
    assert logged_scan.risk_reason == "Unrecognized QR token"


def test_internal_token_on_external_verify_returns_suspicious(db_session):
    """
    Verify that scanning an internal warranty token on the external verification endpoint:
    - Returns SUSPICIOUS
    - Flags that the code is intended for warranty registration, not verification
    - Logs the scan event in Scan_History
    """
    seed_database(db_session, generate_qrs=False)
    prod_a = db_session.query(Product).filter_by(product_id="PROD-001").first()

    # Pass INTERNAL token instead of EXTERNAL token
    res = verify_external_token(db_session, prod_a.internal_qr_token)
    assert res["result"] == "SUSPICIOUS"
    assert "internal warranty" in res["explanation"].lower()
    assert len(res["risk_warnings"]) >= 1
    assert "internal" in res["risk_warnings"][0].lower()

    # Verify scan history was logged for prod_a
    logged_scan = (
        db_session.query(ScanHistory)
        .filter_by(product_id=prod_a.product_id, result="SUSPICIOUS")
        .first()
    )
    assert logged_scan is not None


def test_repeated_scans_and_scan_count_accuracy(db_session):
    """
    Verify scan count accuracy and configurable threshold flagging:
    - Current scan is counted exactly once per attempt
    - Subsequent scans increment by exactly 1
    - Scans exceeding SCAN_ALERT_THRESHOLD return SUSPICIOUS with explanation
    - Repeated scans explain copying risk without asserting counterfeiting
    """
    seed_database(db_session, generate_qrs=False)
    prod_a = db_session.query(Product).filter_by(product_id="PROD-001").first()

    # Scan repeatedly up to threshold
    for i in range(1, SCAN_ALERT_THRESHOLD + 1):
        res = verify_external_token(db_session, prod_a.external_qr_token)
        assert res["scan_count"] == i
        assert res["result"] == "VERIFIED"

    # Scan once more to exceed threshold
    res_exceeded = verify_external_token(db_session, prod_a.external_qr_token)
    assert res_exceeded["scan_count"] == SCAN_ALERT_THRESHOLD + 1
    assert res_exceeded["result"] == "SUSPICIOUS"

    # Warning must explain elevated count without concluding counterfeiting directly
    warning_text = "; ".join(res_exceeded["risk_warnings"])
    assert "elevated scan count" in warning_text.lower()
    assert "browsing" in warning_text.lower()  # acknowledges routine customer browsing
    assert "duplicated" in warning_text.lower() or "copied" in warning_text.lower()

    # Verify database scan count matches
    actual_db_scans = (
        db_session.query(ScanHistory)
        .filter_by(product_id=prod_a.product_id, scan_type="EXTERNAL_VERIFICATION")
        .count()
    )
    assert actual_db_scans == SCAN_ALERT_THRESHOLD + 1


def test_retailer_mismatch_evidence(db_session):
    """
    Verify retailer mismatch detection:
    - Customer reports matching retailer -> VERIFIED
    - Customer reports different retailer -> SUSPICIOUS with clear mismatch explanation
    """
    seed_database(db_session, generate_qrs=False)
    prod_b = db_session.query(Product).filter_by(product_id="PROD-002").first()
    # prod_b intended retailer is Empire Gadgets (ID: 2)

    # 1. Matching retailer reported
    res_match = verify_external_token(
        db_session,
        prod_b.external_qr_token,
        reported_retailer_id=prod_b.intended_retailer_id,
    )
    assert res_match["result"] == "VERIFIED"
    assert len(res_match["risk_warnings"]) == 0

    # 2. Mismatched retailer reported (ID: 1 instead of 2)
    wrong_retailer_id = 1 if prod_b.intended_retailer_id != 1 else 2
    res_mismatch = verify_external_token(
        db_session,
        prod_b.external_qr_token,
        reported_retailer_id=wrong_retailer_id,
    )
    assert res_mismatch["result"] == "SUSPICIOUS"
    assert any("retailer mismatch" in w.lower() for w in res_mismatch["risk_warnings"])
    assert "diversion" in "; ".join(res_mismatch["risk_warnings"]).lower()


def test_product_blocked_or_sold_status_triggers_suspicious(db_session):
    """Verify that BLOCKED and SOLD products produce SUSPICIOUS results."""
    seed_database(db_session, generate_qrs=False)
    prod_c = db_session.query(Product).filter_by(product_id="PROD-003").first()

    # Change to BLOCKED
    prod_c.product_status = "BLOCKED"
    db_session.commit()

    res_blocked = verify_external_token(db_session, prod_c.external_qr_token)
    assert res_blocked["result"] == "SUSPICIOUS"
    assert any("BLOCKED" in w for w in res_blocked["risk_warnings"])

    # Change to SOLD
    prod_c.product_status = "SOLD"
    db_session.commit()

    res_sold = verify_external_token(db_session, prod_c.external_qr_token)
    assert res_sold["result"] == "SUSPICIOUS"
    assert any("SOLD" in w for w in res_sold["risk_warnings"])


def test_api_verification_endpoints(client, db_session):
    """
    Verify FastAPI routes:
    - GET /api/health
    - GET /api/verify/{token}
    - GET /api/products/{id}/qrs
    - GET /api/products/{id}/qrs/external
    - GET /verify/{token} (HTML page)
    - GET / (Home portal page)
    """
    seed_database(db_session, generate_qrs=False)
    prod_a = db_session.query(Product).filter_by(product_id="PROD-001").first()

    # 1. Health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # 2. API Verify endpoint
    res_verify = client.get(f"/api/verify/{prod_a.external_qr_token}")
    assert res_verify.status_code == 200
    data = res_verify.json()
    assert data["result"] == "VERIFIED"
    assert data["product"]["product_id"] == "PROD-001"
    assert data["scan_count"] == 1

    # 3. QR metadata endpoint
    res_qrs = client.get("/api/products/PROD-001/qrs")
    assert res_qrs.status_code == 200
    qr_data = res_qrs.json()
    assert qr_data["product_id"] == "PROD-001"
    assert "/verify/" in qr_data["external_qr"]["target_url"]
    assert "/register/" in qr_data["internal_qr"]["target_url"]

    # 4. QR image serving endpoint
    res_img = client.get("/api/products/PROD-001/qrs/external")
    assert res_img.status_code == 200
    assert res_img.headers["content-type"] == "image/png"
    assert len(res_img.content) > 500

    # 5. Customer-facing HTML verification page
    res_page = client.get(f"/verify/{prod_a.external_qr_token}")
    assert res_page.status_code == 200
    assert "text/html" in res_page.headers["content-type"]
    assert "ProdVerify" in res_page.text
    assert "Authenticity Verification" in res_page.text

    # 6. Portal page
    res_portal = client.get("/")
    assert res_portal.status_code == 200
    assert "Product A" in res_portal.text
    assert "PROD-001" in res_portal.text
