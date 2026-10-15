import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal, init_db
from backend.app.models.manufacturer import Manufacturer
from backend.app.models.retailer import Retailer
from backend.app.models.product import Product
from backend.app.services.token_service import generate_product_token_pair
from backend.app.services.qr_service import generate_product_qr_files

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prodverify.seed")


DEMO_MANUFACTURER = {
    "manufacturer_name": "Apex Manufacturing Corp",
    "contact_email": "support@apexcorp.com",
    "status": "ACTIVE",
}

DEMO_RETAILERS = [
    {
        "retailer_name": "ElectroTech Downtown",
        "address": "101 Market Street",
        "city": "San Francisco",
        "state": "CA",
        "status": "ACTIVE",
    },
    {
        "retailer_name": "Empire Gadgets",
        "address": "550 5th Avenue",
        "city": "New York",
        "state": "NY",
        "status": "ACTIVE",
    },
]

DEMO_PRODUCTS = [
    {
        "product_id": "PROD-001",
        "product_name": "Product A",
        "serial_number": "SN-PROD-A-001",
        "manufacturing_location": "Fremont, CA",
        "retailer_index": 0,  # ElectroTech Downtown (San Francisco, CA)
        "product_status": "IN_STOCK",
    },
    {
        "product_id": "PROD-002",
        "product_name": "Product B",
        "serial_number": "SN-PROD-B-002",
        "manufacturing_location": "Austin, TX",
        "retailer_index": 1,  # Empire Gadgets (New York, NY)
        "product_status": "IN_STOCK",
    },
    {
        "product_id": "PROD-003",
        "product_name": "Product C",
        "serial_number": "SN-PROD-C-003",
        "manufacturing_location": "Fremont, CA",
        "retailer_index": 0,  # ElectroTech Downtown (San Francisco, CA)
        "product_status": "IN_STOCK",
    },
]


def seed_database(session: Session, generate_qrs: bool = True) -> Dict[str, Any]:
    """
    Seed demo manufacturer, two demo retailers, and exactly three products.
    Ensures idempotency: running this function again will NOT create duplicates
    and will NOT modify or overwrite existing tokens.
    """
    # 1. Manufacturer
    mfg = (
        session.query(Manufacturer)
        .filter_by(manufacturer_name=DEMO_MANUFACTURER["manufacturer_name"])
        .first()
    )
    if not mfg:
        mfg = Manufacturer(**DEMO_MANUFACTURER)
        session.add(mfg)
        session.flush()
        logger.info(f"Created demo manufacturer: {mfg.manufacturer_name} (ID: {mfg.manufacturer_id})")
    else:
        logger.info(f"Demo manufacturer already exists: {mfg.manufacturer_name} (ID: {mfg.manufacturer_id})")

    # 2. Retailers
    retailers = []
    for ret_data in DEMO_RETAILERS:
        ret = session.query(Retailer).filter_by(retailer_name=ret_data["retailer_name"]).first()
        if not ret:
            ret = Retailer(**ret_data)
            session.add(ret)
            session.flush()
            logger.info(f"Created demo retailer: {ret.retailer_name} ({ret.city}, {ret.state}) (ID: {ret.retailer_id})")
        else:
            logger.info(f"Demo retailer already exists: {ret.retailer_name} (ID: {ret.retailer_id})")
        retailers.append(ret)

    # 3. Products
    seeded_products = []
    for prod_spec in DEMO_PRODUCTS:
        product_id = prod_spec["product_id"]
        existing = session.query(Product).filter_by(product_id=product_id).first()
        if existing:
            logger.info(
                f"Product '{product_id}' ({existing.product_name}) already exists with serial {existing.serial_number}. Skipping."
            )
            seeded_products.append(existing)
            continue

        # Check by serial number to guarantee uniqueness
        existing_sn = session.query(Product).filter_by(serial_number=prod_spec["serial_number"]).first()
        if existing_sn:
            logger.info(
                f"Product with serial '{prod_spec['serial_number']}' already exists. Skipping."
            )
            seeded_products.append(existing_sn)
            continue

        # Generate two cryptographically secure, unique tokens
        ext_token, int_token = generate_product_token_pair(session)

        intended_retailer = retailers[prod_spec["retailer_index"]]
        new_product = Product(
            product_id=product_id,
            product_name=prod_spec["product_name"],
            serial_number=prod_spec["serial_number"],
            manufacturer_id=mfg.manufacturer_id,
            external_qr_token=ext_token,
            internal_qr_token=int_token,
            manufacturing_location=prod_spec["manufacturing_location"],
            intended_retailer_id=intended_retailer.retailer_id,
            product_status=prod_spec["product_status"],
        )
        session.add(new_product)
        session.flush()

        if generate_qrs:
            try:
                generate_product_qr_files(
                    product_id=new_product.product_id,
                    external_token=new_product.external_qr_token,
                    internal_token=new_product.internal_qr_token,
                )
            except Exception as e:
                logger.warning(f"Failed to generate QR files for {product_id}: {e}")

        logger.info(
            f"Created {new_product.product_name} (ID: {new_product.product_id}, SN: {new_product.serial_number}) "
            f"with external token: {new_product.external_qr_token[:8]}... "
            f"and internal token: {new_product.internal_qr_token[:8]}..."
        )
        seeded_products.append(new_product)

    session.commit()

    return {
        "manufacturer": mfg,
        "retailers": retailers,
        "products": seeded_products,
    }


def main():
    """CLI entrypoint to initialize database and seed demo data."""
    init_db()
    session = SessionLocal()
    try:
        results = seed_database(session, generate_qrs=True)
        print("\n=== ProdVerify Database Seeding Complete ===")
        print(f"Manufacturer: {results['manufacturer'].manufacturer_name}")
        print("Retailers:")
        for r in results["retailers"]:
            print(f"  - [{r.retailer_id}] {r.retailer_name} ({r.city}, {r.state})")
        print("Products & QR Tokens:")
        for p in results["products"]:
            print(f"  - [{p.product_id}] {p.product_name} (SN: {p.serial_number})")
            print(f"      External QR Token: {p.external_qr_token}")
            print(f"      Internal QR Token: {p.internal_qr_token}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
