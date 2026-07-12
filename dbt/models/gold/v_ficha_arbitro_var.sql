-- P2/P7 (bloque 2 §2.2, anexo VAR): sección "Actividad VAR" de la ficha.
-- Desglose por tipo_decision_revisada, con las confirmaciones como
-- contexto de segundo nivel (D35: no ranqueadas, solo modifica cuenta en
-- el ranking) pero visibles aquí para dar el cuadro completo.

select
    arbitro_principal_id as arbitro_id,
    tipo_decision_revisada,
    count(*) filter (where resultado = 'modifica') as total_modifica,
    count(*) filter (where resultado = 'confirma') as total_confirma
from {{ ref('evento_var') }}
where arbitro_principal_id is not null
group by arbitro_principal_id, tipo_decision_revisada
