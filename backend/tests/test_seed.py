from backend.app.models.manufacturer import Manufacturer
from backend.app.models.retailer import Retailer
from backend.app.models.product import Product
from backend.app.seed import seed_database


def test_seed_creates_expected_data(db_session):
    """
    Verify seed creates:
    - 1 demo manufacturer
    - 2 demo retailers in different locations
    - Exactly 3 products (Product A, B, C)
    - Exactly 6 unique QR tokens persisted in SQLite
    """
    results = seed_database(db_session, generate_qrs=False)

    # 1. Manufacturer
    manufacturers = db_session.query(Manufacturer).all()
    assert len(manufacturers) == 1
    assert manufacturers[0].manufacturer_name == "Apex Manufacturing Corp"

    # 2. Retailers
    retailers = db_session.query(Retailer).all()
    assert len(retailers) == 2
    cities = {r.city for r in retailers}
    assert cities == {"San Francisco", "New York"}

    # 3. Products
    products = db_session.query(Product).order_by(Product.product_id).all()
    assert len(products) == 3
    product_names = [p.product_name for p in products]
    assert product_names == ["Product A", "Product B", "Product C"]

    # 4. Six unique tokens
    tokens = []
    for p in products:
        assert p.external_qr_token != p.internal_qr_token
        tokens.extend([p.external_qr_token, p.internal_qr_token])

    assert len(tokens) == 6
    assert len(set(tokens)) == 6, "All 6 tokens must be globally unique"


def test_seed_is_repeatable_and_idempotent(db_session):
    """
    Verify that running the seed function a second time:
    - Does not create duplicate manufacturers, retailers, or products
    - Does not replace or overwrite existing tokens
    """
    # First seed run
    seed_database(db_session, generate_qrs=False)

    # Snapshot existing product tokens and IDs
    initial_products = db_session.query(Product).order_by(Product.product_id).all()
    assert len(initial_products) == 3

    token_map_1 = {
        p.product_id: (p.external_qr_token, p.internal_qr_token)
        for p in initial_products
    }

    # Second seed run
    seed_database(db_session, generate_qrs=False)

    # Verify counts remain identical
    assert db_session.query(Manufacturer).count() == 1
    assert db_session.query(Retailer).count() == 2
    assert db_session.query(Product).count() == 3

    # Verify tokens did not change
    after_products = db_session.query(Product).order_by(Product.product_id).all()
    token_map_2 = {
        p.product_id: (p.external_qr_token, p.internal_qr_token)
        for p in after_products
    }

    assert token_map_1 == token_map_2, "Seed rerun must preserve existing tokens without replacing them"
