-- D5 tipología (amarilla/segunda_amarilla/roja_directa), D6 solo jugadores,
-- D8 minuto siempre, D18 atribución a equipo denormalizada.
-- D8/D17 (decisión de esta sesión): minuto = base sin descuento;
-- es_tiempo_anadido = true si el 'clock' trae formato "90+N".

-- D39 (hallazgo positivo): cada evento trae su propio id de Opta
-- (laliga_event_id), una clave natural real y mejor que la tupla
-- (partido, jugador, tipo, minuto) que proponía D17 — esa tupla colisiona
-- de verdad cuando dos jugadores distintos ven la misma tarjeta en el mismo
-- minuto (verificado sobre la temporada completa).

with mapped as (

    select
        e.partido_natural_key,
        e.laliga_event_id,
        e.equipo_laliga_id,
        e.jugador_nombre,
        e.minuto,
        e.clock,
        case e.kind_id
            when 10 then 'amarilla'
            when 11 then 'segunda_amarilla'
            when 12 then 'roja_directa'
        end as tipo
    from {{ ref('stg_evento') }} e
    where e.kind_id in (10, 11, 12)

)

select
    md5(m.laliga_event_id::text) as tarjeta_id,
    m.laliga_event_id,
    p.partido_id,
    j.jugador_id,
    eq.equipo_id,
    m.tipo,
    m.minuto,
    (m.clock like '%+%') as es_tiempo_anadido
from mapped m
join {{ ref('partido') }} p on p.slug = m.partido_natural_key
left join {{ ref('jugador') }} j on j.jugador_id = md5(m.jugador_nombre)
left join {{ ref('equipo') }} eq on eq.equipo_laliga_id = m.equipo_laliga_id
