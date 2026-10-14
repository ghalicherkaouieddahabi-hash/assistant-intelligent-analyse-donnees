"""Import PostgreSQL depuis notebooks/ (wrapper)."""
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src.etl.import_data import import_to_postgres

if __name__ == "__main__":
    tables = import_to_postgres(ROOT / "data" / "processed")
    print("Tables importées :", ", ".join(tables))
