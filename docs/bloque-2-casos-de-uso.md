# Observatorio Arbitral de LaLiga — Bloque 2: Casos de uso

*Documento de síntesis autocontenido. Recoge las decisiones D11–D15 y la lista priorizada de preguntas del MVP. Se apoya en el bloque 1 (diseño funcional) y precede al bloque 3 (modelo de datos), que debe soportar todas las preguntas del MVP sin cerrar la puerta a los módulos futuros.*

---

## 1. Usuario y propósito

**Usuario primario:** el **analítico** — llega a **explorar sin un nombre en mente** (rankings, "quién saca más rojas", "quién pita más faltas"), quiere filtrar, ordenar y comparar entre árbitros, y sabe leer una cifra en su contexto.

**Doble función del producto:** herramienta pública **y** pieza de portfolio, con el portfolio tirando de **lucir algo técnicamente concreto** — una superficie de exploración analítica interactiva es, en sí misma, el objeto de portfolio.

**Disciplina del bloque:** los tres rasgos del usuario empujan hacia "más rico y más vistoso", que es el vector que puede inflar el alcance por encima de "terminable en ratos libres". La contramedida adoptada en todo el bloque ha sido mantener **una espina única** (una superficie de ranking + una de ficha) y resistir abrir superficies paralelas.

---

## 2. Modelo de exploración (recorrido del usuario)

La superficie primaria es **árbitro-céntrica**, coherente con la unidad de análisis del bloque 1:

1. **Puerta de entrada — ranking de árbitros.** Una tabla de árbitros ordenable y filtrable por las métricas del MVP. Aquí se resuelve "explorar sin nombre": el usuario ordena y descubre.
2. **Drill-down — ficha del árbitro.** Al elegir un árbitro se baja a su perfil completo (la pregunta-estrella del bloque 1), con el desglose por equipo dentro.
3. **Dimensiones dentro, no puertas propias:** *tiempo* (filtro por rango de jornadas) y *equipo* (desglose dentro de la ficha) modulan las dos superficies anteriores; ninguna es una entrada de primera clase.

**Base de comparabilidad:** el ranking se ordena por **tasa por partido** (evento ÷ partidos dirigidos), con el **total bruto** también visible y el **denominador (partidos dirigidos) siempre a la vista**. Es aritmética sobre el conteo, no un juicio; el ruido de muestra pequeña se comunica mostrando el denominador, no ocultando árbitros.

**Referencia de tendencia central:** se muestra la **mediana de liga** como referencia **solo en métricas de volumen (faltas y amarillas)**, donde la muestra la sostiene. En rojas y penaltis no hay referencia (solo orden y cifra), para no fabricar una señal donde sobre una sola temporada hay ruido.

---

## 3. Lista priorizada de preguntas del MVP

Las métricas disponibles son las del bloque 1: amarillas, segundas amarillas, rojas directas, penaltis señalados (a favor / en contra), faltas pitadas (agregadas por equipo), y tiempo añadido (agregado por mitad — **condicional a fuente**).

### Nivel 1 — Núcleo (debe funcionar impecable)

- **P1 · Ranking por métrica.** ¿Qué árbitros encabezan cada métrica? Tabla ordenable por cualquiera de las métricas, en **tasa por partido** o **total bruto**. *(D11, D12)*
- **P2 · Perfil del árbitro.** ¿Cuál es el retrato completo de un árbitro concreto? Ficha con sus métricas en total y tasa/partido, con partidos dirigidos a la vista. *(D11, D12)*
- **P3 · Desglose por equipo.** ¿Cómo reparte el árbitro X sus tarjetas / penaltis / faltas entre los distintos equipos? Desglose por club **dentro de la ficha**, en conteos brutos. *(D2, D14)*

### Nivel 2 — Refinamientos de exploración (dentro del MVP)

- **P4 · Corte temporal.** ¿Y si acoto a un tramo de la temporada (p. ej. primera vuelta)? El mismo ranking y la misma ficha, filtrados por rango de jornadas. *(D13)*
- **P5 · ¿Es alto respecto a lo típico?** ¿La tasa de faltas o amarillas del árbitro X está por encima o por debajo de la mediana de la liga? Solo para métricas de volumen. *(D15)*
- **P6 · Tamaño de muestra.** ¿Sobre cuántos partidos se calcula esto? El denominador (partidos dirigidos) acompaña siempre a la tasa, para que el usuario juzgue la fiabilidad. *(D12)*

*Nota:* las preguntas sobre **tiempo añadido** (variantes de P1/P2) solo se sirven si el estudio de fuentes confirma la cobertura por partido (D10). Si no, esas variantes caen junto con la métrica.

---

## 4. Preguntas explícitamente FUERA del MVP (con destino)

Se listan porque un usuario analítico las esperará; cada una tiene un hogar definido, y el modelo de datos del bloque 3 debe dejarlas viables sin construirlas.

| Pregunta que un usuario podría esperar | Por qué no está en el MVP | Destino |
|---|---|---|
| "¿Cómo es tratado el equipo Y por el conjunto de árbitros?" (agregado por equipo) | Sobre una temporada, el corte por árbitro×equipo es de muestra mínima; como ranking reintroduce el titular de sesgo | **Primer módulo post-MVP:** explorador árbitro×equipo en **brutos**, con nº de enfrentamientos visible *(D14)* |
| "¿Cómo evoluciona el árbitro X a lo largo de la temporada?" (tendencia visualizada) | Serie temporal de eventos raros sobre una temporada es ruidosa; superficie nueva | Módulo posterior con masa multi-temporada. Aproximable toscamente hoy con el filtro de P4 *(D13)* |
| "¿Qué árbitros se desvían significativamente de lo normal?" | Requiere líneas base y control de confusores; instala el marco de desviación | Módulo C aparcado (detector de desviaciones) |
| Cualquier pregunta sobre VAR | Fuente irregular → sesgo de cobertura | Módulo VAR *(D4)* |
| "¿El penalti se transformó? ¿De dónde vino?" | Mide al lanzador o es detalle-VAR | Atributos futuros del penalti *(D7)* |
| "¿Cuántas tarjetas a entrenadores/banquillo?" | Bifurca atribución; masa fina; riesgo de cobertura | Módulo tarjetas a oficiales *(D6)* |
| "¿Debió pitar penalti aquí?" (faltas/penaltis no señalados) | Es juicio, no hecho | **Descartado de plano** — rompe el principio de rigor *(D1)* |

---

## 5. Registro de decisiones del bloque 2 (D11–D15)

- **D11 — Superficie de exploración primaria.** Árbitro-céntrica: ranking de árbitros ordenable/filtrable → drill-down a ficha. Equipo y tiempo son dimensiones dentro, no puertas.
- **D12 — Base de comparabilidad.** Tasa por partido como base, con total bruto y denominador (partidos dirigidos) siempre visibles.
- **D13 — Dimensión temporal.** Tiempo como filtro por rango de jornadas; sin vista de evolución dedicada (aplazada).
- **D14 — Dimensión equipo.** Solo desglose dentro de la ficha en el MVP; el cruce árbitro×equipo se reserva como primer módulo post-MVP, en brutos y con nº de enfrentamientos visible.
- **D15 — Referencia de tendencia central.** Mediana de liga como referencia solo en métricas de volumen (faltas, amarillas); nada en rojas y penaltis.

---

## 6. Requisitos que el bloque 2 impone al modelo de datos (bloque 3)

Para soportar las preguntas del MVP, el esquema del bloque 3 debe permitir, como mínimo:

- Agregar eventos atómicos (tarjetas, penaltis) **por árbitro**, con posibilidad de **tasa por partido** → necesita el hecho "partidos dirigidos por árbitro".
- Agregar esos mismos eventos **por árbitro × equipo** (para el desglose de la ficha, P3) → la atribución jugador→equipo y árbitro→partido debe resolverse en el modelo.
- Filtrar cualquier agregación **por rango de jornadas** (P4) → la jornada debe ser dimensión consultable del partido.
- Calcular la **mediana de liga por métrica de volumen** (P5) → agregación a nivel liga sobre la temporada.
- Convivencia de los **dos granos** (eventos atómicos y métricas agregadas por partido-equipo: faltas, añadido) bajo el mismo árbitro y partido.
- Dejar viables, sin construirlos, el cruce árbitro×equipo en brutos (módulo inmediato) y las agregaciones por equipo entre árbitros.

---

*Fin del bloque 2. Siguiente: bloque 3 — modelo de datos (esquema completo en Supabase: tablas, columnas, tipos, claves, relaciones y capas bronze/silver/gold que soporten las preguntas P1–P6 sin cerrar la puerta a los módulos futuros).*
