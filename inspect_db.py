"""
Inspection script to verify the contents of counterfeit.db:
- Lists all tables
- Displays Manufacturers and Retailers
- Displays Products, Serial Numbers, and the 6 Unique QR Tokens
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sqlalchemy import inspect
from backend.app.database import SessionLocal, engine
from backend.app.models.manufacturer import Manufacturer
from backend.app.models.retailer import Retailer
from backend.app.models.product import Product
from backend.app.models.scan_history import ScanHistory
from backend.app.models.warranty_registration import WarrantyRegistration


def inspect_database():
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("=" * 70)
    print("PRODVERIFY DATABASE INSPECTOR (counterfeit.db)")
    print("=" * 70)
    print(f"Tables found ({len(tables)}): {', '.join(tables)}\n")

    session = SessionLocal()
    try:
        # Manufacturers
        manufacturers = session.query(Manufacturer).all()
        print(f"--- Manufacturers ({len(manufacturers)}) ---")
        for m in manufacturers:
            print(f"ID: {m.manufacturer_id} | Name: {m.manufacturer_name} | Email: {m.contact_email} | Status: {m.status}")
        print()

        # Retailers
        retailers = session.query(Retailer).all()
        print(f"--- Retailers ({len(retailers)}) ---")
        for r in retailers:
            print(f"ID: {r.retailer_id} | Name: {r.retailer_name} | City: {r.city}, {r.state} | Status: {r.status}")
        print()

        # Products
        products = session.query(Product).all()
        print(f"--- Products ({len(products)}) ---")
        tokens = []
        for p in products:
            ret_name = p.intended_retailer.retailer_name if p.intended_retailer else "None"
            print(f"Product ID     : {p.product_id}")
            print(f"Product Name   : {p.product_name}")
            print(f"Serial Number  : {p.serial_number}")
            print(f"Status         : {p.product_status}")
            print(f"Intended Store : {ret_name}")
            print(f"External Token : {p.external_qr_token}")
            print(f"Internal Token : {p.internal_qr_token}")
            print("-" * 50)
            tokens.extend([p.external_qr_token, p.internal_qr_token])

        unique_tokens = set(tokens)
        print(f"Total Products: {len(products)}")
        print(f"Total QR Tokens: {len(tokens)}")
        print(f"Unique QR Tokens: {len(unique_tokens)}")
        if len(tokens) == 6 and len(unique_tokens) == 6:
            print(">> SUCCESS: Exactly 6 unique tokens present for 3 products!")
        print("=" * 70)
    finally:
        session.close()


if __name__ == "__main__":
    inspect_database()
