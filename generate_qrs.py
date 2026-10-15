"""
Script to generate all 6 QR code images from the tokens already stored in counterfeit.db.
Supports configurable base URL for reachable phone scanning or custom domain testing.
"""
import argparse
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.config import BASE_VERIFY_URL, QR_STORAGE_DIR
from backend.app.database import SessionLocal
from backend.app.services.qr_service import generate_all_stored_qr_codes


def main():
    parser = argparse.ArgumentParser(description="Generate QR codes from tokens stored in counterfeit.db")
    parser.add_argument(
        "--base-url",
        default=BASE_VERIFY_URL,
        help=f"Reachable base URL for verification links (default: {BASE_VERIFY_URL})",
    )
    parser.add_argument(
        "--output-dir",
        default=str(QR_STORAGE_DIR),
        help=f"Directory to save generated QR images (default: {QR_STORAGE_DIR})",
    )
    args = parser.parse_args()

    session = SessionLocal()
    try:
        results = generate_all_stored_qr_codes(
            session=session,
            output_dir=Path(args.output_dir),
            base_url=args.base_url,
        )
        print("=" * 65)
        print("PRODVERIFY QR CODE GENERATOR")
        print("=" * 65)
        print(f"Base URL   : {args.base_url}")
        print(f"Output Dir : {args.output_dir}")
        print(f"Generated  : {len(results) * 2} QR codes for {len(results)} products\n")

        for prod_id, ext_path, int_path in results:
            print(f"[{prod_id}]")
            print(f"  External QR (Verify)  : {ext_path.name}")
            print(f"  Internal QR (Register): {int_path.name}")
        print("=" * 65)
        print("All QR images successfully generated and persisted.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
