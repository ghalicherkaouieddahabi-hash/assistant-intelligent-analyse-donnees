"""Import des CSV nettoyés vers PostgreSQL."""
import logging
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


def import_to_postgres(processed_dir: Path, database_url: str | None = None) -> list[str]:
    processed_dir = Path(processed_dir)
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL est requis")
    engine = create_engine(url)
    imported: list[str] = []
    for csv_path in sorted(processed_dir.glob("*.csv")):
        table = csv_path.stem
        logger.info("Import %s -> %s", csv_path.name, table)
        df = pd.read_csv(csv_path)
        df.to_sql(table, engine, if_exists="replace", index=False, method="multi", chunksize=5000)
        imported.append(table)
    return imported
