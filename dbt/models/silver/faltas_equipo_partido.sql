-- D9: faltas agregadas por equipo y partido. Decisión de esta sesión:
-- comments (kind=6, "Falta de X (Equipo)") no trae equipo estructurado.
-- Comprobado sobre las 9429 faltas de la temporada: el texto entre
-- paréntesis usa una TERCERA forma de nombre (ni nombre_canonico, ni
-- apodo/boundname/shortname — p.ej. "Getafe", "Celta de Vigo", "Barcelona"),
-- pero siempre es subcadena de nombre_canonico. Para evitar cualquier
-- ambigüedad (dos equipos cuyo nombre corto se solape) se resuelve contra
-- los DOS equipos ya conocidos de ESE partido, no contra los 20 de la liga.

with comentarios as (

    select
        partido_natural_key,
        substring(content from '\(([^)]+)\)') as equipo_texto
    from {{ ref('stg_comentario') }}
    where kind_id = 6

),

candidatos as (

    select
        c.partido_natural_key,
        p.partido_id,
        case
            when el.nombre_canonico ilike '%' || c.equipo_texto || '%' then p.equipo_local_id
            when ev.nombre_canonico ilike '%' || c.equipo_texto || '%' then p.equipo_visitante_id
        end as equipo_id
    from comentarios c
    join {{ ref('partido') }} p on p.slug = c.partido_natural_key
    join {{ ref('equipo') }} el on el.equipo_id = p.equipo_local_id
    join {{ ref('equipo') }} ev on ev.equipo_id = p.equipo_visitante_id

)

select
    partido_id,
    equipo_id,
    count(*) as n_faltas
from candidatos
where equipo_id is not null
group by partido_id, equipo_id
