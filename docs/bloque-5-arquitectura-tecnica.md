# Observatorio Arbitral de LaLiga — Bloque 5: Arquitectura técnica

*Documento de síntesis autocontenido. Recoge las decisiones D27–D34 y las convenciones de implementación derivadas. Pone en pie el circuito completo del proyecto sobre las decisiones de diseño de los bloques 1–4 (D1–D26). Nivel: arquitectura y stack, no código.*

---

## 1. Circuito completo del proyecto

```
[LaLiga.com]  ──HTTP + JSON embebido──▶  [Scraper Python]
                                              │
                                              ▼
                                       [Bronze  (Neon)]
                                              │
                                              ▼
                                       [dbt: silver + gold vistas]
                                              │
                                              ▼
                                       [Neon  (Postgres serverless)]
                                              ▲
                                              │  st.cache_data
                                       [Streamlit Community Cloud]
                                              ▲
                                              │
                                          Usuario público

Orquestación: GitHub Actions
  · workflow manual (backfill temporada)   ┐  mismo pipeline
  · workflow programado (semanal)          ┘  idempotente
Ambos: scraper → bronze → dbt run + dbt test
```

Dos ritmos de ejecución (backfill puntual + captura semanal) sobre **un único pipeline idempotente**. Cero infraestructura *always-on*: Neon con scale-to-zero (D29), GitHub Actions por lotes (D32), Streamlit Cloud con hibernación (D34).

---

## 2. Piezas y responsabilidades

### 2.1 Extracción — Scraper (Python)
- **Aislado** como etapa separada; su única salida es escribir bronze (D27).
- **Tonto**: captura el payload **entero verbatim** — todo lo que la fuente da, no solo las métricas del MVP. Así el excedente del feed (VAR, resultado/origen de penalti, faltas atómicas, cuadro completo…) queda disponible en bronze para módulos futuros **sin volver a scrapear**.
- **Técnica: HTTP + parseo del JSON embebido** / endpoint interno que la propia app consume (D30). Sin navegador headless: el JSON es más estable que el DOM, ligero en CI, mínima huella de rate-limit.
- **Frontera dura**: el pipeline de transformación *nunca* invoca al scraper; lee exclusivamente de bronze.

### 2.2 Bronze — copia cruda literal
- **Tabla `bronze` en Neon** (D28), una fila por partido: payload crudo + metadatos de procedencia (`source_url`, `fetched_at`, clave natural del partido).
- **JSONB** si el blob embebido lo trae todo; **text** si algún dato exige guardar el HTML crudo. Verificable al aterrizar.
- Sirve dos propósitos operativos: (a) **reproducibilidad** (D21 — acta original inmutable como verdad, aplicado al snapshot de fuente) y (b) **objeto de validación** (D26 — la validación ligera trabaja contra esta copia congelada).

### 2.3 Transformación — dbt (D31)
- **dbt sobre Postgres** de punta a punta: bronze (JSONB) → silver (extracción JSONB tipada, D3-esquema del bloque 3) → gold (vistas, D22).
- **Tests de dbt** implementan de forma declarativa parte de D26: `not_null`, `unique` sobre claves naturales de D16, `accepted_values` para el enum de tarjeta (D5), rangos de sanidad.
- **Linaje y docs automáticos** (`dbt docs`) como artefacto de portfolio y documentación viva.
- **Idempotencia** por reconstrucción y por las UNIQUE de D16 (surrogate PK + clave natural).
- *Nota de aprendizaje:* dbt se enseña durante la implementación, concepto por concepto y cuando el proyecto lo necesite (modelo → test → source → macro), no en abstracto.

### 2.4 Base de datos — Neon (D29)
- **PostgreSQL serverless** con scale-to-zero (sin la pausa por inactividad de otros gestionados) y **branching** para probar migraciones y re-runs sin tocar producción.
- **No se toca ninguna decisión previa**: el esquema (bloque 3), las vistas de gold (D22), el JSONB de bronze (D28) son Postgres estándar.
- Sin auth ni storage integrados; irrelevante para el MVP (app pública de solo lectura; bronze como tabla).

### 2.5 App — Streamlit
- **Consulta directa** a las vistas de gold en Neon, con **`st.cache_data`** para amortiguar el cold start y la latencia (D33).
- Refresco tras cada ingesta semanal: por **TTL** del caché o botón manual de "refrescar".
- La lógica de agregación vive **en las vistas de gold**, no en la app (una sola fuente de verdad).
- **Alojada en Streamlit Community Cloud** (D34), ligada al repositorio de GitHub; despliegue trivial, mantenimiento cero. Migración a PaaS (Render/Railway/Fly) queda como puerta abierta si molesta la hibernación o se quiere dominio propio.

### 2.6 Orquestación — GitHub Actions (D32)
- **Dos workflows sobre el mismo pipeline idempotente**:
  - **Manual** (`workflow_dispatch`) → backfill de la temporada (D3), troceable por jornadas.
  - **Programado** (`schedule`, semanal tras la jornada) → captura incremental.
- Secuencia común: **scraper → bronze → `dbt run` + `dbt test`**.
- La idempotencia se apoya en las UNIQUE de D16 (UPSERT en bronze/silver) y en la reconstrucción de dbt.

---

## 3. Convenciones de implementación (no elevadas a decisión)

Estas piezas quedan resueltas por las decisiones ya tomadas o son convención estándar; se documentan aquí para que la implementación arranque sin fricción.

### 3.1 Estructura del repositorio
Convivencia limpia de las tres piezas de código en un mismo repo (el mismo que dispara Streamlit Cloud y los workflows):
- `scraper/` — Python (extracción → bronze).
- `dbt/` — proyecto dbt (`models/`, `tests/`, `sources.yml`, `profiles.yml`).
- `app/` — Streamlit (consultas cacheadas a las vistas de gold).
- `.github/workflows/` — `backfill.yml` (manual) y `ingest.yml` (schedule).
- `docs/` — los cuatro documentos de síntesis (bloques 1–4) + este.

### 3.2 Secretos y configuración
Variables de entorno estándar: URL de Neon en secretos de GitHub Actions (para el pipeline) y en la UI de Streamlit Cloud (para la app). Sin fichero de secretos en el repo.

### 3.3 Testing y observabilidad
- **Tests de datos:** los de dbt (§2.3) — que ya cumplen parte de D26.
- **Tests de código:** ligeros en el scraper (parseo del JSON contra un fixture guardado), por si el formato de LaLiga.com cambia — el fixture actúa de canario.
- **Observabilidad mínima:** logs de GitHub Actions + `dbt docs` publicado. Suficiente para un MVP; si algún día molesta, se puede añadir un runbook simple.

### 3.4 Migraciones de esquema
Gestionadas por dbt (los modelos SON el esquema de silver/gold). Para cambios delicados: **branching de Neon** como red de seguridad — probar la migración en un branch antes de mergear.

---

## 4. Registro de decisiones del bloque 5 (D27–D34)

- **D27 — Frontera scraper ↔ transformación.** Scraper como etapa aislada que escribe bronze; la transformación lee exclusivamente de bronze, nunca invoca al scraper.
- **D28 — Medio físico de bronze.** Tabla `bronze` en Postgres (JSONB / text) con metadatos de procedencia. Un solo sistema; copia cruda auditable con SQL.
- **D29 — Proveedor de PostgreSQL.** Neon (serverless, scale-to-zero, branching). Reemplaza a Supabase como supuesto de fondo. Puro cambio de proveedor: no toca ninguna decisión previa.
- **D30 — Técnica de extracción.** HTTP + parseo del JSON embebido / endpoint interno. Sin navegador headless: más estable, ligero, barato.
- **D31 — Pipeline de transformación.** dbt sobre Postgres de punta a punta (bronze → silver → gold). Tests de dbt cablan parte de D26; linaje y docs automáticos. Aprendizaje guiado durante la implementación.
- **D32 — Orquestación.** Dos workflows de GitHub Actions (manual + programado) sobre el mismo pipeline idempotente. Cero infra always-on.
- **D33 — Acceso de la app a los datos.** Streamlit consulta las vistas de Neon directamente, con `st.cache_data`. Cero infra intermedia; refresco por TTL o botón.
- **D34 — Alojamiento de la app.** Streamlit Community Cloud, con puerta abierta a PaaS si conviene.

---

## 5. Cabos pendientes (no bloquean implementación)

- **Cabo D5 vivo** — Cómo se marca `segunda_amarilla` vs `roja_directa` en LaLiga.com. Descubrimiento sobre partido real con expulsión; afecta al parser, no al modelo.
- **Verificación D30** — Confirmar que el blob embebido trae panel + timeline + cuadro arbitral completos; si algún campo falta, localizar el endpoint XHR que lo sirve.
- **Cobertura del añadido (D26)** — Validar en los 380 partidos que el evento de añadido viene sin huecos. Es la validación (1) de D26 aplicada.
- **Acceso al acta (RFEF)** — Vía limpia al acta dado el `robots.txt` del endpoint heredado. Parte del escaneo ético/legal ligero.

Ninguno bloquea empezar la implementación; se resuelven al aterrizar en la fuente real.

---

## 6. Estado global del proyecto

Con el bloque 5 cerrado, el **diseño y la arquitectura del observatorio están completos**: bloques 1–4 fijan *qué* se construye y cuáles son las verdades del dato (D1–D26); el bloque 5 fija *cómo* se pone en pie (D27–D34). No quedan decisiones de diseño ni de arquitectura pendientes.

Lo que sigue es **implementación**: montar la ingesta (con el aterrizaje real de la fuente que resuelve los cabos pendientes), levantar el proyecto dbt (con enseñanza guiada), montar los workflows y publicar la app. Piezas identificadas a lo largo del proyecto y aún no abordadas —ninguna bloquea el MVP— quedan como trabajo posterior: página pública de metodología, escaneo ético/legal ligero, y los módulos aparcados del bloque 1 (VAR, detector de desviaciones, explorador árbitro×equipo, tarjetas a oficiales, evolución temporal, resultado/origen del penalti, faltas atómicas, cuadro arbitral completo).

---

*Fin del bloque 5. Los cinco documentos de síntesis, juntos, constituyen el diseño completo del observatorio, listo para implementar.*
