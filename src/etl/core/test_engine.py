import logging
import os

from dotenv import load_dotenv

from src.db.query_executor import execute_query
from src.etl.core.hallucination_detector import HallucinationDetector
from src.etl.core.schema_manager import SchemaManager
from src.etl.core.sql_agent import SQLAgent, load_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


SAMPLE_QUESTIONS = [
    "Quels sont les 5 produits les plus vendus ?",
    "Quel est le montant moyen des paiements ?",
]


def run_tests() -> None:
    load_dotenv()
    config = load_config()
    if not config.groq_api_key:
        raise ValueError("GROQ_API_KEY manquant dans .env")

    schema_manager = SchemaManager(config.db_url)
    agent = SQLAgent(config)
    detector = HallucinationDetector(schema_manager.get_table_names())

    for question in SAMPLE_QUESTIONS:
        print(f"\n--- Question: {question}")
        sql = agent.generate_sql(schema_manager.get_schema(), question)
        print(f"SQL: {sql}")
        ok, msg = detector.validate(sql)
        print(f"Validation: {ok} ({msg})")
        if ok:
            df = execute_query(sql)
            print(df.head())


if __name__ == "__main__":
    run_tests()
