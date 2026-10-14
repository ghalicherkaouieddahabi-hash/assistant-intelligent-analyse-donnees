"""Lance le nettoyage depuis notebooks/ (wrapper)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.etl.clean_data import run_clean

if __name__ == "__main__":
    stats = run_clean(ROOT / "data" / "raw", ROOT / "data" / "processed")
    for name, rows in stats.items():
        print(f"{name} : {rows} lignes")
    print("Nettoyage terminé.")
