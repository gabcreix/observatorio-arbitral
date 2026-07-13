-- P2/P7 (bloque 2 §2.2, anexo VAR): sección "Actividad VAR" de la ficha.
-- Desglose por tipo_decision_revisada, con las confirmaciones como
-- contexto de segundo nivel (D35: no ranqueadas, solo modifica cuenta en
-- el ranking) pero visibles aquí para dar el cuadro completo.
--
-- Grano: árbitro × temporada × tipo_decision_revisada (D23/D3 — ver
-- v_ranking_arbitro). evento_var no trae temporada_id directo, se resuelve
-- vía partido.

select
    p.arbitro_principal_id as arbitro_id,
    p.temporada_id,
    v.tipo_decision_revisada,
    count(*) filter (where v.resultado = 'modifica') as total_modifica,
    count(*) filter (where v.resultado = 'confirma') as total_confirma
from {{ ref('evento_var') }} v
join {{ ref('partido') }} p on p.partido_id = v.partido_id
where p.arbitro_principal_id is not null
group by p.arbitro_principal_id, p.temporada_id, v.tipo_decision_revisada
