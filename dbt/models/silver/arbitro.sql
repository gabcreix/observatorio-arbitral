-- D16: PK surrogate + nombre_canonico UNIQUE (D25: conjunto ~20/temporada,
-- verificable a mano). Une principal y VAR en la misma tabla — D2/D11 tratan
-- a cualquier árbitro como la misma entidad, sea cual sea su rol en un
-- partido concreto.

with nombres as (

    select arbitro_principal_nombre as nombre from {{ ref('stg_partido') }}
    union
    select arbitro_var_nombre from {{ ref('stg_partido') }}

)

select
    md5(nombre) as arbitro_id,
    nombre       as nombre_canonico
from nombres
where nombre is not null
