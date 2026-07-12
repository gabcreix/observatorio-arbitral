-- D10: añadido anunciado por mitad. D39 §3: viene como texto libre en
-- comments (kind=31, "El cuarto árbitro ha anunciado N minutos..."), no como
-- campo numérico — se extrae el entero con una expresión regular.

with comentarios as (

    select
        partido_natural_key,
        period,
        (substring(content from '(\d+)\s+minutos?'))::int as minutos
    from {{ ref('stg_comentario') }}
    where kind_id = 31

)

select
    p.partido_id,
    max(c.minutos) filter (where c.period = 'FirstHalf')  as minutos_primera,
    max(c.minutos) filter (where c.period = 'SecondHalf') as minutos_segunda
from comentarios c
join {{ ref('partido') }} p on p.slug = c.partido_natural_key
group by p.partido_id
