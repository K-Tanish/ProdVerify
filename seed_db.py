"""
Database seed script for ProdVerify.
Initializes the schema if needed and seeds the demo manufacturer, retailers, and products.
Repeatable and idempotent: will not create duplicate products or replace existing tokens.
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.seed import main

if __name__ == "__main__":
    main()
