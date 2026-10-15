"""
Database initialization script for ProdVerify.
Creates counterfeit.db and all required schema tables.
"""
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.database import init_db, engine
from backend.app.config import DATABASE_URL

if __name__ == "__main__":
    print(f"Initializing database at: {DATABASE_URL}")
    init_db()
    print("Database schema successfully created with all tables and constraints.")
