"""Pipeline ETL complet : nettoyage puis import PostgreSQL."""
import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.etl.clean_data import run_clean
from src.etl.import_data import import_to_postgres

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


def run_pipeline(import_db: bool = True) -> None:
    load_dotenv(ROOT / ".env")
    logger.info("Étape 1/2 — Nettoyage data/raw -> data/processed")
    stats = run_clean(RAW_DIR, PROCESSED_DIR)
    if not stats:
        raise FileNotFoundError(f"Aucun CSV trouvé dans {RAW_DIR}")
    for name, rows in stats.items():
        logger.info("  %s : %s lignes", name, rows)
    if not import_db:
        logger.info("Pipeline terminé (import DB ignoré).")
        return
    logger.info("Étape 2/2 — Import data/processed -> PostgreSQL")
    tables = import_to_postgres(PROCESSED_DIR)
    logger.info("Tables importées : %s", ", ".join(tables))
    logger.info("Pipeline terminé.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline ETL e-commerce")
    parser.add_argument("--clean-only", action="store_true", help="Nettoyer sans importer en base")
    args = parser.parse_args()
    run_pipeline(import_db=not args.clean_only)


if __name__ == "__main__":
    main()
