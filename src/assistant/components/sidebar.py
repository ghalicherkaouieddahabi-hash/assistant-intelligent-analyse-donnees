import streamlit as st

from src.assistant.components.templates import render_sidebar_brand
from src.assistant.utils.session import clear_history, clear_pdf_document, get_pdf_document

EXAMPLE_QUESTIONS = [
    "Quels sont les 5 produits les plus vendus ?",
    "Graphique des commandes par statut",
    "Quel est le montant moyen des paiements ?",
    "Camembert des ventes par catégorie",
    "Liste les 10 villes avec le plus de clients",
]


def render_sidebar(tables: list[str], model: str) -> str | None:
    selected: str | None = None

    with st.sidebar:
        render_sidebar_brand()

        st.divider()

        st.subheader("⚙️ Configuration")
        st.text_input("Modèle", value=model, disabled=True)
        with st.expander(f"📊 Tables ({len(tables)})", expanded=False):
            for t in sorted(tables):
                st.caption(f"• `{t}`")

        st.divider()

        st.subheader("📎 Document PDF")
        pdf = get_pdf_document()
        if pdf:
            st.caption(f"**{pdf['name']}** — {pdf['pages']} p., {pdf['chars']} car.")
            if st.button("Retirer le PDF", use_container_width=True):
                clear_pdf_document()
                st.session_state.pop("_last_pdf_id", None)
                st.rerun()
        else:
            st.caption("Utilisez le bouton d'import dans la barre de message.")

        st.divider()

        st.subheader("💡 Exemples")
        for i, question in enumerate(EXAMPLE_QUESTIONS):
            if st.button(question, key=f"example_{i}", use_container_width=True):
                selected = question

        st.divider()

        st.subheader("🕐 Historique")
        user_msgs = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
        if not user_msgs:
            st.caption("Aucune question pour l'instant.")
        else:
            for msg in user_msgs[-6:]:
                st.caption(f"• {msg[:55]}{'…' if len(msg) > 55 else ''}")

        st.divider()

        if st.button("🗑️ Effacer la conversation", use_container_width=True, type="secondary"):
            clear_history()
            st.rerun()

        st.caption("Powered by Groq · Llama 3")

    return selected
