"""Extraction et analyse de PDF projet."""
import logging
from io import BytesIO

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from src.assistant.services.language import language_instruction
from src.etl.core.sql_agent import AgentConfig

logger = logging.getLogger(__name__)

MAX_PDF_CHARS = 80_000
MAX_CONTEXT_CHARS = 14_000

_PDF_QA_PROMPT = """{language_rule}

Tu es l'assistant e-commerce Olist. L'utilisateur a importé un document PDF lié au projet.
Réponds UNIQUEMENT à partir du contenu ci-dessous. Si la réponse n'est pas dans le document, dis-le clairement.
Ne invente pas de chiffres ni de faits absents du PDF.

--- Document : {filename} ---
{content}
--- Fin du document ---

Question : {question}

Réponse :"""


def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, int]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ImportError(
            "Le module pypdf est requis. Exécutez : .\\venv\\Scripts\\pip install pypdf"
        ) from exc
    reader = PdfReader(BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    full = "\n\n".join(pages).strip()
    return full[:MAX_PDF_CHARS], len(reader.pages)


def answer_from_pdf(config: AgentConfig, question: str, filename: str, text: str) -> str:
    content = text[:MAX_CONTEXT_CHARS]
    if len(text) > MAX_CONTEXT_CHARS:
        content += "\n\n[… document tronqué pour l'analyse …]"
    llm = ChatGroq(
        api_key=config.groq_api_key,
        model=config.model,
        temperature=0.3,
    )
    chain = (
        PromptTemplate(
            input_variables=["language_rule", "filename", "content", "question"],
            template=_PDF_QA_PROMPT,
        )
        | llm
        | StrOutputParser()
    )
    return chain.invoke(
        {
            "language_rule": language_instruction(),
            "filename": filename,
            "content": content,
            "question": question,
        }
    ).strip()
