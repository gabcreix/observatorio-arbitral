-- Test "singular": un SQL suelto que falla si devuelve alguna fila. Aquí
-- comprueba la clave natural de D20 (temporada_id, jornada, local,
-- visitante) sin necesidad del paquete dbt_utils para una unicidad
-- compuesta.

select temporada_id, jornada, equipo_local_id, equipo_visitante_id, count(*)
from {{ ref('partido') }}
group by 1, 2, 3, 4
having count(*) > 1
