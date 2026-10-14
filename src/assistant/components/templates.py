import html
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
HTML_DIR = STATIC_DIR / "html"
CSS_FILE = STATIC_DIR / "css" / "main.css"


def _read(name: str) -> str:
    return (HTML_DIR / name).read_text(encoding="utf-8")


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def render_sidebar_brand() -> None:
    st.markdown(_read("sidebar_brand.html"), unsafe_allow_html=True)


def inject_template() -> None:
    css = CSS_FILE.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _wrap_html(body: str) -> str:
    """Inclut le CSS dans l'iframe (components.html n'hérite pas du parent)."""
    css = CSS_FILE.read_text(encoding="utf-8")
    return (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{css}</style></head><body>{body}</body></html>"
    )


def render_html_fragment(fragment: str, height: int | None = None) -> None:
    wrapped = _wrap_html(fragment)
    if height is not None:
        components.html(wrapped, height=height, scrolling=True)
    else:
        st.markdown(fragment, unsafe_allow_html=True)


def render_header(model: str, table_count: int, question_count: int) -> None:
    tpl = _read("header.html")
    fragment = tpl.format(
        title="E-commerce LLM Assistant",
        subtitle="Multilingue : FR · EN · AR · Darija — Text-to-SQL Llama 3 (Groq)",
        model=_esc(model),
        table_count=table_count,
        question_count=question_count,
    )
    render_html_fragment(fragment, height=200)


def _build_sql_block(sql: str, success: bool) -> str:
    label = "Requête SQL" if success else "SQL (non exécuté)"
    tpl = _read("sql_block.html")
    return tpl.format(sql_label=label, sql=_esc(sql))


def _build_message(
    role: str,
    content: str,
    sql: str | None = None,
    success: bool = True,
    show_sql: bool = False,
) -> str:
    role_class = "user" if role == "user" else "assistant"
    role_label = "Vous" if role == "user" else "Assistant"
    extra = "" if success or role == "user" else "error-bubble"
    sql_block = _build_sql_block(sql, success) if sql and show_sql else ""
    tpl = _read("message.html")
    return tpl.format(
        role_class=role_class,
        extra_class=extra,
        role_label=role_label,
        content=_esc(content).replace("\n", "<br>"),
        sql_block=sql_block,
    )


def render_welcome() -> None:
    render_html_fragment(_read("welcome.html"), height=280)


def render_chat(messages: list[dict]) -> None:
    if not messages:
        render_welcome()
        return
    parts = [
        _build_message(
            m["role"],
            m["content"],
            m.get("sql"),
            m.get("success", True),
            m.get("show_sql", False),
        )
        for m in messages
    ]
    tpl = _read("chat.html")
    fragment = tpl.format(messages="\n".join(parts))
    height = min(560, max(320, 90 * len(messages) + 120))
    render_html_fragment(fragment, height=height)
