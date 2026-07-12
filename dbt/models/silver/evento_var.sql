-- D35/D36/D38 + D39 §2: el VAR vive estructurado en events[] (collection=var),
-- mejor fuente que la prosa de comments. Mapeo de match_event_kind a
-- tipo_decision_revisada y de decision a resultado, según lo verificado en
-- docs/d39-anatomia-feed.md:
--   15 Goal awarded / 16 Goal not awarded          -> gol
--   17 Penalty awarded / 18 Penalty not awarded    -> penalti
--   19 Red card given / 20 Card upgrade / 21 Mistaken Identity -> tarjeta
--   decision confirmed -> confirma ; decision cancelled -> modifica
-- Atribución doble (D36): arbitro_principal_id ya resuelto en partido;
-- arbitro_var_id se resuelve aquí porque partido no lo expone (D38: la
-- superficie del MVP solo usa el principal).

with mapped as (

    select
        e.partido_natural_key,
        e.laliga_event_id,
        e.minuto,
        case
            when e.kind_id in (15, 16)     then 'gol'
            when e.kind_id in (17, 18)     then 'penalti'
            when e.kind_id in (19, 20, 21) then 'tarjeta'
        end as tipo_decision_revisada,
        case e.decision
            when 'confirmed' then 'confirma'
            when 'cancelled' then 'modifica'
        end as resultado
    from {{ ref('stg_evento') }} e
    where e.kind_collection = 'var'

)

select
    md5(m.laliga_event_id::text) as evento_var_id,
    m.laliga_event_id,
    p.partido_id,
    p.arbitro_principal_id,
    ar_var.arbitro_id as arbitro_var_id,
    m.minuto,
    m.tipo_decision_revisada,
    m.resultado
from mapped m
join {{ ref('partido') }} p on p.slug = m.partido_natural_key
left join {{ ref('stg_partido') }} sp on sp.partido_natural_key = m.partido_natural_key
left join {{ ref('arbitro') }} ar_var on ar_var.nombre_canonico = sp.arbitro_var_nombre
