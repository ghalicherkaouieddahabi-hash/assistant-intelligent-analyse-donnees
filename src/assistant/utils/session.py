import streamlit as st


def get_pdf_document() -> dict | None:
    return st.session_state.get("pdf_document")


def set_pdf_document(name: str, text: str, pages: int) -> None:
    st.session_state.pdf_document = {
        "name": name,
        "text": text,
        "pages": pages,
        "chars": len(text),
    }


def clear_pdf_document() -> None:
    st.session_state.pdf_document = None


def init_session() -> None:
    defaults = {
        "messages": [],
        "pending_prompt": None,
        "pdf_document": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_history() -> None:
    st.session_state.messages = []
    st.session_state.pending_prompt = None


def add_message(
    role: str,
    content: str,
    dataframe=None,
    sql: str | None = None,
    success: bool = True,
    show_sql: bool = False,
    show_download: bool = False,
    show_chart: bool = False,
    chart_question: str | None = None,
) -> None:
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
            "dataframe": dataframe,
            "sql": sql,
            "success": success,
            "show_sql": show_sql,
            "show_download": show_download,
            "show_chart": show_chart,
            "chart_question": chart_question,
        }
    )


def last_ecommerce_result() -> dict | None:
    for msg in reversed(st.session_state.get("messages", [])):
        if msg.get("role") == "assistant" and msg.get("dataframe") is not None:
            return msg
    return None
