"""
Manual verification script for Checkpoint 3:
1. Verifies Product A status before registration (IN_STOCK).
2. Submits valid warranty registration for Product A.
3. Verifies Product A status after registration (SOLD) and warranty status (ACTIVE).
4. Verifies duplicate registration attempt is rejected with 409 Conflict.
"""
import datetime
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.database import SessionLocal
from backend.app.models.product import Product
from backend.app.services.registration_service import register_warranty, RegistrationError


def run_manual_test():
    session = SessionLocal()
    try:
        prod_a = session.query(Product).filter_by(product_id="PROD-001").first()
        if not prod_a:
            print("Product PROD-001 not found in database.")
            return

        print("=" * 65)
        print("PRODVERIFY CHECKPOINT 3: MANUAL TEST VERIFICATION")
        print("=" * 65)
        print(f"[1] Initial State:")
        print(f"    Product ID    : {prod_a.product_id} ({prod_a.product_name})")
        print(f"    Serial Number : {prod_a.serial_number}")
        print(f"    Status        : {prod_a.product_status}")

        today_str = datetime.date.today().isoformat()

        # Step 2: Register if not already registered
        if prod_a.warranty_registration is None:
            print(f"\n[2] Executing Warranty Registration for Product A...")
            res = register_warranty(
                session=session,
                token=prod_a.internal_qr_token,
                customer_name="Jane Doe",
                email="jane.doe@example.com",
                retailer_id=prod_a.intended_retailer_id,
                purchase_price=299.99,
                purchase_date=today_str,
            )
            print("    Registration Result : SUCCESS")
            print(f"    Registration ID     : {res['registration']['registration_id']}")
            print(f"    Customer Name       : {res['registration']['customer_name']}")
            print(f"    Customer Email      : {res['registration']['email']}")
            print(f"    Warranty Status     : {res['registration']['warranty_status']}")
            print(f"    Warranty Period     : {res['registration']['warranty_start_date']} to {res['registration']['warranty_end_date']}")
        else:
            print(f"\n[2] Product A already registered with Warranty ID {prod_a.warranty_registration.registration_id}.")

        session.expire_all()
        prod_a_updated = session.query(Product).filter_by(product_id="PROD-001").first()
        print(f"\n[3] Post-Registration State:")
        print(f"    Product Status      : {prod_a_updated.product_status}")
        print(f"    Warranty Status     : {prod_a_updated.warranty_registration.warranty_status}")

        # Step 4: Duplicate Registration Attempt
        print(f"\n[4] Attempting Duplicate Registration for Product A...")
        try:
            register_warranty(
                session=session,
                token=prod_a_updated.internal_qr_token,
                customer_name="Duplicate Applicant",
                email="duplicate@example.com",
                retailer_id=prod_a_updated.intended_retailer_id,
                purchase_price=299.99,
                purchase_date=today_str,
            )
            print("    ERROR: Duplicate registration succeeded when it should have failed!")
        except RegistrationError as err:
            print(f"    SUCCESS: Duplicate registration rejected!")
            print(f"    Status Code         : {err.status_code}")
            print(f"    Error Message       : {err.message}")

        print("=" * 65)
    finally:
        session.close()


if __name__ == "__main__":
    run_manual_test()
