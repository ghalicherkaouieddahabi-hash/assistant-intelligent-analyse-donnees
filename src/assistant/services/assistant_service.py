import logging

import streamlit as st

from src.assistant.services.display_prefs import (
    is_followup_only,
    wants_chart,
    wants_download,
    wants_sql,
)
from src.assistant.services.intent import (
    classify_question,
    greeting_reply,
    off_topic_reply,
)
from src.assistant.utils.session import get_pdf_document
from src.assistant.services.responses import ecommerce_rejection, ecommerce_summary
from src.assistant.utils.session import last_ecommerce_result
from src.db.query_executor import execute_query
from src.etl.core.hallucination_detector import HallucinationDetector
from src.etl.core.schema_manager import SchemaManager
from src.etl.core.sql_agent import SQLAgent, load_config

logger = logging.getLogger(__name__)


@st.cache_resource(show_spinner="Connexion à la base et chargement du modèle...")
def get_pipeline():
    from src.assistant.utils.config import load_environment

    load_environment()
    config = load_config()
    if not config.groq_api_key:
        raise ValueError("GROQ_API_KEY manquant — configurez `.env` ou `.streamlit/secrets.toml`")
    if not config.db_url:
        raise ValueError("DATABASE_URL manquant — configurez `.env` ou `.streamlit/secrets.toml`")
    schema_manager = SchemaManager(config.db_url)
    tables = schema_manager.get_table_names()
    return {
        "config": config,
        "schema": schema_manager.get_schema(),
        "tables": tables,
        "agent": SQLAgent(config),
        "detector": HallucinationDetector(tables),
    }


def _followup_response(question: str, config, show_sql: bool, show_download: bool, show_chart: bool) -> dict:
    last = last_ecommerce_result()
    if not last:
        text = off_topic_reply(
            config,
            "Je n'ai pas encore de résultats. Posez d'abord une question sur les données e-commerce.",
        )
        return {
            "mode": "off_topic",
            "success": True,
            "sql": None,
            "summary": text,
            "dataframe": None,
            "row_count": 0,
            "show_sql": False,
            "show_download": False,
            "show_chart": False,
            "chart_question": None,
        }

    parts = []
    if show_sql and last.get("sql"):
        parts.append("Voici la requête SQL demandée.")
    if show_download and last.get("dataframe") is not None:
        parts.append("Le téléchargement des résultats est disponible ci-dessous.")
    if show_chart and last.get("dataframe") is not None:
        parts.append("Voici le diagramme demandé.")
    summary = " ".join(parts) if parts else greeting_reply(config, question)

    need_data = show_download or show_chart
    return {
        "mode": "ecommerce",
        "success": True,
        "sql": last.get("sql") if show_sql else None,
        "summary": summary,
        "dataframe": last.get("dataframe") if need_data else None,
        "row_count": len(last["dataframe"]) if need_data and last.get("dataframe") is not None else 0,
        "show_sql": show_sql,
        "show_download": show_download,
        "show_chart": show_chart,
        "chart_question": question if show_chart else None,
    }


def ask(question: str, pipeline: dict) -> dict:
    config = pipeline["config"]
    pdf_doc = get_pdf_document()
    has_pdf = pdf_doc is not None
    intent = classify_question(config, question, has_pdf=has_pdf)
    show_sql = wants_sql(question)
    show_download = wants_download(question)
    show_chart = wants_chart(question)

    if is_followup_only(question, intent):
        return _followup_response(question, config, show_sql, show_download, show_chart)

    if intent == "DOCUMENT":
        if not pdf_doc:
            return {
                "mode": "document",
                "success": True,
                "sql": None,
                "summary": off_topic_reply(
                    config,
                    "Importez d'abord un PDF avec le bouton d'import à gauche de la barre de message.",
                ),
                "dataframe": None,
                "row_count": 0,
                "show_sql": False,
                "show_download": False,
                "show_chart": False,
                "chart_question": None,
            }
        from src.assistant.services.pdf_service import answer_from_pdf

        summary = answer_from_pdf(
            config,
            question,
            pdf_doc["name"],
            pdf_doc["text"],
        )
        return {
            "mode": "document",
            "success": True,
            "sql": None,
            "summary": summary,
            "dataframe": None,
            "row_count": 0,
            "show_sql": False,
            "show_download": False,
            "show_chart": False,
            "chart_question": None,
        }

    if intent == "GREETING":
        return {
            "mode": "greeting",
            "success": True,
            "sql": None,
            "summary": greeting_reply(config, question),
            "dataframe": None,
            "row_count": 0,
            "show_sql": False,
            "show_download": False,
            "show_chart": False,
            "chart_question": None,
        }

    if intent == "OFF_TOPIC":
        return {
            "mode": "off_topic",
            "success": True,
            "sql": None,
            "summary": off_topic_reply(config, question),
            "dataframe": None,
            "row_count": 0,
            "show_sql": False,
            "show_download": False,
            "show_chart": False,
            "chart_question": None,
        }

    agent: SQLAgent = pipeline["agent"]
    detector: HallucinationDetector = pipeline["detector"]
    schema: str = pipeline["schema"]

    sql = agent.generate_sql(schema, question)
    ok, msg = detector.validate(sql)
    if not ok:
        return {
            "mode": "ecommerce",
            "success": False,
            "sql": sql,
            "summary": ecommerce_rejection(config, question, msg),
            "dataframe": None,
            "row_count": 0,
            "show_sql": show_sql,
            "show_download": False,
            "show_chart": False,
            "chart_question": None,
        }

    df = execute_query(sql)
    n = len(df)
    summary = ecommerce_summary(config, question, n, empty=(n == 0))
    has_data = n > 0

    return {
        "mode": "ecommerce",
        "success": True,
        "sql": sql,
        "summary": summary,
        "dataframe": df if has_data else None,
        "row_count": n,
        "show_sql": show_sql,
        "show_download": show_download and has_data,
        "show_chart": show_chart and has_data,
        "chart_question": question if show_chart and has_data else None,
    }
