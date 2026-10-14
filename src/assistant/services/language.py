"""Règles multilingues : arabe, français, anglais, darija."""

LANGUAGE_RULE = """
LANGUE (OBLIGATOIRE) :
Réponds UNIQUEMENT dans la même langue que la question de l'utilisateur.
- Question en français → réponse en français
- Question en anglais → réponse en anglais
- Question en arabe standard (فصحى) → réponse en arabe standard
- Question en darija marocaine (dialecte : شنو، كيفاش، واش، بزاف، etc.) → réponse en darija marocaine naturelle
Ne mélange pas les langues dans une seule réponse.
"""


def language_instruction() -> str:
    return LANGUAGE_RULE.strip()
