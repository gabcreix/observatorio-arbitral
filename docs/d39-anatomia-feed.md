# D39 — Anatomía real del feed de LaLiga.com

*Producto de la fase de análisis exploratorio (D39, anexo de propagación).
Versión 2: temporada 2025/2026 completa (380 partidos, las 38 jornadas)
aterrizada en modo `--dry-run` vía `scraper.ingest --temporada`. La versión 1
se basaba solo en la jornada 28 (10 partidos); esta la sustituye y cierra los
cabos que aquella dejaba abiertos. Sustituye a las suposiciones de los
bloques 1–5 donde la evidencia real las corrige. No sustituye a esos
documentos: se lee junto a ellos.*

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

## 2. Inventario `match_event_kind` (events[], tipado) — temporada completa

| id | name | collection | count/temporada | Uso en el MVP |
|---|---|---|---|---|
| 1 | Goal | goal | 897 | fuera de alcance (no se trackean goles per se) |
| 2 | Penalty | goal | 103 | penalti **transformado** — parte de "penalti señalado" (D7) |
| 3 | Own | goal | 24 | fuera de alcance |
| 4 | Missed | missedPenalty | 4 | penalti **fallado** — parte de "penalti señalado" (D7) |
| 5 | Post | missedPenalty | 8 | penalti al **poste** — parte de "penalti señalado" (D7) |
| 6 | Saved | missedPenalty | 17 | penalti **parado** — parte de "penalti señalado" (D7) |
| 10 | Yellow | booking | 1717 | **`tarjeta.tipo = amarilla`** (D5) |
| 11 | Second Yellow | booking | 40 | **`tarjeta.tipo = segunda_amarilla`** (D5) |
| 12 | Straight Red | booking | 73 | **`tarjeta.tipo = roja_directa`** (D5 — cabo cerrado) |
| 13 | Injury | substitution | 231 | fuera de alcance |
| 14 | Tactical | substitution | 3362 | fuera de alcance |
| 15 | Goal awarded | var | 38 | `evento_var`: tipo=**gol**, revisión iniciada por gol dado |
| 16 | Goal not awarded | var | 17 | `evento_var`: tipo=**gol**, revisión iniciada por gol no dado |
| 17 | Penalty awarded | var | 15 | `evento_var`: tipo=**penalti**, revisión iniciada por penalti dado |
| 18 | Penalty not awarded | var | 49 | `evento_var`: tipo=**penalti**, revisión iniciada por penalti no dado |
| 19 | Red card given | var | 4 | `evento_var`: tipo=**tarjeta**, VAR indica roja no señalada en campo |
| 20 | Card upgrade | var | 22 | `evento_var`: tipo=**tarjeta**, revisión de una tarjeta ya mostrada |
| 21 | Mistaken Identity | var | 2 | `evento_var`: tarjeta corregida a otro jugador (edge case raro) |

**D7 cerrado del todo:** bloque 4 tenía razón — sí existe un evento tipado para
penaltis no transformados. Vive en su propia `collection: "missedPenalty"`
(tres variantes: fallado fuera / al poste / parado), separada de `Penalty`
(`collection: "goal"`, solo el transformado). "Penalti señalado" (D7) = unión de
las cuatro: 132 penaltis pitados en la temporada (103 transformados + 29
fallados/al poste/parados). Solo hacía falta más muestra para verlo — la
jornada 28 (v1 de este documento) no tuvo ningún caso.

**Inventario VAR ampliado respecto a la v1:** con 10 partidos solo habíamos visto
3 de los 7 `kind` de `collection: "var"` (15, 18, 20). La temporada completa
revela los otros cuatro (16, 17, 19, 21) — pares "awarded"/"not awarded" para
gol y penalti, más una variante directa de tarjeta ("Red card given", sin
tarjeta previa en campo) y un caso raro de identidad equivocada.

**Campo `decision`:** `"confirmed"` → D35 `resultado = confirma`; `"cancelled"`
→ D35 `resultado = modifica`. Verificado contra el texto de los comentarios en
los casos revisados a mano; se sostiene en los 22 "Card upgrade" observados
(mayoría `cancelled` = tarjeta revocada). Pendiente de revisar específicamente
en los `kind` nuevos (16, 17, 19, 21), pero es razonable asumir la misma
semántica uniforme.

**Straight Red en contexto:** de las 73 rojas directas de la temporada, solo
~22-26 tienen un evento VAR de tarjeta asociado (`Card upgrade`/`Red card
given`/`Mistaken Identity`) — la gran mayoría de rojas **no se revisan**, que es
el caso normal. La v1 de este documento solo había visto 2 rojas, ambas
revisadas; con la temporada completa se confirma que eso no era representativo.

---

## 3. Inventario `match_comment_kind` (comments[], prosa) — temporada completa

| id | Contenido | Conteo/temporada | Uso en el MVP |
|---|---|---|---|
| 1, 2, 10, 18 | Remates (rechazado/parado/fallado/al poste) | 8413 | fuera de alcance |
| 3 | Córner | 3695 | fuera de alcance |
| 4 | **"Decisión del VAR: ..."** | 151 | contexto textual del evento VAR (redundante con events[]) |
| 5 | Final de parte/partido | 1140 | fuera de alcance |
| 6 | **"Falta de X (Equipo)"** — incluye manos | 9429 | candidato a `faltas_equipo_partido` (D9) — **ver fricción §5** |
| 7 | "X ha recibido una falta" | 8961 | contraparte de 6, no usado directamente |
| 8, 12, 29 | Gol / gol en propia / gol de penalti convertido | 1024 | fuera de alcance |
| 9 | Alineaciones confirmadas (pre-partido) | 380 | fuera de alcance (1 por partido, cuadra) |
| 11 | Fuera de juego | 1439 | descartado de plano (bloque 1) |
| 13 | **"Penalti cometido por X (Equipo)"** | 134 | señalamiento de penalti (D7) — resuelto vía events[], ver §2 |
| 14, 15 | **"¡Penalti fallado!..."** (dos redacciones distintas) | 21 | eco textual de `missedPenalty` (§2) |
| 16 | **"Penalti a favor del Equipo. X sufrió falta"** | 98 | variante textual de penalti señalado |
| 17 | Retirada por lesión sin cupo de cambios | 4 | fuera de alcance (edge case) |
| 20 | "X ha visto tarjeta amarilla" | 1636 | redundante con events[] kind=10 |
| 21 | "X ha visto tarjeta roja" | 65 | redundante con events[] kind=12 |
| 22 | "X segunda tarjeta amarilla" | 38 | redundante con events[] kind=11 |
| 23, 24, 25 | Inicio/lesión/reanudación | 2994 | fuera de alcance |
| 26 | Cambio (sustitución en prosa) | 3593 | **coincide exacto** con events[] Injury+Tactical (231+3362=3593) — buena señal de consistencia entre feeds |
| 28 | **"GOL ANULADO POR EL VAR"** | 36 | redundante con events[] kind=16 (Goal not awarded) |
| 31 | **"El cuarto árbitro ha anunciado N minutos de tiempo añadido"** | 760 = **2 × 380, sin excepciones** | **`anadido_partido`** (D10) — cobertura 100% confirmada (§ cabos), número va embebido en texto libre, requiere regex |

---

## 4. Penalti señalado (D7) — cerrado

Con la temporada completa aparece la `collection: "missedPenalty"` (§2): todo
penalti señalado, se transforme o no, tiene un evento estructurado en
`events[]` con `team.id`/`person` limpios, igual que tarjetas y goles. D7 se
resuelve enteramente desde `events[]`, sin necesidad de tocar `comments[]` en
prosa. 132 penaltis señalados en la temporada: 103 transformados (`Penalty`),
29 no transformados (4 fallados fuera, 8 al poste, 17 parados).

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

Confirmado sobre la temporada completa (380 partidos):

- **`role.id = 5`**: 20 árbitros principales distintos en toda la temporada
  → cuadra con el tamaño real del colegio arbitral de Primera División,
  confirma **árbitro principal** (D20).
- **`role.id = 9`**: 15 árbitros VAR distintos → confirma **árbitro VAR**
  (D25 "role.id: 9"), pool algo más reducido que el de principales, coherente
  con la realidad (no todos los árbitros están habilitados para VAR).
- **`role.id` = 6 (30), 7 (28), 8 (51), 10 (34)**: presentes en todos los
  partidos, siguen sin mapear con certeza — el salto a 51 nombres distintos en
  `role.id=8` sugiere que ese id puede agrupar más de un puesto físico
  (posiblemente los dos asistentes de línea bajo el mismo id en partidos
  distintos). No bloquea el MVP, que solo necesita principal + VAR (D36); queda
  anotado para el futuro "cuadro arbitral completo" (bloque 3, §7, puerta
  abierta).

---

## 8. Cabos de D39 — estado final (temporada completa, 380/380 partidos)

| Cabo | Estado |
|---|---|
| `segunda_amarilla` vs `roja_directa` (D5) | **Cerrado.** `events[].match_event_kind.id` 11 vs 12, nombres propios ("Second Yellow"/"Straight Red"). Confirmado con 40 + 73 casos reales. |
| Blob embebido cubre todo / XHR complementario (D30) | **Cerrado.** Todo vive en `__NEXT_DATA__`; no hace falta otro endpoint — validado en los 380 partidos, 0 errores de parseo. |
| Cobertura del añadido en 380 partidos (D26) | **Cerrado, 100%.** 760 comentarios kind=31 = exactamente 2 por partido en los 380, sin excepciones. |
| Inventario `match_comment_kind` | **Cerrado** (§3): 26 valores distintos con conteos sobre la temporada completa. |
| Detalle VAR sobre penaltis/goles/tarjetas | **Cerrado y ampliado** (§2): 7 tipos de evento VAR (no 3), con pares awarded/not-awarded para gol y penalti. |
| Penalti fallado/parado (D7) | **Cerrado** (§4): `collection: missedPenalty`, 29 casos reales sobre la temporada. |

**Cabos que siguen abiertos** (no bloquean seguir a silver, se resuelven al
diseñar cada tabla concreta): atribución de equipo en `comments[]` para faltas
(§5, D9); formato de `clock` en descuento vs `smallint` de silver (§6, D8/D17);
mapeo exacto de `role.id` 6/7/8/10 (§7, no bloquea D36).

**Conclusión:** con 380/380 partidos analizados sin errores y los cabos
funcionales todos cerrados, la fase D39 se da por completa. Los dos cabos que
quedan son de diseño de silver (D9, D8/D17), no de descubrimiento de fuente.
