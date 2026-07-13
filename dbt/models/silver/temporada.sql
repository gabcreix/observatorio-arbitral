-- D23: temporada como dimensión propia. fecha_inicio/fecha_fin y n_jornadas
-- se derivan de los propios partidos de bronze (min/max fecha, nº de
-- jornadas distintas vistas) en vez de venir de un seed a mano — así
-- multi-temporada (D23, puerta futura) es solo "aparecen más filas", sin
-- mantenimiento manual.

select
    md5(temporada_opta_id)  as temporada_id,
    -- "2025" (opta_id) -> "2025-26" (misma forma que usa scraper.discover)
    temporada_opta_id || '-' || lpad(((temporada_opta_id::int + 1) % 100)::text, 2, '0') as etiqueta,
    min(fecha)::date        as fecha_inicio,
    max(fecha)::date        as fecha_fin,
    count(distinct jornada) as n_jornadas
from {{ ref('stg_partido') }}
where temporada_opta_id is not null
group by temporada_opta_id
