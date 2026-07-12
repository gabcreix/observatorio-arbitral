# Observatorio Arbitral de LaLiga — Bloque 1: Diseño funcional (v2 — con módulo VAR)

*Documento de síntesis autocontenido. Recoge las decisiones D1–D10 originales del diseño funcional del MVP y el **miniciclo VAR (D35–D38)** que reabre D4 y lo trae al MVP. Es la referencia de "qué se mide y qué queda fuera" sobre la que se construyeron los bloques 2 (casos de uso), 3 (modelo de datos), 4 (fuentes/validación) y 5 (arquitectura técnica). Sustituye a la versión previa del bloque 1.*

---

## 1. Propósito y principio de rigor

El Observatorio Arbitral es una base de datos estructurada y consultable sobre la actuación arbitral en Primera División. Sirve datos arbitrales limpios y analizables que hoy viven dispersos en actas y estadísticas de partido.

**Principio innegociable:** el proyecto cuenta hechos verificables con metodología transparente. No evalúa aciertos ni errores, ni alimenta inferencias de sesgo. Cada métrica se define por lo que *objetivamente ocurrió y consta en la fuente*, no por su corrección.

**Comunicación de "lo que NO se puede concluir".** En la versión original del bloque 1, este principio vivía como **disciplina interna de diseño**. Con la incorporación del módulo VAR (D35, ver §5), asciende a **característica visible del producto** (D37): la métrica VAR obliga a etiquetas contextuales en el punto de consulta y a una página de metodología pública como pieza dura del MVP.

**Criterio-guía transversal — homogeneidad de la fuente.** La regla que decide si una métrica entra al núcleo o se aparca es una sola: se incluye lo que consta de forma **completa y consistente en todos los partidos**; se aparca lo que depende de que "alguien lo reporte". Este criterio explica todas las inclusiones y exclusiones del MVP. La reapertura de D4 (VAR) es la aplicación estricta de este criterio: se aparcó cuando la fuente parecía irregular; se reincorporó cuando el bloque 4 verificó que LaLiga.com expone eventos VAR de forma tipada y homogénea.

---

## 2. Alcance del MVP

### Qué entra
- **Competición:** solo Primera División.
- **Ventana temporal:** una temporada completa, con relleno retrospectivo (masa útil desde el lanzamiento).
- **Unidad de análisis primaria:** el árbitro **principal** (§3).
- **Dimensiones descriptivas integradas desde el día uno:** equipo y tiempo (jornada/minuto).
- **Métricas** (§4):
  - Tarjetas — evento **atómico**.
  - Penaltis señalados — evento **atómico**.
  - Faltas pitadas — métrica **agregada** por equipo y partido.
  - Tiempo añadido anunciado — métrica **agregada** por mitad y partido. *(D10 confirmada dentro tras verificación en bloque 4.)*
  - **Eventos VAR de veredicto — evento atómico**, con distinción `modifica` / `confirma`. *(D35, ver §5.)*

### Qué queda explícitamente fuera del MVP
- Cualquier juicio de acierto/error arbitral.
- Tarjetas a cuerpo técnico y oficiales de banquillo.
- Resultado del lanzamiento del penalti y origen del penalti (campo vs. VAR).
- Detección de desviaciones estadísticas entre árbitros o equipos.
- Faltas a grano atómico (evento a evento).
- **Perfilador del árbitro VAR** (el evento se atribuye también al VAR en el modelo — D36 —, pero la vista se aplaza).

### Descartado de plano (no solo aparcado)
- **Faltas o penaltis NO señalados** ("los que debió pitar"): rompen el principio de rigor de raíz; son juicio, no hecho.
- **Tiempo efectivo de juego / balón en juego** y **fueras de juego**: fuera de foco o de fuente pobre.

---

## 3. Unidad de análisis y pregunta-estrella

**Pregunta-estrella:** *"¿Qué tarjetas, penaltis, faltas y decisiones VAR con impacto acumula el árbitro X, desglosado por equipo y por jornada?"*

El observatorio es, en su MVP, un **perfilador de árbitros principales**. La unidad de análisis es el árbitro principal; equipo y tiempo son dimensiones descriptivas que cuelgan de cada evento o métrica. **El módulo VAR mantiene esta unidad** (D36): el evento VAR se guarda con doble atribución (principal + VAR) en el modelo, pero la superficie del MVP expone solo el corte por principal.

Consecuencia de diseño: la vista "trato por equipo" se obtiene de forma **descriptiva** agregando por equipo, sin construir un analizador de sesgo. La comparación estadística entre árbitros/equipos (con líneas base y control de confusores) queda aparcada como módulo futuro.

---

## 4. Métricas capturadas — definiciones operativas

El MVP maneja **dos granos** de dato:

- **Eventos atómicos:** un incidente por fila (actor, equipo, minuto, tipo). → tarjetas, penaltis, **eventos VAR**.
- **Métricas agregadas por partido-equipo:** un número por partido y unidad, sin incidente individual. → faltas, tiempo añadido.

### 4.1 Tarjeta *(atómica)*

- **Evento =** sanción disciplinaria mostrada por el árbitro a un jugador (registro por *sanción*, no por cartón físico anónimo).
- **Tipos (enumerado cerrado):** `amarilla`, `segunda_amarilla`, `roja_directa`.
- **Doble amarilla:** dos filas — `amarilla` + `segunda_amarilla`.
- **Expulsión:** estado derivado en gold (jugador con `segunda_amarilla` o `roja_directa`).
- **Receptor:** solo **jugadores** (titulares y suplentes).
- **Atribución a equipo:** vía la afiliación del jugador (jugador → equipo).
- **Amonestaciones totales** = `amarilla` + `segunda_amarilla`.
- **Minuto:** se almacena siempre.

### 4.2 Penalti *(atómico)*

- **Evento =** señalamiento de penalti por el árbitro.
- **Atributos:** equipo a favor (lanza), equipo en contra (comete), minuto.
- **No se captura:** resultado del lanzamiento ni origen (campo/VAR). Aparcados.

### 4.3 Faltas pitadas *(agregada por equipo y partido)*

- **Métrica =** nº de faltas señaladas **contra cada equipo** en el partido.
- **Grano:** por partido y por equipo. Sin minuto ni autor.
- **Fuente:** panel agregado de LaLiga.com.

### 4.4 Tiempo añadido anunciado *(agregada por mitad)*

- **Métrica =** minutos de añadido **anunciados** en cada mitad (1ª y 2ª), por partido.
- **Grano:** por partido y por mitad.
- **No se captura:** el añadido realmente jugado.
- **Estado:** **dentro del MVP**, confirmado en bloque 4 (LaLiga.com lo expone como evento tipado por mitad).

### 4.5 Evento VAR de veredicto *(atómico — NUEVA)*

- **Evento =** decisión estructurada del VAR sobre una situación de campo (`match_comment_kind` 4 y 28 del feed).
- **Atributos capturados:**
  - Árbitro principal del partido y árbitro VAR designado (**doble atribución**, D36).
  - Minuto.
  - **Tipo de decisión revisada** (enum): `gol`, `tarjeta`, `penalti`.
  - **Resultado** (enum): `modifica` (la decisión de campo se cambió) o `confirma` (la decisión de campo se ratificó).
- **NO se registra:**
  - El evento kind 24 "juego detenido... VAR" (redundante con el veredicto).
  - Los **checks silenciosos** — no están en el feed. Este límite es parte de la comunicación visible del producto (D37).
- **Métrica visible en el ranking:** *"decisiones VAR con impacto"* = filas con `resultado = modifica`. Las que confirman viven en la ficha del árbitro como contexto de segundo nivel, no ranqueadas.
- **Atribución a árbitro principal** en el MVP; el corte por árbitro VAR queda preparado en el dato para un módulo post-MVP.

---

## 5. Miniciclo VAR — decisiones D35–D38

### D4 (reabierta)
La decisión original (VAR fuera del MVP, fuente irregular) queda **superada** por la verificación en bloque 4: el feed de LaLiga.com expone eventos VAR de forma **tipada y homogénea** — invalidando la premisa de irregularidad que motivó el aparcamiento. La reapertura se hizo con dos partidos analizados (Rayo-Real Sociedad y Atlético-Barcelona) confirmando cinco eventos VAR estructurados que cubren goles anulados, revocaciones de tarjeta y confirmaciones tras revisión.

### D35 — Alcance del módulo VAR
Se registran **todas las decisiones VAR de veredicto** (kind 4 + 28) con campo `resultado = {modifica, confirma}`. **La métrica visible en el ranking es solo `modifica`** ("decisiones VAR con impacto"). Las confirmaciones se guardan y viven en la ficha como contexto de segundo nivel, no ranqueadas. Se acepta explícitamente que los *checks silenciosos* no están en el feed y por tanto no están en el dato — la comunicación de este límite es parte de D37.

### D36 — Unidad arbitral del evento VAR
**Doble atribución en el modelo, superficie única en el MVP.** El evento se guarda con ambos árbitros (principal y VAR); el MVP expone solo el corte por árbitro principal (coherente con D2/D11). El corte por árbitro VAR queda preparado en el dato como puerta abierta.

### D37 — Comunicación de límites (característica visible)
**Página de metodología prominente + etiqueta contextual en el ranking VAR.** La página explica los tres puntos de rigor (cuenta modificaciones no revisiones totales; atribución al principal; no juzga acierto/error); el ranking VAR lleva una etiqueta contextual breve con enlace a la explicación completa. **Consecuencia:** la página de metodología pasa a ser requisito duro del MVP, no pieza opcional.

### D38 — Ubicación del módulo VAR
- **Modelo:** tabla nueva `evento_var` en silver (patrón D17).
- **UI:** métrica en el ranking (columna adicional en P1) + sección VAR en la ficha del árbitro (P2). Sin abrir puerta nueva de exploración; disciplina de espina única de D11 preservada.

---

## 6. Convención de conteo temporal

- Aplica a los **eventos atómicos** (tarjetas, penaltis, eventos VAR): se cuentan **todos** los que consten en la fuente, **con independencia del minuto**.
- El **minuto se almacena siempre**.
- Las métricas agregadas (faltas, añadido) no tienen minuto por definición de su grano.

---

## 7. Módulos futuros aparcados (puerta abierta en el modelo)

| Módulo aparcado | Qué añadiría | Motivo de aplazamiento |
|---|---|---|
| **Detector de desviaciones** | Comparación estadística entre árbitros/equipos | Requiere líneas base y control de confusores; roza el juicio |
| **Perfilador de árbitros VAR** | Ranking y ficha del árbitro de cabina | D36 preparó el dato; se aplaza la superficie por disciplina de espina única |
| **Tarjetas a oficiales** | Amonestaciones a cuerpo técnico/banquillo | Bifurca la atribución; masa fina; riesgo de cobertura |
| **Resultado del penalti** | Transformado / fallado / repetido | Mide al lanzador, no al árbitro |
| **Origen del penalti** | Campo vs. VAR | Es detalle-VAR; encaja mejor con el módulo VAR extendido |
| **Faltas atómicas** | Cada falta con minuto y autor | Play-by-play: fuente heterogénea; sobrealcance de ingesta |
| **Explorador árbitro×equipo** | Cruce en brutos con nº de enfrentamientos visible **y balance V-E-D** | Sobre 1-2 partidos por temporada, muestras finas; V-E-D introduce narrativa resultado↔árbitro que se comunica mejor en un módulo dedicado que como columna del MVP |
| **Vista de evolución temporal** | Serie temporal por árbitro | Sobre una temporada, eventos raros son ruidosos |

*Nota:* el módulo VAR ha salido de esta tabla y pasa al núcleo del MVP.

---

## 8. Registro de decisiones (D1–D10 + miniciclo VAR)

- **D1 — Alcance de medición.** Solo eventos objetivamente verificables. No juzga acierto/error.
- **D2 — Pregunta-estrella y unidad de análisis.** Perfilador de árbitros principales; equipo y tiempo como dimensiones desde el día uno.
- **D3 — Alcance temporal.** Una temporada completa con relleno retrospectivo.
- **D4 — Estatus del VAR.** *Reabierta.* La versión original (VAR fuera del MVP) queda superada por el miniciclo D35–D38.
- **D5 — Tipología de la tarjeta.** Tres tipos: `amarilla`, `segunda_amarilla`, `roja_directa`. Expulsión derivada.
- **D6 — Receptor de tarjeta.** Solo jugadores.
- **D7 — Definición de penalti.** Señalamiento atómico: a favor / en contra / minuto.
- **D8 — Conteo temporal y minuto.** Todo evento del feed, sin filtro; minuto almacenado siempre.
- **D9 — Faltas pitadas.** Agregada por equipo y partido. Introduce el carril agregado.
- **D10 — Tiempo añadido.** Agregada por mitad, **dentro del MVP** (verificado en bloque 4).
- **D35 — Alcance VAR.** Decisiones de veredicto (kind 4 + 28) con `modifica` / `confirma`; ranking solo con `modifica`.
- **D36 — Unidad arbitral del VAR.** Doble atribución en el modelo; superficie única (principal) en el MVP.
- **D37 — Comunicación de límites.** Característica visible: metodología + etiqueta contextual en el ranking VAR.
- **D38 — Ubicación del módulo VAR.** Tabla `evento_var` en silver; ranking (columna) + sección en ficha en la UI.

---

*Fin del bloque 1 v2. El siguiente documento (anexo de propagación) recoge los cambios que este miniciclo introduce en los bloques 2, 3, 4 y 5, más D39.*
