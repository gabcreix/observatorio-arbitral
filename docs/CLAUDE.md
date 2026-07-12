# CLAUDE.md — Observatorio Arbitral de LaLiga

*Este fichero es el preámbulo de contexto para cualquier sesión de desarrollo del proyecto. Léelo antes de escribir código. Los documentos de diseño referenciados están en `docs/`.*

---

## Quién soy y qué construyo

Soy Gabriel, data engineer / AI developer. Estoy construyendo un **observatorio público del arbitraje en LaLiga (Primera División)** como pieza de portfolio y como herramienta genuinamente útil.

El proyecto es un pipeline de datos completo: scraper Python → PostgreSQL (Neon) → dbt (bronze/silver/gold) → Streamlit. Perfila a los árbitros principales con métricas objetivas (tarjetas, penaltis, faltas, tiempo añadido, y decisiones VAR con impacto).

## Cómo hemos trabajado en el diseño

He usado con Claude un método muy concreto durante todo el diseño y quiero mantenerlo en el desarrollo:

1. **Decisiones pequeñas, numeradas, documentadas.** El diseño está compuesto por 38 decisiones (D1–D39, con D4 reabierta) recogidas en cinco documentos de síntesis (`docs/bloque-1-...` a `docs/bloque-5-...` + `docs/anexo-propagacion-var.md`). En desarrollo quiero seguir el mismo espíritu: cuando aparezca un fork real, plantearlo con 2–3 opciones, tradeoffs honestos y una recomendación explícita — no elegir por mí en silencio.

2. **Fricción cuando toca (regla 4).** Si una decisión mía choca con una decisión previa (D1–D39), quiero que me lo señales antes de ejecutar, con la referencia concreta a qué decisión choca y por qué. Varias veces el diseño mejoró porque Claude me paró y ofreció un puente en vez de aceptar sin más.

3. **Concisión estructurada.** Prefiero respuestas concisas y estructuradas a párrafos largos. Al citar decisiones (D1, D9, D22…), acompáñalas siempre de una descripción breve de a qué se refieren, para no depender de tener la doc delante.

4. **Aprendizaje guiado de dbt.** No domino dbt. Enséñamelo **a medida que el proyecto lo necesita** — qué es un modelo cuando escribamos el primero, qué es un test cuando cablemos D26, qué es un `source` cuando conectemos bronze. No lecciones abstractas.

## Referencia rápida del stack

- **Ingesta:** Python + HTTP (nada de headless — el JSON viene embebido en el HTML de LaLiga.com; ver D30).
- **Base:** Neon (PostgreSQL serverless, scale-to-zero) — no Supabase.
- **Transformación:** dbt sobre Postgres, bronze → silver → gold. Gold son **vistas SQL**, no materializadas (D22).
- **Orquestación:** GitHub Actions con dos workflows (`workflow_dispatch` para backfill; `schedule` semanal). Un solo pipeline idempotente.
- **App:** Streamlit con `st.cache_data`, alojada en Streamlit Community Cloud.

## Principios innegociables del proyecto (no revisar sin abrirlo como decisión)

- **D1** — Solo eventos objetivamente verificables. No juzga acierto/error arbitral.
- **D18** — El scraper es **tonto**: captura el payload entero verbatim en bronze. Nunca pre-filtrar a las métricas del MVP.
- **D21** — El evento original es inmutable (una roja revocada por VAR no se borra de `tarjeta`; queda en `tarjeta` **y** en `evento_var`).
- **D26** — Validación ligera con "marcar sin sobrescribir" ante discrepancias.
- **D27** — Frontera dura scraper ↔ transformación: la transformación **nunca** invoca al scraper; lee exclusivamente de bronze.
- **D37** — La comunicación de "lo que NO se puede concluir" es característica visible del producto (etiqueta contextual en el ranking VAR + página de metodología como requisito duro del MVP).

## Estructura del repo

- `scraper/` — Python. Escribe a bronze en Neon.
- `dbt/` — proyecto dbt (`models/bronze`, `models/silver`, `models/gold`; `sources.yml`; `tests`).
- `app/` — Streamlit.
- `docs/` — los cinco documentos de síntesis del diseño + anexo VAR + este CLAUDE.md.
- `.github/workflows/` — `backfill.yml` (manual) y `ingest.yml` (schedule).

## Estado actual y siguiente paso concreto

**Estado:** diseño cerrado (D1–D39), sin decisiones de diseño pendientes. Cero código escrito todavía.

**Siguiente paso concreto (por D39):** montar el scraper mínimo, aterrizar `bronze` con una muestra suficiente de partidos (una jornada + partidos con expulsión/penalti/VAR), y ejecutar un **análisis exploratorio** para descubrir la forma real del feed antes de escribir los modelos dbt de silver. Es descubrimiento humano en notebook, no ETL automatizado.

**Cabos vivos que ese análisis debe cerrar:**
- Cómo se marca `segunda_amarilla` vs `roja_directa` en LaLiga.com (cabo D5).
- Verificar que el blob JSON embebido cubre todo, o localizar endpoints XHR complementarios (D30).
- Cobertura completa del añadido en los 380 partidos (D26).
- Inventario completo de `match_comment_kind` con conteos y ejemplos.

## Cómo quiero que arranques la sesión

Antes de escribir código: recorre `docs/` los documentos de bloque que sean relevantes para la tarea del día. Si no sabes cuáles, pregúntame qué toca. Si vas a tocar algo que roza un principio innegociable de arriba, párame antes.
