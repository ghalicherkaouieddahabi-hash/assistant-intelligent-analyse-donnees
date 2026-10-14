import streamlit as st
import pandas as pd

from src.assistant.services.chart_service import render_chart


def render_dataframe(
    df: pd.DataFrame,
    *,
    show_download: bool = False,
    show_chart: bool = False,
    chart_question: str | None = None,
) -> None:
    if df is None or df.empty:
        st.caption("Aucune donnée à afficher.")
        return

    if show_chart:
        if render_chart(df, chart_question or ""):
            st.caption("Diagramme généré à partir des résultats.")
        else:
            st.warning("Impossible de générer le diagramme pour ces données.")

    st.dataframe(df, use_container_width=True, height=min(320, 35 * len(df) + 38))

    if show_download:
        st.download_button(
            label="Télécharger CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="resultats_olist.csv",
            mime="text/csv",
            use_container_width=True,
        )
