"""Génération de diagrammes à partir des résultats SQL."""
import logging

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

_PIE_KEYWORDS = ("camembert", "pie", "secteur", "répartition", "repartition", "part de")
_LINE_KEYWORDS = (
    "courbe", "line", "linéaire", "lineaire", "évolution", "evolution",
    "tendance", "temporel", "timeline",
)
_HIST_KEYWORDS = ("histogramme", "histogram", "distribution", "fréquence", "frequence")
_SCATTER_KEYWORDS = ("scatter", "nuage", "corrélation", "correlation", "dispersion")
_AREA_KEYWORDS = ("area", "aire", "remplissage")


def infer_chart_type(question: str) -> str:
    q = question.lower()
    if any(w in q for w in _PIE_KEYWORDS):
        return "pie"
    if any(w in q for w in _LINE_KEYWORDS):
        return "line"
    if any(w in q for w in _HIST_KEYWORDS):
        return "hist"
    if any(w in q for w in _SCATTER_KEYWORDS):
        return "scatter"
    if any(w in q for w in _AREA_KEYWORDS):
        return "area"
    return "bar"


def _pick_columns(df: pd.DataFrame) -> tuple[str | None, str | None]:
    numeric = df.select_dtypes(include="number").columns.tolist()
    labels = [c for c in df.columns if c not in numeric]

    if labels and numeric:
        return labels[0], numeric[0]
    if len(numeric) >= 2:
        return numeric[0], numeric[1]
    if len(df.columns) >= 2:
        return df.columns[0], df.columns[1]
    if len(df.columns) == 1:
        return df.columns[0], None
    return None, None


def _limit_rows(df: pd.DataFrame, max_rows: int = 30) -> pd.DataFrame:
    if len(df) <= max_rows:
        return df
    return df.head(max_rows)


def render_chart(df: pd.DataFrame, question: str) -> bool:
    """Affiche un diagramme adapté. Retourne False si impossible."""
    if df is None or df.empty:
        return False

    chart_type = infer_chart_type(question)
    plot_df = _limit_rows(df.copy())
    x_col, y_col = _pick_columns(plot_df)
    if x_col is None:
        return False

    try:
        if chart_type == "pie" and y_col:
            import altair as alt

            chart = (
                alt.Chart(plot_df)
                .mark_arc(innerRadius=40)
                .encode(
                    theta=alt.Theta(field=y_col, type="quantitative"),
                    color=alt.Color(field=x_col, type="nominal", legend=alt.Legend(title=x_col)),
                    tooltip=[x_col, y_col],
                )
                .properties(height=360)
            )
            st.altair_chart(chart, use_container_width=True)
            return True

        if chart_type == "hist" and y_col:
            st.bar_chart(plot_df, x=x_col, y=y_col, use_container_width=True)
            return True

        if chart_type == "line" and y_col:
            st.line_chart(plot_df, x=x_col, y=y_col, use_container_width=True)
            return True

        if chart_type == "area" and y_col:
            st.area_chart(plot_df, x=x_col, y=y_col, use_container_width=True)
            return True

        if chart_type == "scatter" and y_col:
            st.scatter_chart(plot_df, x=x_col, y=y_col, use_container_width=True)
            return True

        if y_col:
            st.bar_chart(plot_df, x=x_col, y=y_col, use_container_width=True)
            return True

        st.bar_chart(plot_df, use_container_width=True)
        return True
    except Exception as exc:
        logger.warning("Échec rendu graphique: %s", exc)
        return False
