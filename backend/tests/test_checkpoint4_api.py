from backend.app.models.product import Product
from backend.app.models.retailer import Retailer
from backend.app.seed import seed_database


def test_dashboard_stats_api(client, db_session):
    """Verify /api/dashboard/stats returns real counts from database."""
    seed_database(db_session, generate_qrs=False)

    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_products"] == 3
    assert data["in_stock_products"] == 3
    assert data["sold_products"] == 0
    assert data["blocked_products"] == 0
    assert data["active_warranties"] == 0
    assert "total_external_scans" in data
    assert "suspicious_scans" in data
    assert "total_suspicious_events" in data


def test_create_product_api(client, db_session):
    """Verify creating a new product via POST /api/products."""
    seed_database(db_session, generate_qrs=False)
    ret = db_session.query(Retailer).first()

    payload = {
        "product_name": "Product D Special",
        "intended_retailer_id": ret.retailer_id,
        "manufacturing_location": "Seattle, WA",
    }
    res = client.post("/api/products", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["product_name"] == "Product D Special"
    assert data["product_status"] == "IN_STOCK"
    assert "external_qr_token" in data
    assert "internal_qr_token" in data
    assert data["external_qr_token"] != data["internal_qr_token"]

    # Verify in DB
    created = db_session.query(Product).filter_by(product_name="Product D Special").first()
    assert created is not None
    assert created.intended_retailer_id == ret.retailer_id


def test_scans_and_warranties_lists_api(client, db_session):
    """Verify /api/scans and /api/warranties list endpoints."""
    seed_database(db_session, generate_qrs=False)
    prod = db_session.query(Product).first()

    # Trigger a scan
    client.get(f"/api/verify/{prod.external_qr_token}")

    # Check scans endpoint
    res_scans = client.get("/api/scans")
    assert res_scans.status_code == 200
    scans = res_scans.json()
    assert len(scans) >= 1
    assert scans[0]["product_id"] == prod.product_id
    assert scans[0]["result"] == "VERIFIED"

    # Check warranties endpoint
    res_warr = client.get("/api/warranties")
    assert res_warr.status_code == 200
    assert isinstance(res_warr.json(), list)
