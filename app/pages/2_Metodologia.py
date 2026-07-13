import streamlit as st

st.set_page_config(page_title="Metodología — Observatorio Arbitral", page_icon="📖", layout="wide")

st.title("Metodología")
st.caption(
    "Requisito duro del MVP (D37): esta página explica qué cuenta el observatorio, "
    "qué no, y sus límites conocidos — para que ninguna cifra se lea fuera de contexto."
)

st.header("Principio de rigor")
st.markdown(
    """
El Observatorio Arbitral **cuenta hechos objetivamente verificables**, con metodología
transparente. **No evalúa si una decisión arbitral fue acertada o errónea**, ni alimenta
inferencias de sesgo entre árbitros o equipos. Cada métrica se define por lo que
*objetivamente ocurrió y consta en la fuente* — no por su corrección.

El criterio que decide qué entra: se incluye lo que consta de forma **completa y
consistente en todos los partidos**; se aparca lo que depende de que "alguien lo reporte".
"""
)

st.header("Qué se mide")
st.markdown(
    """
- **Tarjetas** — amarilla, segunda amarilla, roja directa. Evento atómico, por jugador.
- **Penaltis señalados** — a favor / en contra, se transformen o no. No se registra el
  resultado del lanzamiento ni su origen (campo o VAR).
- **Faltas pitadas** — agregado por equipo y partido (no hay autor ni minuto individual).
- **Tiempo añadido anunciado** — agregado por mitad, tal y como lo anuncia el cuarto
  árbitro (no el añadido realmente jugado).
- **Decisiones VAR con impacto** — ver más abajo, sección propia.

**Explícitamente fuera de alcance:** cualquier juicio de acierto/error arbitral; faltas o
penaltis **no** señalados ("los que debió pitar" — es juicio, no hecho); tarjetas a
cuerpo técnico; comparación estadística entre árbitros o equipos.
"""
)

st.header("Cómo leer las cifras")
st.markdown(
    """
- **Tasa por partido** es la base de comparación (evento ÷ partidos dirigidos), no el
  total bruto — para que un árbitro con pocos partidos no se compare en desigualdad de
  condiciones con uno que ha dirigido toda la temporada. El total bruto y el
  **número de partidos dirigidos** (el denominador) están siempre visibles junto a la
  tasa, precisamente para que se pueda juzgar la fiabilidad de la cifra.
- **Mediana de liga**: se muestra **solo** en amarillas y faltas — las métricas de
  volumen, donde la muestra de una temporada la sostiene. En rojas directas y penaltis
  no se muestra ninguna referencia, para no fabricar una señal donde el número de casos
  es demasiado pequeño y una sola temporada es ruido.
"""
)

st.header("Módulo VAR — los tres puntos de rigor")
st.markdown(
    """
1. **Cuenta modificaciones, no el total de revisiones.** La métrica "decisiones VAR con
   impacto" son solo los casos en que el VAR **cambió** la decisión de campo. Las
   revisiones que **confirmaron** lo ya decidido en el campo se guardan y se muestran en
   la ficha del árbitro como contexto, pero no se ranquean.
2. **Se atribuye al árbitro principal, no al árbitro VAR.** El dato interno guarda ambos,
   pero la superficie pública de esta primera versión solo expone el corte por árbitro
   principal.
3. **No juzga acierto/error.** Que una decisión se "modificara" no implica que la
   decisión original fuera un error, ni que la revisada sea la correcta — solo que hubo
   un cambio.

**Límite conocido de la fuente:** los *checks* silenciosos de cabina (revisiones del VAR
que no derivan en una parada de juego ni en un anuncio) **no están en el feed de
LaLiga.com** y, por tanto, no están en el dato. No se intenta reconstruir ni inferir su
número.
"""
)

st.header("Fuente y cobertura")
st.markdown(
    """
- **Fuente primaria:** LaLiga.com (oficial, rastreable), vía el JSON embebido en cada
  ficha de partido.
- **Temporada cubierta:** 2025-26, temporada completa (380 partidos).
- **Limitación conocida:** en **15 de los 380 partidos** (~4%), la fuente no expone la
  designación arbitral (el campo llega vacío). Esos partidos quedan fuera del ranking y
  de las fichas — no se les asigna un árbitro por aproximación ni se completa a mano,
  siguiendo el principio de marcar y no sobrescribir ante una discrepancia o un hueco de
  la fuente.
"""
)
