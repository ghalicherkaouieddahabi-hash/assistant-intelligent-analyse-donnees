import html
import logging

import streamlit as st

from src.assistant.components.results import render_dataframe
from src.assistant.services.assistant_service import ask
from src.assistant.utils.session import add_message

logger = logging.getLogger(__name__)

_WELCOME = """
<div class="welcome-centered">
  <h1>Bienvenue</h1>
</div>
"""


def _render_welcome() -> None:
    st.markdown(_WELCOME, unsafe_allow_html=True)


def _user_bubble(text: str) -> None:
    safe = html.escape(text).replace("\n", "<br>")
    st.markdown(
        f'<div class="chat-msg-row chat-msg-right">'
        f'<div class="chat-bubble chat-bubble-user">{safe}</div></div>',
        unsafe_allow_html=True,
    )


def _assistant_content(
    content: str,
    *,
    sql: str | None = None,
    show_sql: bool = False,
    dataframe=None,
    show_download: bool = False,
    show_chart: bool = False,
    chart_question: str | None = None,
    success: bool = True,
) -> None:
    st.markdown('<div class="chat-msg-row chat-msg-left">', unsafe_allow_html=True)
    st.markdown('<div class="chat-assistant-block">', unsafe_allow_html=True)
    st.markdown(content)

    if show_sql and sql:
        with st.expander("Requête SQL", expanded=False):
            st.code(sql, language="sql")

    if dataframe is not None and success:
        render_dataframe(
            dataframe,
            show_download=show_download,
            show_chart=show_chart,
            chart_question=chart_question,
        )

    st.markdown("</div></div>", unsafe_allow_html=True)


def _render_single_message(message: dict) -> None:
    if message["role"] == "user":
        _user_bubble(message["content"])
    else:
        _assistant_content(
            message["content"],
            sql=message.get("sql"),
            show_sql=message.get("show_sql", False),
            dataframe=message.get("dataframe"),
            show_download=message.get("show_download", False),
            show_chart=message.get("show_chart", False),
            chart_question=message.get("chart_question"),
            success=message.get("success", True),
        )


def render_message_history() -> None:
    if not st.session_state.messages:
        _render_welcome()
        return
    for message in st.session_state.messages:
        _render_single_message(message)


def process_user_input(prompt: str, pipeline: dict) -> None:
    add_message("user", prompt)
    with st.spinner("Réflexion en cours..."):
        try:
            result = ask(prompt, pipeline)
            has_table = result.get("dataframe") is not None
            add_message(
                "assistant",
                result["summary"],
                dataframe=result["dataframe"] if has_table else None,
                sql=result.get("sql"),
                success=result["success"],
                show_sql=result.get("show_sql", False),
                show_download=result.get("show_download", False),
                show_chart=result.get("show_chart", False),
                chart_question=result.get("chart_question"),
            )
        except Exception as exc:
            logger.exception("Erreur assistant")
            add_message("assistant", f"Une erreur est survenue : {exc}", success=False)
    st.rerun()
