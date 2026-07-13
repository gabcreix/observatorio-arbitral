-- D17: "todos los eventos del árbitro X" vía UNION de tarjeta + penalti +
-- evento_var, normalizados a (arbitro_id, temporada_id, partido_id,
-- tipo_evento, minuto, equipo_id). Ampliado por el anexo VAR:
-- var_modifica/var_confirma entran al UNION con su propia semántica.
-- temporada_id se pasa siempre (vía partido, o directo en evento_var) para
-- poder filtrar por temporada sin volver a tocar esta vista (D23/D3).

select
    p.arbitro_principal_id as arbitro_id,
    p.temporada_id,
    t.partido_id,
    t.tipo as tipo_evento,
    t.minuto,
    t.equipo_id
from {{ ref('tarjeta') }} t
join {{ ref('partido') }} p on p.partido_id = t.partido_id
where p.arbitro_principal_id is not null

union all

select
    p.arbitro_principal_id as arbitro_id,
    p.temporada_id,
    pe.partido_id,
    'penalti' as tipo_evento,
    pe.minuto,
    pe.equipo_a_favor_id as equipo_id
from {{ ref('penalti') }} pe
join {{ ref('partido') }} p on p.partido_id = pe.partido_id
where p.arbitro_principal_id is not null

union all

select
    ev.arbitro_principal_id as arbitro_id,
    p.temporada_id,
    ev.partido_id,
    'var_' || ev.resultado as tipo_evento,
    ev.minuto,
    null as equipo_id
from {{ ref('evento_var') }} ev
join {{ ref('partido') }} p on p.partido_id = ev.partido_id
where ev.arbitro_principal_id is not null
