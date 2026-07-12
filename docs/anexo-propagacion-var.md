# Anexo de propagación — Miniciclo VAR (D35–D38) + D39

*Documento de propagación. Recoge, por bloque afectado, los cambios que el miniciclo VAR y la decisión D39 (análisis exploratorio antes de silver) introducen en las síntesis previas de los bloques 2, 3, 4 y 5. No sustituye a esas síntesis: se lee **junto a ellas**. El bloque 1 sí queda sustituido por su versión v2.*

---

## Cambios en el bloque 2 — Casos de uso

### 2.1 Ranking (P1) — nueva columna
El ranking de árbitros gana la columna **"decisiones VAR con impacto"** — filas de `evento_var` con `resultado = modifica`, agregadas por árbitro principal. La columna:
- Se ordena y filtra como las demás (D12: tasa por partido con total y denominador visibles).
- Lleva **etiqueta contextual breve** (D37) con enlace a la página de metodología.
- **No** tiene mediana de liga como referencia (D15: mediana solo en métricas de volumen — faltas, amarillas — no en las raras).

### 2.2 Ficha (P2) — nueva sección "Actividad VAR"
Dos bloques:
- **Decisiones VAR con impacto:** total del árbitro, desglosado por tipo de decisión revisada (goles anulados / tarjetas modificadas / penaltis modificados).
- **Contexto (no ranqueado):** revisiones que confirmaron la decisión de campo.

La etiqueta contextual de D37 acompaña también al encabezado de la sección.

### 2.3 Nueva pregunta P7
- **P7 · Actividad VAR sobre el árbitro X.** ¿Cuántas de sus decisiones fueron modificadas por revisión VAR, y de qué tipo? ¿Cuántas se ratificaron? *(D35, D36, D38.)*

### 2.4 Salidas / entradas de la tabla "Preguntas FUERA del MVP"
- **Sale del listado:** "Cualquier pregunta sobre VAR". Ya está dentro con las limitaciones fijadas por D35.
- **Entra al listado (o se enriquece la fila existente):**
  - "Perfilador de árbitros VAR" — el dato está en el modelo (D36), la superficie se aplaza.
  - "Explorador árbitro×equipo" — la fila ya estaba; **se enriquece** para incluir el **balance V-E-D** por equipo, con la misma disciplina de brutos y nº de enfrentamientos visible. El balance V-E-D no entra al MVP porque introduce la asociación "resultado del partido ↔ árbitro" que la comunicación descriptiva actual no soporta bien; encaja mejor en un módulo dedicado con su propio contexto.

---

## Cambios en el bloque 3 — Modelo de datos

### 3.1 Nueva tabla `evento_var` en silver

Siguiendo el patrón D17 (una tabla por tipo de evento):

| Columna | Tipo | Clave / Constraint | Notas |
|---|---|---|---|
| `evento_var_id` | bigint | PK surrogate (D16) | |
| `partido_id` | bigint | FK → `partido` | |
| `arbitro_principal_id` | bigint | FK → `arbitro` | atribución doble de D36 |
| `arbitro_var_id` | bigint | FK → `arbitro` | atribución doble de D36 |
| `minuto` | smallint | NOT NULL | del feed |
| `tipo_decision_revisada` | `tipo_decision_var` (enum) | NOT NULL | `gol` \| `tarjeta` \| `penalti` |
| `resultado` | `resultado_var` (enum) | NOT NULL | `modifica` \| `confirma` (D35) |
| — | — | UNIQUE (`partido_id`, `minuto`, `tipo_decision_revisada`) | guarda de dedup |

Los enums viven en Postgres como tipos propios, igual que `tipo_tarjeta`.

### 3.2 Cambios en gold (vistas)

- **`v_ranking_arbitro`** (D22): añade la columna `decisiones_var_con_impacto`, calculada como `COUNT(*)` sobre `evento_var` filtrando por `arbitro_principal_id` y `resultado = 'modifica'`, con su tasa por partido.
- **`v_ficha_arbitro_var`** (nueva vista): sirve la sección VAR de la ficha (P2). Modificaciones desglosadas por `tipo_decision_revisada` y conteo de confirmaciones, por árbitro.
- **`v_evento_arbitro`** (D17): se amplía el `UNION` para incluir eventos VAR con su semántica normalizada (tipo `var_modifica`, `var_confirma`).

### 3.3 Actualización del mapa de relaciones

Se añaden estas líneas al mapa existente:

```
partido   1 ──< N evento_var
arbitro   1 ──< N evento_var   (arbitro_principal_id)
arbitro   1 ──< N evento_var   (arbitro_var_id)
```

### 3.4 Actualización de la tabla "Puertas futuras"

- **Módulo VAR:** pasa de aparcado a **implementado**.
- **Nueva puerta abierta — Perfilador de árbitros VAR:** el dato existe (D36); la vista de ranking/ficha por árbitro VAR es la extensión natural (nueva `v_ranking_arbitro_var`).
- **Puerta enriquecida — Explorador árbitro×equipo:** además del cruce en brutos ya previsto (D14), incluir el **balance V-E-D**.

### 3.5 Notas de rigor que no cambian el esquema

- **Coherencia con D21 (acta original inmutable como verdad):** cuando una revisión VAR modifica una decisión de campo (p. ej. revoca una roja), **la fila original en `tarjeta` NO se borra**. La roja se registró en el minuto X; el evento VAR queda como fila separada en `evento_var`. Ambas conviven; la lectura de "actividad efectiva" se construye en gold. La verdad de campo se preserva.

---

## Cambios en el bloque 4 — Fuentes y validación

### 4.1 Reparto fuente ↔ métrica (fila nueva)

| Métrica | Fuente primaria | Cross-check |
|---|---|---|
| **Eventos VAR de veredicto** | **LaLiga.com** (`match_comment_kind` 4 y 28) | — (no hay segunda fuente estructurada; ver 4.2) |

### 4.2 Validación ligera (D26) — chequeo específico VAR

Se añade al conjunto de chequeos:
- **Consistencia interna VAR:** en partidos con `evento_var.resultado = modifica` sobre `tipo_decision_revisada = tarjeta`, debería existir un evento de tarjeta en el mismo minuto (o muy cercano) en la tabla `tarjeta`. Si no existe, se marca con flag (mismo mecanismo de D26: registrar, no sobrescribir).

**Lo que NO se puede verificar:** los *checks silenciosos* (revisiones de cabina sin comunicación) no están en el feed. Esta limitación se comunica en la página de metodología (D37); no se intenta reconstruirla ni inferirla.

### 4.3 Reconciliación de entidades (D25)
- El **árbitro VAR designado** entra al mismo mecanismo de identidad canónica que el principal (nombre canónico como UNIQUE; conjunto reducido, verificable a mano). El feed lo expone con `role.id: 9`.

---

## Cambios en el bloque 5 — Arquitectura técnica

**Ninguno estructural.** El scraper tonto (D18) ya captura el JSON entero — los `match_comment_kind` 4, 24 y 28 aterrizan en `bronze` sin cambio. dbt (D31) parsea los eventos VAR desde `bronze` y los materializa en la nueva tabla silver `evento_var`. Los tests de dbt (parte de D26) ganan `accepted_values` para los dos nuevos enums (`tipo_decision_revisada`, `resultado`).

**Requisito nuevo del MVP derivado de D37:** la **página pública de metodología** deja de ser pieza pendiente opcional y pasa a ser requisito duro del MVP. En términos de arquitectura, es un artefacto estático (Markdown/HTML) que puede vivir en `docs/` del repo y publicarse desde Streamlit Cloud como una vista más de la app, o como página independiente.

---

## D39 — Fase de análisis del contenido scrapeado antes de silver

**Motivación.** Antes de escribir modelos dbt de silver, con `bronze` cargado con una muestra suficiente de partidos, se ejecuta un análisis exploratorio del contenido real para descubrir la forma efectiva del feed y diseñar silver "atinada y tolerante al fallo" sobre evidencia, no supuestos.

**Cabos que esta fase cierra de una vez:**
- **Cabo D5 vivo:** cómo se marca `segunda_amarilla` vs `roja_directa` en LaLiga.com.
- **Verificación D30:** confirmar que el blob embebido cubre todo, o localizar endpoints XHR complementarios.
- **Cobertura del añadido (D26):** validar en los 380 partidos.
- **Inventario completo de `match_comment_kind`:** todos los tipos que aparecen en la práctica (más allá de los ~17 que hemos visto), con conteos y ejemplos.
- **Detalle VAR:** confirmar el patrón kind 4 sobre penaltis (aún no visto explícitamente); listar todas las variantes textuales de `content` para el mismo `kind`.

**Forma de trabajo.** Notebook exploratorio sobre `bronze`, con inventarios (todos los `kind` vistos, todas las combinaciones de campos, distribuciones de nulls por campo, casos raros), no un proceso automatizado. Es descubrimiento humano, no ETL.

**Producto.** Un documento breve —"anatomía real del feed"— que alimenta:
- Los `schema.yml` de dbt (tipos, `accepted_values`, `not_null`).
- Los tests de dbt (parte de D26).
- Los enums de silver, si el análisis revela valores no anticipados.

**Refuerza D31:** la calidad de los `accepted_values` y `not_null` de silver depende directamente de este análisis. Los tests aterrizan sobre evidencia, no sobre supuestos.

**Muestra suficiente:** a definir en implementación. Sugerencia razonable: una jornada completa (~10 partidos) más una muestra estratificada de partidos con expulsión, penalti(s) y VAR — para cubrir el long tail.

---

## Registro consolidado del proyecto

Con este anexo, el registro completo del proyecto queda así:

- **Bloque 1 (v2)** — D1–D10 + miniciclo VAR (D35–D38). *Ver bloque-1-diseno-funcional.md v2.*
- **Bloque 2** — D11–D15. *Ver bloque-2-casos-de-uso.md + §"Cambios en el bloque 2" arriba.*
- **Bloque 3** — D16–D23. *Ver bloque-3-modelo-de-datos.md + §"Cambios en el bloque 3" arriba.*
- **Bloque 4** — D24–D26. *Ver bloque-4-fuentes-y-validacion.md + §"Cambios en el bloque 4" arriba.*
- **Bloque 5** — D27–D34 + **D39**. *Ver bloque-5-arquitectura-tecnica.md + §"Cambios en el bloque 5" y §D39 arriba.*

**Total: 38 decisiones activas** (D1–D39 con D4 reabierta y superada por D35–D38).

---

## Estado final del proyecto

Con el bloque 1 v2, este anexo, y D39 registrada, el **diseño del observatorio queda cerrado**. No hay decisiones pendientes; los cabos vivos que quedaban se resuelven todos en la fase de análisis de contenido scrapeado (D39), que es implementación.

Lo que sigue es:
1. Montar el scraper y aterrizar bronze con una muestra suficiente de partidos.
2. Ejecutar el análisis exploratorio de D39 y producir "anatomía real del feed".
3. Diseñar y escribir los modelos dbt de silver sobre la evidencia recogida.
4. Escribir las vistas gold.
5. Montar los workflows de GitHub Actions.
6. Redactar la página de metodología (requisito duro por D37).
7. Publicar la app Streamlit.

*Fin del anexo. Cierre del diseño.*
