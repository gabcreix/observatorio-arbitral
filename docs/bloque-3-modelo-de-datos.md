# Observatorio Arbitral de LaLiga — Bloque 3: Modelo de datos

*Documento de síntesis autocontenido. Recoge las decisiones D16–D23 y el esquema completo en Supabase (PostgreSQL) con arquitectura medallón. Soporta las preguntas P1–P6 del bloque 2 (casos de uso) sin cerrar la puerta a los módulos futuros del bloque 1 (diseño funcional). Nivel: diseño de esquema (tablas, columnas, tipos, claves, relaciones), no implementación de código.*

---

## 1. Convenciones de partida

- **Arquitectura medallón estándar:** *bronze* = copia cruda literal de la fuente; *silver* = normalizado y tipado a nivel de evento; *gold* = agregados listos para consulta.
- **Estrategia de claves (D16 — surrogate PK + natural UNIQUE):** toda tabla de silver/gold lleva PK **surrogate** (opaca); las claves naturales se conservan como restricciones **UNIQUE** (garantizan unicidad, sirven de guarda de deduplicación y son la diana de la futura reconciliación de entidades). *Bronze queda exento*: guarda las claves que traiga el origen.
- **Dos granos de hecho** conviven bajo `partido`: eventos **atómicos** (tarjetas, penaltis) y métricas **agregadas** por partido (faltas por equipo, añadido por mitad).
- **Tipo de PK:** `bigint` de identidad por defecto (UUID es alternativa equivalente bajo D16).

---

## 2. Arquitectura medallón

| Capa | Contenido | Claves |
|---|---|---|
| **Bronze** | Copia literal de cada fuente (payload HTML/JSON verbatim) + metadatos de procedencia (fuente, URL, `fetched_at`). Sin normalizar. | Exenta (D16) |
| **Silver** | Dimensiones (`temporada`, `equipo`, `arbitro`, `jugador`, `partido`) y hechos (`tarjeta`, `penalti`, `faltas_equipo_partido`, `anadido_partido`), normalizados y tipados. | Surrogate PK + natural UNIQUE (D16) |
| **Gold** | **Vistas SQL** (D22 — no tablas materializadas) que sirven el ranking y la ficha (P1–P6). | — (derivadas) |

---

## 3. Esquema silver — Dimensiones

### `temporada` *(D23 — temporada como dimensión)*
| Columna | Tipo | Clave / Constraint | Notas |
|---|---|---|---|
| `temporada_id` | bigint | PK surrogate | |
| `etiqueta` | text | UNIQUE (natural) | p. ej. `2025-26` |
| `fecha_inicio` | date | | |
| `fecha_fin` | date | | |
| `n_jornadas` | smallint | NULL | metadato |

### `equipo`
| Columna | Tipo | Clave / Constraint | Notas |
|---|---|---|---|
| `equipo_id` | bigint | PK surrogate | |
| `nombre_canonico` | text | UNIQUE (natural) | diana de reconciliación (D16) |

### `arbitro`
| Columna | Tipo | Clave / Constraint | Notas |
|---|---|---|---|
| `arbitro_id` | bigint | PK surrogate | |
| `nombre_canonico` | text | UNIQUE (natural) | diana de reconciliación (D16) |

### `jugador` *(ligero — D18)*
| Columna | Tipo | Clave / Constraint | Notas |
|---|---|---|---|
| `jugador_id` | bigint | PK surrogate | |
| `nombre_canonico` | text | UNIQUE (natural) | ligero, **no** load-bearing; puerta abierta a enriquecer/reconciliar y añadir alineaciones en el futuro (D18) |

### `partido` *(D20 — dimensión partido con designación)*
| Columna | Tipo | Clave / Constraint | Notas |
|---|---|---|---|
| `partido_id` | bigint | PK surrogate | |
| `temporada_id` | bigint | FK → `temporada` | (D23) |
| `jornada` | smallint | NOT NULL | dimensión de filtro de P4 (D13 — tiempo como filtro) |
| `fecha` | date | | |
| `equipo_local_id` | bigint | FK → `equipo` | habilita futuro corte casa/fuera |
| `equipo_visitante_id` | bigint | FK → `equipo` | |
| `arbitro_principal_id` | bigint | FK → `arbitro` | designación; base del ranking y del denominador "partidos dirigidos" (D20, D12) |
| — | — | UNIQUE (`temporada_id`, `jornada`, `equipo_local_id`, `equipo_visitante_id`) | clave natural del partido (D20) |

---

## 4. Esquema silver — Hechos

### Grano atómico *(D17 — una tabla por tipo de evento)*

#### `tarjeta` *(D5 tipología, D6 solo jugadores, D8 minuto, D18 atribución)*
| Columna | Tipo | Clave / Constraint | Notas |
|---|---|---|---|
| `tarjeta_id` | bigint | PK surrogate | |
| `partido_id` | bigint | FK → `partido` | |
| `jugador_id` | bigint | FK → `jugador` | receptor siempre jugador (D6) |
| `equipo_id` | bigint | FK → `equipo` | atribución **denormalizada**, capturada del acta (D18); base de P3 |
| `tipo` | `tipo_tarjeta` (enum) | NOT NULL | `amarilla` \| `segunda_amarilla` \| `roja_directa` (D5) |
| `minuto` | smallint | NOT NULL | siempre almacenado, sin filtro (D8) |
| — | — | UNIQUE (`partido_id`, `jugador_id`, `tipo`, `minuto`) | guarda de dedup/idempotencia; los eventos atómicos carecen de clave natural perfecta (D16/D17) |

> Expulsión = **estado derivado** en gold (jugador con `segunda_amarilla` o `roja_directa`), no se almacena. Amonestaciones = `amarilla` + `segunda_amarilla`.

#### `penalti` *(D7 — señalamiento atómico, D8 minuto)*
| Columna | Tipo | Clave / Constraint | Notas |
|---|---|---|---|
| `penalti_id` | bigint | PK surrogate | |
| `partido_id` | bigint | FK → `partido` | |
| `equipo_a_favor_id` | bigint | FK → `equipo` | el que lanza (D7) |
| `equipo_en_contra_id` | bigint | FK → `equipo` | el que comete (D7) |
| `minuto` | smallint | NOT NULL | (D8) |
| — | — | UNIQUE (`partido_id`, `equipo_a_favor_id`, `minuto`) | guarda de dedup |
| — | — | CHECK `equipo_a_favor_id <> equipo_en_contra_id` | integridad |

> Resultado del lanzamiento y origen (campo/VAR) **no** se capturan (D7); son atributos futuros.

### Grano agregado *(D19 — tablas a medida por grano)*

#### `faltas_equipo_partido` *(D9 — faltas agregadas por equipo)*
| Columna | Tipo | Clave / Constraint | Notas |
|---|---|---|---|
| `falta_id` | bigint | PK surrogate | |
| `partido_id` | bigint | FK → `partido` | |
| `equipo_id` | bigint | FK → `equipo` | equipo **contra** el que se señalan (D9) |
| `n_faltas` | smallint | NOT NULL | agregado por equipo y partido (D9) |
| — | — | UNIQUE (`partido_id`, `equipo_id`) | una fila por equipo y partido |

> "Faltas a favor" = espejo (las señaladas contra el rival); no se almacena aparte.

#### `anadido_partido` *(D10 — añadido por mitad, CONDICIONAL a fuente)*
| Columna | Tipo | Clave / Constraint | Notas |
|---|---|---|---|
| `anadido_id` | bigint | PK surrogate | |
| `partido_id` | bigint | FK → `partido` | |
| `minutos_primera` | smallint | | añadido anunciado 1ª mitad (D10) |
| `minutos_segunda` | smallint | | añadido anunciado 2ª mitad (D10) |
| — | — | UNIQUE (`partido_id`) | una fila por partido |

> **Dependencia viva (D10):** tabla entera condicional a que el estudio de fuentes confirme cobertura completa por partido. Si la fuente falla, se **retira la tabla entera** sin efecto colateral en el resto del esquema (por eso está aislada — D19).

---

## 5. Capa gold — Vistas *(D22 — gold como vistas SQL)*

Vistas sobre silver, sin materializar; siempre frescas, cero orquestación de refresco. Todas filtrables por `temporada` y por rango de `jornada` (P4).

| Vista | Grano | Sirve | Lógica clave |
|---|---|---|---|
| `v_evento_arbitro` | evento | base común | `UNION` de `tarjeta` + `penalti` normalizados a (árbitro vía partido, partido, tipo_evento, minuto, equipo) — resuelve "todos los eventos del árbitro X" (D17) |
| `v_ranking_arbitro` | árbitro | **P1, P2, P6** | `partidos_dirigidos` = COUNT sobre `partido` por `arbitro_principal_id` (D20); totales por métrica; **tasa/partido** (D12); **mediana de liga solo en faltas y amarillas** (D15) |
| `v_ficha_arbitro_equipo` | árbitro × equipo | **P3** | conteos brutos desglosados por `equipo_id` (D2, D14) |
| `v_resumen_partido` | partido | composición | reúne las cuatro fuentes de hechos por partido (D19) |

> **Estados derivados en gold:** expulsión (de `tipo`), amonestaciones (`amarilla`+`segunda_amarilla`). La **referencia de mediana** se calcula a nivel liga sobre la temporada, y **solo** para métricas de volumen (D15).

---

## 6. Mapa de relaciones

```
temporada 1 ──< N partido
equipo    1 ──< N partido   (local)
equipo    1 ──< N partido   (visitante)
arbitro   1 ──< N partido   (principal — designación, D20)

partido   1 ──< N tarjeta
partido   1 ──< N penalti
partido   1 ──< N faltas_equipo_partido   (2 filas: local y visitante)
partido   1 ──< 0..1 anadido_partido       (condicional, D10)

jugador   1 ──< N tarjeta
equipo    1 ──< N tarjeta                  (equipo_id, atribución D18)
equipo    1 ──< N penalti                  (a favor / en contra)
equipo    1 ──< N faltas_equipo_partido
```

Toda métrica del árbitro se resuelve vía `partido.arbitro_principal_id`; el desglose por equipo (P3), vía `tarjeta.equipo_id` y los dos equipos de `penalti`.

---

## 7. Puertas futuras (abiertas, no construidas)

El esquema admite cada módulo aparcado **sin reescritura**:

| Módulo / extensión | Cómo entra | Origen |
|---|---|---|
| **Módulo VAR** | Nueva(s) tabla(s) de hecho colgando de `partido` | D4 |
| **Tarjetas a oficiales** | Campo `receptor_tipo` o tabla paralela; el resto del esquema intacto | D6 |
| **Resultado / origen del penalti** | Columnas nuevas en `penalti` | D7 |
| **Faltas atómicas** | Nueva tabla atómica (grano fino) junto al agregado | D9 |
| **Explorador árbitro×equipo (brutos)** | Vista gold sobre tablas existentes | D14 (1er módulo post-MVP) |
| **Vista de evolución temporal** | Vista gold sobre tablas existentes | D13 |
| **Detector de desviaciones (módulo C)** | Analítica gold sobre tablas existentes | aparcado |
| **Jugador canónico / alineaciones** | Enriquecer `jugador`; añadir tabla de alineaciones | D18 |
| **Versionado de correcciones** | Campo `estado`/`version` en eventos, sin sobrescribir | D21 |
| **Cuadro arbitral completo** | Migrar `arbitro_principal_id` a tabla `designacion` (partido, arbitro, rol) | D20 |
| **Materialización** | Promover vistas gold a `MATERIALIZED VIEW` | D22 |
| **Multi-temporada** | `INSERT` en `temporada`; el resto ya lo referencia | D23 |

---

## 8. Registro de decisiones del bloque 3 (D16–D23)

- **D16 — Estrategia de claves.** PK surrogate en silver/gold; claves naturales como UNIQUE (unicidad, dedup, diana de reconciliación). Bronze exento.
- **D17 — Forma de eventos atómicos.** Una tabla por tipo: `tarjeta` (jugador + tipo) y `penalti` (dos equipos). "Todos los eventos" vía vista `UNION`.
- **D18 — Atribución a equipo de la tarjeta.** `equipo_id` denormalizado en el evento; jugador ligero; puerta abierta a jugador canónico/alineaciones.
- **D19 — Hechos agregados.** Tablas a medida por grano: `faltas_equipo_partido` y `anadido_partido` (añadido aislado por su condicionalidad).
- **D20 — Dimensión partido y designación.** `partido` con PK surrogate, clave natural temporada+jornada+local+visitante, y árbitro principal como FK directa.
- **D21 — Correcciones post-partido.** Acta original = fuente de verdad; sin versionado en el MVP (extensión futura anotada).
- **D22 — Capa gold.** Vistas SQL (no materializadas); promoción a materializadas reservada.
- **D23 — Temporada.** Dimensión propia con FK en `partido`; multi-temporada como `INSERT`.

---

## 9. Dependencias vivas y siguiente bloque

- **Dependencia viva (D10):** la tabla `anadido_partido` permanece condicional hasta que el estudio de fuentes confirme (o niegue) cobertura completa por partido. El esquema la incluye de forma aislada para poder retirarla sin coste si la fuente no acompaña.
- **Siguiente bloque natural — Fuentes + Validación:** resuelve la dependencia de D10, valida a posteriori el criterio de homogeneidad de fuente que gobernó todas las inclusiones/exclusiones, y define la reconciliación de entidades (los `nombre_canonico` UNIQUE de este esquema son su diana). Es el desbloqueo principal del proyecto.

---

*Fin del bloque 3 y de los tres entregables de diseño (diseño funcional, casos de uso, modelo de datos). El diseño queda cerrado y listo para la fase de fuentes/validación e implementación.*
