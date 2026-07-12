# Observatorio Arbitral de LaLiga — Bloque 4: Fuentes y estrategia de validación

*Documento de síntesis autocontenido. Recoge las decisiones D24–D26 y resuelve la dependencia viva de D10. Cierra las tres misiones del bloque: verificar el criterio de homogeneidad de fuente, resolver el añadido (D10) y definir la reconciliación de entidades. Nivel: tipo de fuente y estrategia, no scraping concreto.*

---

## 1. Panorama de fuentes (verificado)

Se estudiaron tres tipos de fuente. Resumen de lo confirmado sobre partidos reales:

### Acta arbitral oficial (RFEF)
- **Pública** y consultable en rfef.es; **histórico desde 2003**; publica también las **designaciones** arbitrales.
- **Contiene, limpio y parseable:** el **cuadro arbitral completo** (principal + asistentes + 4º + VAR/AVAR), y las **amonestaciones** en formato regular (equipo + minuto + dorsal + jugador + motivo). Marca los **goles de penalti** (`title="Gol de penalti"`).
- **No contiene:** faltas, tiempo añadido, ni el penalti como evento independiente (solo el penalti *transformado*, vía el gol; los fallados/parados no aparecen).
- **Fricción:** el detalle del acta vive en un endpoint heredado (Novanet) con **`robots.txt` restrictivo** → el acceso automatizado es un matiz ético/legal a resolver, distinto de que el dato sea público.
- **Pendiente de formato:** no se ha visto un acta con **expulsión**, así que falta confirmar cómo distingue `segunda_amarilla` de `roja_directa` (D5).

### LaLiga.com (fuente elegida como primaria)
- **Oficial y rastreable** (`robots: index,follow`), con **API subyacente** probable (JSON embebido de eventos).
- Ofrece **dos granos a la vez**:
  - **Panel de estadísticas (agregado, por equipo):** Faltas, Tarjetas amarillas, Tarjetas rojas y Penaltis `n(m)` (señalados / transformados) — listos para usar.
  - **Minuto a minuto tipado (atómico):** ~17 tipos de evento (Opta) con tipo + minuto + periodo + jugador + equipo: tarjetas con motivo, **penaltis señalados con resultado (incluidos fallados)**, **añadido anunciado por mitad**, goles, cambios, córners, fueras de juego, lesiones…
  - **Designación:** árbitro principal + cuadro en la ficha del partido.
- **Cubre todas las métricas del MVP**, incluido el añadido (D10) y la designación (D20).

### Portal estadístico tipo FBref (secundario opcional)
- Estructurado, con tarjetas, penaltis (PKatt), faltas agregadas y árbitro por partido; histórico por temporadas.
- Queda como **segundo cross-check opcional**, no en el pipeline principal.

**Descartado como fuente de añadido:** portales estructurados abiertos (el dato fino de tiempo es propietario — Opta/Mediacoach) y prosa periodística. LaLiga.com lo resuelve al exponerlo como evento tipado.

---

## 2. Reparto fuente ↔ métrica (resultado)

| Métrica | Fuente primaria | Cross-check |
|---|---|---|
| Tarjetas (D5) | LaLiga.com (panel + timeline) | **Acta RFEF** (verdad disciplinaria, D21) |
| Penaltis señalados (D7) | LaLiga.com (timeline, incl. fallados) | Panel LaLiga.com; FBref opcional |
| Faltas por equipo (D9) | LaLiga.com (panel agregado) | FBref opcional |
| Tiempo añadido por mitad (D10) | LaLiga.com (evento tipado) | — (chequeo de cobertura) |
| Designación (D20) | LaLiga.com (ficha) | Acta / designaciones RFEF |

**El esquema del bloque 3 sobrevive intacto a la elección de fuente:** el panel agregado cae en `faltas_equipo_partido`; el timeline atómico en `tarjetas` y `penaltis`; el añadido en `anadido_partido`; la designación en `partido.arbitro_principal_id`. La fuente encajó en el diseño, no al revés — que era el objetivo del principio "diseñar independiente de la fuente, validar después".

---

## 3. Resolución de la dependencia viva D10

**D10 — Tiempo añadido: DENTRO del MVP.** La condición establecida (fuente completa y estructurada por partido) queda **satisfecha**: LaLiga.com expone el añadido anunciado por mitad como evento tipado, en fuente oficial y rastreable. La tabla `anadido_partido` se mantiene. Único pendiente: **chequeo de cobertura** del añadido en los 380 partidos, que es tarea de validación (D26), no de diseño.

---

## 4. Registro de decisiones del bloque 4 (D24–D26)

- **D24 — Estrategia de autoridad de fuente.** **LaLiga.com** como fuente primaria única de todas las métricas del MVP (oficial, rastreable, cubre todo incluido el añadido); **acta RFEF** como cross-check disciplinario de tarjetas vía validación ligera, honrando D21. FBref queda como segundo cross-check opcional. Supera el marco previo acta-vs-portal.
- **D25 — Reconciliación de entidades.** IDs estables de LaLiga.com como identidad canónica de equipos y jugadores; nombres de árbitro como clave natural (conjunto ~20/temporada, verificable a mano). Cross-check del acta por **fecha + equipos** comparando **conteos de tarjetas por equipo** (agregado, sin emparejar jugador a jugador). Se captura el **ID de equipo de la RFEF** (escudos) como alias para el join partido↔acta.
- **D26 — Validación ligera.** Tres chequeos: (1) completitud (380 partidos + campos clave, incl. añadido), (2) rangos sanos, (3) cross-check de tarjetas contra el acta por partido agregado. Ante discrepancia: **marcar con flag y registrar, sin sobrescribir** (respeta D21 y la reproducibilidad; alimenta la página de metodología).

---

## 5. Cabos pendientes (no bloquean el diseño)

- **Formato de expulsión (D5):** confirmar, con un acta y/o un partido de LaLiga.com con expulsión, cómo se marca `segunda_amarilla` vs `roja_directa` (iconos tipados en LaLiga.com: `minute-yelow-card`, `minute-bad-penalti`…; existirá el de roja/doble). Afecta al parser, no al modelo.
- **Vía de ingesta LaLiga.com:** localizar el endpoint de API (JSON) en lugar de scrapear el HTML renderizado.
- **Cobertura:** verificar en los 380 partidos (y en el relleno retrospectivo de D3) que panel + timeline + añadido vienen sin huecos. Es el chequeo (1) de D26.
- **Acceso al acta:** resolver la vía limpia al acta (¿exportación a PDF que el HTML referencia?, ¿histórico?) dado el `robots.txt` del endpoint Novanet — parte del escaneo ético/legal ligero.

---

## 6. Estado global del diseño

Con el bloque 4 cerrado, los **cuatro bloques de diseño** están completos: diseño funcional (D1–D10), casos de uso (D11–D15), modelo de datos (D16–D23) y fuentes/validación (D24–D26). No quedan dependencias vivas de diseño; el añadido (D10) está resuelto. Lo que resta es **fase de implementación y verificación** (parser, ingesta vía API, chequeos de cobertura), no decisiones de diseño.

Piezas futuras identificadas a lo largo del proyecto y aún no abordadas (ninguna bloquea el MVP): pipeline de extracción y orquestación (backfill vs captura hacia adelante), página pública de metodología, escaneo ético/legal ligero, testing/observabilidad, y los módulos aparcados (VAR, detector de desviaciones, explorador árbitro×equipo, tarjetas a oficiales, evolución temporal, etc.).

---

*Fin del bloque 4 y del diseño del observatorio. Los cuatro documentos de síntesis, juntos, constituyen el documento de diseño completo, listo para implementación.*
