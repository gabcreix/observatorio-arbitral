-- D20: dimensión partido con designación. Clave natural real
-- (temporada_id, jornada, equipo_local_id, equipo_visitante_id) — testeada
-- en schema.yml, no como constraint de Postgres (D16: bronze/silver via
-- dbt tests, no DDL constraints a mano).
-- slug se guarda además como columna de trazabilidad hacia bronze (no es
-- parte de la clave natural de D20, es solo para depurar).

select
    md5(sp.partido_natural_key) as partido_id,
    t.temporada_id,
    sp.jornada,
    sp.fecha::date               as fecha,
    el.equipo_id                 as equipo_local_id,
    ev.equipo_id                 as equipo_visitante_id,
    ar.arbitro_id                as arbitro_principal_id,
    sp.partido_natural_key       as slug
from {{ ref('stg_partido') }} sp
left join {{ ref('temporada') }} t  on t.temporada_id = md5(sp.temporada_opta_id)
left join {{ ref('equipo') }} el    on el.equipo_laliga_id = sp.equipo_local_laliga_id
left join {{ ref('equipo') }} ev    on ev.equipo_laliga_id = sp.equipo_visitante_laliga_id
left join {{ ref('arbitro') }} ar   on ar.nombre_canonico = sp.arbitro_principal_nombre
