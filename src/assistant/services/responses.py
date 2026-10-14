"""Résumés e-commerce dans la langue de l'utilisateur."""
import logging

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from src.assistant.services.language import language_instruction
from src.etl.core.sql_agent import AgentConfig

logger = logging.getLogger(__name__)

_SUMMARY_PROMPT = """{language_rule}

L'utilisateur a posé cette question : {question}

Contexte technique (ne pas répéter le SQL) :
{context}

Rédige un message court (1 à 2 phrases) pour informer l'utilisateur du résultat.
"""

_REJECT_PROMPT = """{language_rule}

Question : {question}
Problème : {error}

Explique poliment en une ou deux phrases pourquoi la requête n'a pas été exécutée.
"""


def _llm(config: AgentConfig, temperature: float = 0.3) -> ChatGroq:
    return ChatGroq(
        api_key=config.groq_api_key,
        model=config.model,
        temperature=temperature,
    )


def ecommerce_summary(
    config: AgentConfig,
    question: str,
    row_count: int,
    *,
    empty: bool = False,
) -> str:
    if empty:
        context = "La requête SQL a réussi mais 0 ligne retournée."
    else:
        context = f"La requête a retourné {row_count} ligne(s) de données."
    chain = (
        PromptTemplate(
            input_variables=["language_rule", "question", "context"],
            template=_SUMMARY_PROMPT,
        )
        | _llm(config)
        | StrOutputParser()
    )
    try:
        return chain.invoke(
            {
                "language_rule": language_instruction(),
                "question": question,
                "context": context,
            }
        ).strip()
    except Exception as exc:
        logger.warning("Résumé multilingue échoué: %s", exc)
        return _fallback_summary(row_count, empty)


def ecommerce_rejection(
    config: AgentConfig,
    question: str,
    error: str,
) -> str:
    chain = (
        PromptTemplate(
            input_variables=["language_rule", "question", "error"],
            template=_REJECT_PROMPT,
        )
        | _llm(config)
        | StrOutputParser()
    )
    try:
        return chain.invoke(
            {
                "language_rule": language_instruction(),
                "question": question,
                "error": error,
            }
        ).strip()
    except Exception as exc:
        logger.warning("Message rejet multilingue échoué: %s", exc)
        return f"Requête refusée : {error}"


def _fallback_summary(row_count: int, empty: bool) -> str:
    if empty:
        return "La requête s'est exécutée mais aucune ligne n'a été retournée."
    return f"J'ai trouvé {row_count} résultat(s) pour votre question."
