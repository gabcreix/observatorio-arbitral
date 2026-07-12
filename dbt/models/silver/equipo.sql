-- D16: PK surrogate opaca (aquí, hash md5 de la clave natural — alternativa
-- equivalente al bigint de identidad, igual que dbt trata un UUID) +
-- nombre_canonico como UNIQUE natural (testeado en schema.yml).
-- apodo/boundname/shortname alimentan la resolución de equipo en texto
-- libre de D9 (faltas) sin necesidad de un seed de alias a mano.

with equipos as (

    select
        equipo_local_laliga_id     as laliga_id,
        equipo_local_nombre        as nombre,
        equipo_local_apodo         as apodo,
        equipo_local_boundname     as boundname,
        equipo_local_shortname     as shortname
    from {{ ref('stg_partido') }}

    union all

    select
        equipo_visitante_laliga_id,
        equipo_visitante_nombre,
        equipo_visitante_apodo,
        equipo_visitante_boundname,
        equipo_visitante_shortname
    from {{ ref('stg_partido') }}

)

select
    md5(laliga_id::text) as equipo_id,
    laliga_id             as equipo_laliga_id,
    max(nombre)           as nombre_canonico,
    max(apodo)            as apodo,
    max(boundname)        as boundname,
    max(shortname)        as shortname
from equipos
where laliga_id is not null
group by laliga_id
