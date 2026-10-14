"""Affichage conditionnel : SQL et téléchargement sur demande explicite."""
import re

# Afficher la requête SQL
_SQL_PATTERNS = re.compile(
    r"\b("
    r"sql|requête|requete|query|"
    r"affiche.*requête|montre.*requête|voir.*requête|"
    r"show.*sql|display.*query|"
    r"استعلام|الكود"
    r")\b",
    re.IGNORECASE,
)

# Téléchargement / export
_DOWNLOAD_PATTERNS = re.compile(
    r"\b("
    r"télécharg|telecharg|download|export|exporter|"
    r"fichier csv|en csv|"
    r"حمّل|تحميل|نزّل"
    r")\b",
    re.IGNORECASE,
)


# Graphique / diagramme / visualisation
_CHART_PATTERNS = re.compile(
    r"\b("
    r"graphique|diagramme|chart|plot|graphe|visualis|"
    r"histogramme|histogram|camembert|pie|"
    r"barre|bar chart|courbe|line chart|"
    r"scatter|nuage|"
    r"رسم|مخطط|بياني"
    r")\b",
    re.IGNORECASE,
)


def wants_sql(text: str) -> bool:
    return bool(_SQL_PATTERNS.search(text))


def wants_download(text: str) -> bool:
    return bool(_DOWNLOAD_PATTERNS.search(text))


def wants_chart(text: str) -> bool:
    return bool(_CHART_PATTERNS.search(text))


def is_followup_only(question: str, intent: str) -> bool:
    """Demande d'afficher SQL, CSV ou graphique des derniers résultats."""
    if intent == "ECOMMERCE":
        return False
    return wants_sql(question) or wants_download(question) or wants_chart(question)
