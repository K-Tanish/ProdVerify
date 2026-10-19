import os
from pathlib import Path

# Base directory of the project (ProdVerify root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Database configuration
DEFAULT_DB_PATH = BASE_DIR / "counterfeit.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

# QR and Application settings
BASE_VERIFY_URL = os.getenv("BASE_VERIFY_URL", "http://localhost:8000")
QR_STORAGE_DIR = BASE_DIR / "qr_codes"
SCAN_ALERT_THRESHOLD = int(os.getenv("SCAN_ALERT_THRESHOLD", "5"))
DEFAULT_WARRANTY_DAYS = int(os.getenv("DEFAULT_WARRANTY_DAYS", "365"))


