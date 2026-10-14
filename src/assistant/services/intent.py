"""Routage : e-commerce, salutation, ou hors sujet."""
import logging

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from src.assistant.services.language import language_instruction
from src.etl.core.sql_agent import AgentConfig

logger = logging.getLogger(__name__)

_CLASSIFY_PROMPT = """Tu classifies les messages pour un assistant e-commerce Olist (base SQL + PDF projet optionnel).

{pdf_hint}

Réponds par EXACTEMENT un seul mot (en anglais) :
- ECOMMERCE : stats/listes/chiffres sur ventes, commandes, produits, clients (base de données)
- DOCUMENT : question sur le PDF importé (résumé, analyse, extraire une info du fichier, expliquer le doc)
- GREETING : salutation courte uniquement (bonjour, hello, merci)
- OFF_TOPIC : hors sujet (sport, CR7, culture générale sans lien avec Olist ni le PDF)

Question : {question}

Mot :"""

_GREETING_PROMPT = """{language_rule}

Tu es l'assistant **e-commerce Olist** (analyse de ventes en ligne). Tu ne traites que les données de ce projet.

L'utilisateur te salue. Réponds en 1-2 phrases : salut + invite-le à poser une question sur les données.
Donne 2 exemples courts (ex. produits les plus vendus, montant moyen des paiements).
Ne réponds à aucun autre sujet.

Message : {question}

Réponse :"""

_OFF_TOPIC_PROMPT = """{language_rule}

Tu es l'assistant **e-commerce Olist**. Tu interroges UNIQUEMENT la base de données du projet (ventes, commandes, produits, clients…).

L'utilisateur a posé une question **hors sujet** (pas liée à ces données).

RÈGLES STRICTES :
1. Ne réponds PAS au contenu de la question (pas de biographie, pas de faits généraux).
2. Dis poliment que tu es limité aux analyses e-commerce Olist.
3. Propose 2 exemples de questions valides sur les données.

Question hors sujet : {question}

Réponse courte :"""


def _normalize_class(raw: str) -> str:
    u = raw.strip().upper().replace('"', "").replace("'", "")
    if "DOCUMENT" in u or "PDF" in u:
        return "DOCUMENT"
    if "ECOMMERCE" in u or "E-COMMERCE" in u or u.startswith("ECOM"):
        return "ECOMMERCE"
    if "GREETING" in u or "SALUT" in u or "HELLO" in u:
        return "GREETING"
    if "OFF" in u and "TOPIC" in u:
        return "OFF_TOPIC"
    if "OFF_TOPIC" in u.replace(" ", "_"):
        return "OFF_TOPIC"
    return "OFF_TOPIC"


def classify_question(config: AgentConfig, question: str, *, has_pdf: bool = False) -> str:
    pdf_hint = (
        "Un PDF projet est chargé : classe DOCUMENT si la question concerne ce fichier."
        if has_pdf
        else "Aucun PDF chargé : ne utilise jamais DOCUMENT."
    )
    llm = ChatGroq(
        api_key=config.groq_api_key,
        model=config.model,
        temperature=0.0,
    )
    chain = (
        PromptTemplate(
            input_variables=["question", "pdf_hint"],
            template=_CLASSIFY_PROMPT,
        )
        | llm
        | StrOutputParser()
    )
    try:
        out = chain.invoke({"question": question, "pdf_hint": pdf_hint}).strip()
        label = _normalize_class(out)
        logger.info("Intent classifié: %s (brut: %s)", label, out[:80])
        return label
    except Exception as exc:
        logger.warning("Échec classification, défaut OFF_TOPIC: %s", exc)
        return "OFF_TOPIC"


def _scoped_reply(config: AgentConfig, question: str, template: str) -> str:
    llm = ChatGroq(
        api_key=config.groq_api_key,
        model=config.model,
        temperature=0.2,
    )
    chain = (
        PromptTemplate(
            input_variables=["language_rule", "question"],
            template=template,
        )
        | llm
        | StrOutputParser()
    )
    return chain.invoke(
        {"language_rule": language_instruction(), "question": question}
    ).strip()


def greeting_reply(config: AgentConfig, question: str) -> str:
    return _scoped_reply(config, question, _GREETING_PROMPT)


def off_topic_reply(config: AgentConfig, question: str) -> str:
    return _scoped_reply(config, question, _OFF_TOPIC_PROMPT)
