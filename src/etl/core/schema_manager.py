import logging
import os

from langchain_community.utilities import SQLDatabase

logger = logging.getLogger(__name__)


class SchemaManager:
    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "")
        if not self.db_url:
            raise ValueError("DATABASE_URL est requis")
        self._db = SQLDatabase.from_uri(self.db_url)

    def get_schema(self) -> str:
        schema = self._db.get_table_info()
        logger.debug("Schéma chargé (%s caractères)", len(schema))
        return schema

    def get_table_names(self) -> list[str]:
        return list(self._db.get_usable_table_names())
