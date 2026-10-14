import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine


def execute_query(query: str) -> pd.DataFrame:
    with get_engine().connect() as connection:
        result = connection.execute(text(query))
        rows = result.fetchall()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows, columns=result.keys())
