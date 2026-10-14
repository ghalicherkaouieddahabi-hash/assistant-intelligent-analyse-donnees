"""Nettoyage des CSV Olist : data/raw -> data/processed."""
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

OLIST_FILES = [
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates().copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace("nan", "Inconnu").fillna("Inconnu")
    for col in df.select_dtypes(include=np.number).columns:
        median = df[col].median()
        df[col] = df[col].fillna(median)
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            df = df[(df[col] >= lower) & (df[col] <= upper)]
    return df


def clean_file(src: Path, dest: Path) -> int:
    df = pd.read_csv(src)
    rows_before = len(df)
    cleaned = clean_dataframe(df)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(dest, index=False)
    logger.info("%s : %s -> %s lignes", src.name, rows_before, len(cleaned))
    return len(cleaned)


def run_clean(raw_dir: Path, processed_dir: Path, files: list[str] | None = None) -> dict[str, int]:
    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    targets = files or OLIST_FILES
    stats: dict[str, int] = {}
    for name in targets:
        src = raw_dir / name
        if not src.exists():
            logger.warning("Fichier absent, ignoré : %s", name)
            continue
        stats[name] = clean_file(src, processed_dir / name)
    return stats
