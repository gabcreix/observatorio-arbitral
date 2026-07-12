-- D7: señalamiento atómico (a favor / en contra / minuto), sin resultado del
-- lanzamiento. D39 §4/§2: "señalado" = union de Penalty (transformado,
-- collection=goal, kind=2) y missedPenalty (fallado/poste/parado, kinds
-- 4/5/6) — deliberadamente NO se guarda cuál de los dos fue, por D7.
-- equipo_en_contra se deriva como "el otro equipo del partido", porque el
-- evento solo trae el equipo que lanza.

with penaltis_evento as (

    select
        e.partido_natural_key,
        e.laliga_event_id,
        e.equipo_laliga_id,
        e.minuto,
        e.clock
    from {{ ref('stg_evento') }} e
    where (e.kind_collection = 'goal' and e.kind_id = 2)
       or (e.kind_collection = 'missedPenalty' and e.kind_id in (4, 5, 6))

)

select
    md5(pe.laliga_event_id::text) as penalti_id,
    pe.laliga_event_id,
    p.partido_id,
    eq_favor.equipo_id as equipo_a_favor_id,
    case when p.equipo_local_id = eq_favor.equipo_id
         then p.equipo_visitante_id
         else p.equipo_local_id
    end as equipo_en_contra_id,
    pe.minuto,
    (pe.clock like '%+%') as es_tiempo_anadido
from penaltis_evento pe
join {{ ref('partido') }} p on p.slug = pe.partido_natural_key
join {{ ref('equipo') }} eq_favor on eq_favor.equipo_laliga_id = pe.equipo_laliga_id
