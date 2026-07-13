-- D19: una fila por equipo y partido. Test singular (ver
-- partido_clave_natural_unica.sql para la explicación del patrón).

select partido_id, equipo_id, count(*)
from {{ ref('faltas_equipo_partido') }}
group by 1, 2
having count(*) > 1
