-- Grano partido (bloque 3 §5): reúne las cuatro fuentes de hechos por
-- partido — composición, no analítica. Útil para depurar y para la futura
-- página de metodología (D37).

select
    p.partido_id,
    p.slug,
    p.jornada,
    p.fecha,
    p.arbitro_principal_id,
    (select count(*) from {{ ref('tarjeta') }} t where t.partido_id = p.partido_id)   as n_tarjetas,
    (select count(*) from {{ ref('penalti') }} pe where pe.partido_id = p.partido_id) as n_penaltis,
    (select sum(f.n_faltas) from {{ ref('faltas_equipo_partido') }} f where f.partido_id = p.partido_id) as n_faltas,
    a.minutos_primera,
    a.minutos_segunda,
    (select count(*) from {{ ref('evento_var') }} v where v.partido_id = p.partido_id) as n_eventos_var
from {{ ref('partido') }} p
left join {{ ref('anadido_partido') }} a on a.partido_id = p.partido_id
