import logging
import re

logger = logging.getLogger(__name__)

FORBIDDEN_KEYWORDS = frozenset(
    {"DROP", "DELETE", "UPDATE", "TRUNCATE", "ALTER", "INSERT", "CREATE", "GRANT", "REVOKE"}
)


class HallucinationDetector:
    def __init__(self, table_names: list[str]):
        self.table_names = {name.lower() for name in table_names}

    def is_safe_query(self, query: str) -> bool:
        upper = query.upper()
        for word in FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{word}\b", upper):
                logger.warning("Mot-clé interdit détecté: %s", word)
                return False
        return True

    def references_known_tables(self, query: str) -> bool:
        if not self.table_names:
            return True
        pattern = r"(?:from|join)\s+([a-z_][a-z0-9_]*)"
        referenced = set(re.findall(pattern, query.lower()))
        unknown = referenced - self.table_names
        if unknown:
            logger.warning("Tables inconnues dans la requête: %s", unknown)
            return False
        return True

    def validate(self, query: str) -> tuple[bool, str]:
        if not query.strip():
            return False, "Requête vide"
        if not self.is_safe_query(query):
            return False, "Requête non autorisée (écriture ou DDL détectée)"
        if not self.references_known_tables(query):
            return False, "Tables ou colonnes non reconnues dans le schéma"
        return True, "OK"
