import streamlit as st

from db import get_connection

st.set_page_config(page_title="Observatorio Arbitral de LaLiga", page_icon="🟨", layout="wide")

st.title("Observatorio Arbitral de LaLiga")
st.caption("Perfilador de árbitros de Primera División — temporada 2025-26.")

conn = get_connection()
ranking = conn.query("select * from gold.v_ranking_arbitro", ttl=3600)

# D2/D11: solo eventos objetivamente verificables; no juzga acierto/error.
METRICAS = {
    "Amarillas": ("total_amarillas", "tasa_amarillas", "mediana_liga_tasa_amarillas"),
    "Segundas amarillas": ("total_segundas_amarillas", "tasa_segundas_amarillas", None),
    "Rojas directas": ("total_rojas_directas", "tasa_rojas_directas", None),
    "Penaltis señalados": ("total_penaltis", "tasa_penaltis", None),
    "Faltas pitadas": ("total_faltas", "tasa_faltas", "mediana_liga_tasa_faltas"),
    "Decisiones VAR con impacto": ("decisiones_var_con_impacto", "tasa_var_con_impacto", None),
}

col1, col2 = st.columns([2, 1])
with col1:
    metrica_label = st.selectbox("Métrica", list(METRICAS.keys()))
with col2:
    modo = st.radio("Ver por", ["Tasa por partido", "Total bruto"], horizontal=True)

total_col, tasa_col, mediana_col = METRICAS[metrica_label]

# D12: tasa por partido como base de comparabilidad, con total bruto y
# partidos dirigidos (denominador) siempre visibles — nunca se oculta un
# árbitro por muestra pequeña, se muestra el denominador (D6, P6).
tabla = ranking[["nombre_canonico", "partidos_dirigidos", total_col, tasa_col]].copy()
tabla.columns = ["Árbitro", "Partidos dirigidos", "Total", "Tasa/partido"]
orden_por = "Tasa/partido" if modo == "Tasa por partido" else "Total"
tabla = tabla.sort_values(orden_por, ascending=False).reset_index(drop=True)

st.dataframe(tabla, use_container_width=True, hide_index=True)

# D15: mediana de liga SOLO en métricas de volumen (amarillas, faltas).
if mediana_col and ranking[mediana_col].notna().any():
    mediana = ranking[mediana_col].iloc[0]
    st.caption(
        f"Mediana de liga para «{metrica_label}»: **{mediana}** por partido. "
        "(Referencia mostrada solo en métricas de volumen — D15.)"
    )

# D37: etiqueta contextual breve en el ranking VAR, con enlace a la
# explicación completa (requisito duro del MVP, no opcional).
if metrica_label == "Decisiones VAR con impacto":
    st.info(
        "Cuenta solo decisiones VAR que **modificaron** la decisión de campo, no el total de "
        "revisiones. No incluye los *checks* silenciosos de cabina (no están en la fuente). "
        "Se atribuye siempre al árbitro principal, no al árbitro VAR."
    )
    st.page_link("pages/2_Metodologia.py", label="Ver metodología completa", icon="📖")

st.divider()
st.caption("Elige un árbitro en **Ficha del árbitro** (barra lateral) para ver su perfil completo.")
