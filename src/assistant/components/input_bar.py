"""Barre de saisie unifiée : PDF + message sur une seule ligne."""
import streamlit as st

from src.assistant.services.pdf_service import extract_text_from_pdf
from src.assistant.utils.session import get_pdf_document, set_pdf_document


def handle_pdf_upload(uploaded) -> bool:
    """Importe un PDF. Retourne True si un nouveau document a été chargé."""
    if uploaded is None:
        return False
    last = st.session_state.get("_last_pdf_id")
    file_id = f"{uploaded.name}_{uploaded.size}"
    if last == file_id:
        return False
    st.session_state._last_pdf_id = file_id
    try:
        text, pages = extract_text_from_pdf(uploaded.getvalue())
        if not text.strip():
            st.warning("Le PDF ne contient pas de texte extractible.")
            return False
        set_pdf_document(uploaded.name, text, pages)
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    f"**PDF importé :** `{uploaded.name}` "
                    f"({pages} page(s), {len(text)} caractères). "
                    f"Vous pouvez poser des questions sur ce document."
                ),
                "dataframe": None,
                "sql": None,
                "success": True,
                "show_sql": False,
                "show_download": False,
            }
        )
        return True
    except Exception as exc:
        st.error(f"Impossible de lire le PDF : {exc}")
        return False


def _extract_prompt(prompt) -> tuple[str, list]:
    if hasattr(prompt, "text"):
        return (prompt.text or "").strip(), list(prompt.files or [])
    if isinstance(prompt, dict):
        return (prompt.get("text") or "").strip(), list(prompt.get("files") or [])
    return str(prompt).strip(), []


def render_input_bar(pipeline: dict, example: str | None) -> None:
    doc = get_pdf_document()
    if doc:
        st.markdown(
            f'<p class="input-bar-pdf-tag">📄 {doc["name"]} — {doc["pages"]} page(s)</p>',
            unsafe_allow_html=True,
        )

    if example:
        from src.assistant.components.chat import process_user_input

        process_user_input(example, pipeline)
        return

    prompt = st.chat_input(
        "Message à l'assistant…",
        accept_file=True,
        file_type=["pdf"],
        key="main_chat_input",
    )

    if not prompt:
        return

    text, files = _extract_prompt(prompt)
    pdf_loaded = False
    for uploaded in files:
        if handle_pdf_upload(uploaded):
            pdf_loaded = True

    if text:
        from src.assistant.components.chat import process_user_input

        process_user_input(text, pipeline)
    elif pdf_loaded:
        st.rerun()
