# D39 — Anatomía real del feed de LaLiga.com

*Producto de la fase de análisis exploratorio (D39, anexo de propagación). Basado en
la jornada 28 completa (10 partidos, temporada 2025/2026) aterrizada en modo
`--dry-run`. Sustituye a las suposiciones de los bloques 1–5 donde la evidencia real
las corrige. No sustituye a esos documentos: se lee junto a ellos.*

---

## 0. Descubrimiento de partidos (hueco fuera de D1–D39, resuelto en implementación)

Ninguna decisión de diseño cubría cómo averiguar **qué partidos existen** para
una jornada — D30 solo resuelve cómo leer una página de partido ya conocida.
Confirmado a mano: la página de resultados de LaLiga.com sigue la misma
técnica ya decidida (HTTP + `__NEXT_DATA__`), solo que en otra página:

```
https://www.laliga.com/laliga-easports/resultados/{season}/jornada-{week}
  → pageProps.matches[]        # slug, status, equipos — un slug por partido
  → pageProps.gameweekList[]   # las 38 jornadas de la temporada (id, week, date)
```

El `slug` de cada partido en `matches[]` es exactamente el mismo que arma la
URL de detalle (`https://www.laliga.com/partido/{slug}`), y `status` distingue
partidos ya jugados (`FullTime`) de los pendientes. Esto habilita el backfill
"troceable por jornadas" que pedía D32 sin curación manual: implementado en
`scraper/discover.py` (`discover_jornada`) y enganchado en
`scraper/ingest.py --jornada N`.

---

## 1. Dónde vive todo

El JSON completo está en `<script id="__NEXT_DATA__" type="application/json">` →
`props.pageProps`. D30 queda resuelto: **no hace falta ningún endpoint XHR
complementario**, todo lo necesario para el MVP está en este único blob.

```
pageProps
├── match            # dimensión partido + designación arbitral
│   ├── id, name, slug, date, status, gameweek.week (= jornada), venue, season
│   ├── home_team / away_team   { id, slug, name, opta_id }   ← IDs canónicos (D25)
│   └── persons_role[]          { person: {name}, role: {id} }  ← cuadro arbitral (D20)
├── events[]          # feed TIPADO (Opta puro): goles, tarjetas, sustituciones, VAR
│   └── { match_event_kind: {id, name, collection}, lineup: {team, person},
│         time, minute, second, clock, period, decision? }
└── data
    ├── comments[]    # feed en PROSA español: faltas, penaltis, añadido, VAR (texto)
    │   └── { match_comment_kind: {id}, content, time, period }   ← SIN team/person estructurado
    ├── stats.{home,away}   # ~150 métricas Opta agregadas (no hay campo "fouls" limpio)
    └── lineups            # alineaciones completas
```

**Hallazgo clave:** hay dos feeds paralelos, no uno. `events[]` trae atribución
limpia (`team.id`, `person`) pero solo cubre goles/tarjetas/sustituciones/VAR.
`comments[]` cubre más cosas (faltas, penaltis señalados, añadido) pero **no tiene
campo de equipo o jugador estructurado** — solo texto libre en español.

---

## 2. Inventario `match_event_kind` (events[], tipado)

| id | name | collection | Uso en el MVP |
|---|---|---|---|
| 1 | Goal | goal | fuera de alcance (no se trackean goles per se) |
| 2 | Penalty | goal | **solo penalti transformado** (ver §4 — no cubre fallados) |
| 3 | Own | goal | fuera de alcance |
| 10 | Yellow | booking | **`tarjeta.tipo = amarilla`** (D5) |
| 11 | Second Yellow | booking | **`tarjeta.tipo = segunda_amarilla`** (D5) |
| 12 | Straight Red | booking | **`tarjeta.tipo = roja_directa`** (D5 — cabo cerrado) |
| 13 | Injury | substitution | fuera de alcance |
| 14 | Tactical | substitution | fuera de alcance |
| 15 | Goal awarded | var | **`evento_var.tipo_decision_revisada = gol`** |
| 18 | Penalty not awarded | var | **`evento_var.tipo_decision_revisada = penalti`** |
| 20 | Card upgrade | var | **`evento_var.tipo_decision_revisada = tarjeta`** |

**Campo `decision` en eventos VAR:** `"confirmed"` → D35 `resultado = confirma`;
`"cancelled"` → D35 `resultado = modifica`. Verificado contra el texto de los
comentarios en los 5 casos VAR de esta muestra (2 rojas revocadas, 1 penalti
concedido tras revisión, 1 gol anulado, 1 gol confirmado). Consistente en los tres
`kind` (15/18/20): `decision` siempre describe si la decisión *original* (la que
nombra el `kind`) quedó cancelada o confirmada — no si "hubo VAR a favor/en contra".

**No observado todavía:** `Straight Red` que NO sea revocada por VAR (las 2 rojas de
esta muestra acabaron anuladas); un `Penalty` fallado o parado (bloque 4 asumía que
"incluye fallados", pero esta muestra no tuvo ninguno — ver §4).

---

## 3. Inventario `match_comment_kind` (comments[], prosa)

| id | Contenido | Conteo (10 partidos) | Uso en el MVP |
|---|---|---|---|
| 1, 2, 10, 18 | Remates (rechazado/parado/fallado/al poste) | 246 | fuera de alcance |
| 3 | Córner | 96 | fuera de alcance |
| 4 | **"Decisión del VAR: ..."** | 5 | contexto textual del evento VAR (redundante con events[]) |
| 5 | Final de parte/partido | 30 | fuera de alcance |
| 6 | **"Falta de X (Equipo)"** — incluye manos | 249 | candidato a `faltas_equipo_partido` (D9) — **ver fricción §5** |
| 7 | "X ha recibido una falta" | 238 | contraparte de 6, no usado directamente |
| 8, 12, 29 | Gol / gol en propia / gol de penalti convertido | 30 | fuera de alcance |
| 9 | Alineaciones confirmadas (pre-partido) | 10 | fuera de alcance |
| 11 | Fuera de juego | 44 | descartado de plano (bloque 1) |
| 13 | **"Penalti cometido por X (Equipo)"** | 3 | señalamiento de penalti (D7) — ver §4 |
| 16 | **"Penalti a favor del Equipo. X sufrió falta"** | 1 | variante textual de penalti señalado |
| 20 | "X ha visto tarjeta amarilla" | 44 | redundante con events[] kind=10 |
| 21 | "X ha visto tarjeta roja" | 2 | redundante con events[] kind=12 |
| 22 | "X segunda tarjeta amarilla" | 1 | redundante con events[] kind=11 |
| 23, 24, 25 | Inicio/lesión/reanudación | 66 | fuera de alcance |
| 26 | Cambio (sustitución en prosa) | 99 | fuera de alcance |
| 28 | **"GOL ANULADO POR EL VAR"** | 1 | redundante con events[] kind=15 decision=cancelled |
| 31 | **"El cuarto árbitro ha anunciado N minutos de tiempo añadido"** | 20 (2/partido, 10/10 partidos) | **`anadido_partido`** (D10) — número va embebido en texto libre, requiere regex |

---

## 4. Penalti señalado (D7) — cabo parcialmente abierto

El único rastro estructurado de un penalti es `events[].kind=2 "Penalty"`
(`collection: "goal"`), y **solo aparece cuando se transforma** (es un evento de
gol). Un penalti fallado o parado **no genera este evento** — su única huella en
esta muestra sería el par de comentarios en prosa (kind=13 "Penalti cometido por
X" / kind=16 "Penalti a favor de Y"), sin equipo ni jugador estructurados.

Bloque 4 asumía que el timeline de LaLiga.com trae "penaltis señalados con
resultado (incluidos fallados)" como evento tipado. **Esta muestra no lo
contradice ni lo confirma** — simplemente no hubo ningún penalti fallado/parado
en estos 10 partidos para comprobarlo. Sigue siendo un cabo abierto: hace falta
un partido con un penalti fallado o parado para saber si existe un
`match_event_kind` propio (p. ej. "Penalty missed") o si hay que resolver D7
enteramente desde `comments[]` en prosa.

---

## 5. Fricción con D9 (faltas agregadas por equipo)

Bloque 4 asumía un "panel agregado" limpio con el número de faltas por equipo.
La evidencia real ofrece dos candidatos, ninguno limpio:

- **`stats.{home,away}.fk_foul_lost` / `fk_foul_won`**: no cuadran exactamente
  entre equipos rivales de un mismo partido (ej. 10 vs 9, 13 vs 12) — sugiere que
  no son un espejo perfecto de "faltas cometidas por A" vs "faltas sufridas por B".
- **`comments[]` kind=6** ("Falta de X (Equipo)"): conteo atómico correcto en
  espíritu (una fila por falta señalada), pero **sin campo de equipo
  estructurado** — el nombre del club va en texto libre entre paréntesis, en su
  forma corta de display ("Villarreal", no "Villarreal Club de Fútbol SAD"), y
  habría que resolverlo contra `nombre_canonico` de la tabla `equipo` con un
  parser de texto en español, no con un `team.id` limpio como en `events[]`.

**No lo decido yo:** cuando toque diseñar el modelo dbt de silver para
`faltas_equipo_partido`, hay que elegir entre estas dos fuentes imperfectas (o
aceptar el parseo de texto). Lo señalo aquí para esa conversación.

---

## 6. Fricción con D8/D17 (minuto como `smallint`)

Los eventos de `events[]` traen cuatro campos de tiempo: `time`, `minute`,
`second`, `clock`, `period`. En tiempo de descuento, `clock` toma forma de texto
compuesto (`"90+4"`, `"45+2"`), incompatible con un `smallint` puro tal y como lo
define bloque 3. `comments[]`, en cambio, **solo trae `time` + `period`**, sin
`second` ni `clock` — su granularidad de minuto es más pobre, lo cual afecta
justo a los eventos VAR que solo tienen huella en comentarios más allá del atajo
de `events[]` `collection: var` (§2).

Recomendación a validar cuando se diseñe silver: usar `minute` (entero, sin
descuento) como base del `smallint minuto`, y considerar una columna adicional
(`es_tiempo_anadido` bool, o `minuto_anadido` smallint nullable) si se quiere
preservar la distinción "min 90 normal" vs "min 90 de descuento". No decidido
todavía.

---

## 7. Cuadro arbitral (D20/D25) — `persons_role`

Confirmado en las 10 muestras:

- **`role.id = 5`**: 10 nombres distintos en 10 partidos (biyectivo) → **árbitro
  principal**, consistente con D20.
- **`role.id = 9`**: 8 nombres distintos en 10 partidos → **árbitro VAR**
  (confirma literalmente el cabo D25 "el feed lo expone con `role.id: 9`").
- **`role.id` = 6, 7, 8, 10**: presentes en todos los partidos, pendientes de
  mapear con certeza (candidatos: asistentes de línea, cuarto árbitro, AVAR) —
  no bloquea el MVP, que solo necesita principal + VAR (D36).

---

## 8. Cabos de D39 — estado

| Cabo | Estado |
|---|---|
| `segunda_amarilla` vs `roja_directa` (D5) | **Cerrado.** `events[].match_event_kind.id` 11 vs 12, nombres propios ("Second Yellow"/"Straight Red"). |
| Blob embebido cubre todo / XHR complementario (D30) | **Cerrado.** Todo vive en `__NEXT_DATA__`; no hace falta otro endpoint. |
| Cobertura del añadido en 380 partidos (D26) | **Fuerte señal positiva** (10/10 partidos, 2 comentarios kind=31 cada uno) — falta extender el chequeo a la temporada completa. |
| Inventario `match_comment_kind` | **Hecho** (§3), 25 valores distintos vistos con ejemplos y conteos. |
| Detalle VAR kind 4/28 sobre penaltis | **Cerrado y mejorado** — el caso Barcelona-Sevilla (Cancelo) muestra un penalti concedido tras revisión VAR, y se descubrió que `events[]` tiene una fuente estructurada mejor que la prosa (§2). |

**Nuevos cabos abiertos por este análisis** (no estaban en la lista original):
penalti fallado/parado sin ver todavía (§4); atribución de equipo en `comments[]`
para faltas (§5); formato de `clock` en descuento vs `smallint` de silver (§6).
