import logging
import os
import re
from dataclasses import dataclass

from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

SQL_PROMPT = """Tu es un expert PostgreSQL spécialisé en Text-to-SQL.

MISSION :
Transformer une question utilisateur en requête SQL PostgreSQL valide.
La question peut être en français, anglais, arabe ou darija marocaine : comprends le sens et génère le SQL.

RÈGLES STRICTES :
1. Générer uniquement du SQL (pas d'explication)
2. Ne jamais inventer de tables ou colonnes
3. Utiliser uniquement le schéma fourni
4. Utiliser JOIN si nécessaire
5. Ajouter LIMIT 10 si l'utilisateur ne précise pas de limite
6. Interdire DROP, DELETE, UPDATE, INSERT, TRUNCATE, ALTER

SCHÉMA :
{schema}

QUESTION :
{question}

SQL :
"""


@dataclass
class AgentConfig:
    db_url: str
    groq_api_key: str
    model: str = "llama-3.3-70b-versatile"
    max_retries: int = 3
    temperature: float = 0.0


def _clean_sql(response: str) -> str:
    text = response.strip()
    text = re.sub(r"^```(?:sql)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


class SQLAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self._llm = ChatGroq(
            api_key=config.groq_api_key,
            model=config.model,
            temperature=config.temperature,
        )
        self._chain = (
            PromptTemplate(
                input_variables=["schema", "question"],
                template=SQL_PROMPT,
            )
            | self._llm
            | StrOutputParser()
        )

    def generate_sql(self, schema: str, question: str) -> str:
        last_error = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                raw = self._chain.invoke({"schema": schema, "question": question})
                sql = _clean_sql(raw)
                logger.info("SQL généré (tentative %s)", attempt)
                return sql
            except Exception as exc:
                last_error = exc
                logger.warning("Échec génération SQL (tentative %s): %s", attempt, exc)
        raise RuntimeError(f"Impossible de générer le SQL: {last_error}")


def load_config() -> AgentConfig:
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    db_url = os.getenv("DATABASE_URL", "").strip()
    return AgentConfig(
        db_url=db_url,
        groq_api_key=groq_key,
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip(),
        max_retries=int(os.getenv("MAX_RETRIES", "3") or "3"),
    )
