import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_connection  # noqa: E402

st.set_page_config(page_title="Ficha del árbitro", page_icon="📋", layout="wide")

conn = get_connection()
ranking = conn.query("select * from gold.v_ranking_arbitro", ttl=3600)

st.title("Ficha del árbitro")

nombres = sorted(ranking["nombre_canonico"].tolist())
seleccion = st.selectbox("Árbitro", nombres)

fila = ranking[ranking["nombre_canonico"] == seleccion].iloc[0]
arbitro_id = fila["arbitro_id"]

st.subheader(seleccion)
st.metric("Partidos dirigidos", int(fila["partidos_dirigidos"]))

# P2: retrato completo en total y tasa/partido, partidos dirigidos siempre a la vista (D11/D12).
col1, col2, col3, col4 = st.columns(4)
col1.metric("Amarillas", int(fila["total_amarillas"]), f"{fila['tasa_amarillas']}/partido")
col2.metric("Segundas amarillas", int(fila["total_segundas_amarillas"]), f"{fila['tasa_segundas_amarillas']}/partido")
col3.metric("Rojas directas", int(fila["total_rojas_directas"]), f"{fila['tasa_rojas_directas']}/partido")
col4.metric("Penaltis señalados", int(fila["total_penaltis"]), f"{fila['tasa_penaltis']}/partido")

col5, col6 = st.columns(2)
col5.metric("Faltas pitadas", int(fila["total_faltas"]), f"{fila['tasa_faltas']}/partido")
col6.metric("Decisiones VAR con impacto", int(fila["decisiones_var_con_impacto"]), f"{fila['tasa_var_con_impacto']}/partido")

st.divider()
st.subheader("Desglose por equipo")
st.caption("Conteos brutos — sin analizador de sesgo (D2, D14).")

equipo_df = conn.query(
    """
    select f.*, eq.nombre_canonico as equipo
    from gold.v_ficha_arbitro_equipo f
    join silver.equipo eq on eq.equipo_id = f.equipo_id
    where f.arbitro_id = :arbitro_id
    order by eq.nombre_canonico
    """,
    params={"arbitro_id": arbitro_id},
    ttl=3600,
)

if equipo_df.empty:
    st.write("Sin datos de equipo para este árbitro.")
else:
    tabla_equipo = equipo_df[[
        "equipo", "total_amarillas", "total_segundas_amarillas", "total_rojas_directas",
        "total_penaltis_a_favor", "total_penaltis_en_contra", "total_faltas",
    ]].rename(columns={
        "equipo": "Equipo",
        "total_amarillas": "Amarillas",
        "total_segundas_amarillas": "2ª amarilla",
        "total_rojas_directas": "Rojas directas",
        "total_penaltis_a_favor": "Penaltis a favor",
        "total_penaltis_en_contra": "Penaltis en contra",
        "total_faltas": "Faltas",
    })
    st.dataframe(tabla_equipo, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Actividad VAR")
st.caption(
    "Las confirmaciones son contexto de segundo nivel, no se ranquean (D35). "
    "Solo se cuentan revisiones que llegaron a comunicarse — los *checks* silenciosos no están "
    "en la fuente."
)

var_df = conn.query(
    "select * from gold.v_ficha_arbitro_var where arbitro_id = :arbitro_id",
    params={"arbitro_id": arbitro_id},
    ttl=3600,
)

if var_df.empty:
    st.write("Sin decisiones VAR registradas para este árbitro.")
else:
    tabla_var = var_df.rename(columns={
        "tipo_decision_revisada": "Tipo de decisión",
        "total_modifica": "Modificadas",
        "total_confirma": "Confirmadas (contexto)",
    })
    st.dataframe(
        tabla_var[["Tipo de decisión", "Modificadas", "Confirmadas (contexto)"]],
        use_container_width=True, hide_index=True,
    )
