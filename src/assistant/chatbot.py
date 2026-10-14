"""Point d'entrée Streamlit — E-commerce LLM Assistant."""
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env", override=True, encoding="utf-8")

import streamlit as st

from src.assistant.components.chat import render_message_history
from src.assistant.components.input_bar import render_input_bar
from src.assistant.components.sidebar import render_sidebar
from src.assistant.components.templates import inject_template
from src.assistant.services.assistant_service import get_pipeline
from src.assistant.utils.config import load_environment
from src.assistant.utils.session import init_session

logging.basicConfig(level=logging.INFO)


def main() -> None:
    st.set_page_config(
        page_title="E-commerce LLM Assistant",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    load_environment()
    init_session()
    inject_template()

    try:
        pipeline = get_pipeline()
    except ValueError as exc:
        st.error(str(exc))
        st.markdown(
            """
            ### Configuration requise
            1. Renseignez `GROQ_API_KEY` et `DATABASE_URL` dans `.env`
            2. Importez les données : `python -m src.etl.pipeline`
            3. Relancez l'application
            """
        )
        return

    config = pipeline["config"]
    example = render_sidebar(pipeline["tables"], config.model)

    st.markdown('<div class="chatgpt-thread">', unsafe_allow_html=True)

    _, chat_col, _ = st.columns([1, 7, 1])
    with chat_col:
        render_message_history()

    st.markdown("</div>", unsafe_allow_html=True)

    _, input_col, _ = st.columns([1, 7, 1])
    with input_col:
        render_input_bar(pipeline, example)


if __name__ == "__main__":
    main()
