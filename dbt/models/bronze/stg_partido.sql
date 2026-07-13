-- Un "modelo" dbt es, en su forma más simple, un SELECT guardado en un
-- fichero .sql; dbt lo materializa como vista o tabla según dbt_project.yml.
-- Este es el primero: saca de bronze.raw_partido los campos escalares de
-- cada partido (equipos, jornada, temporada, designación arbitral) y deja
-- los arrays (events, comments) sin desanidar todavía — eso lo hacen
-- stg_evento y stg_comentario, que referencian este modelo (función ref,
-- entre dobles llaves) en vez de volver a leer bronze.

with base as (

    select
        partido_natural_key,
        payload_json #> '{next_data,props,pageProps,match}'                as match_json,
        payload_json #> '{next_data,props,pageProps,events}'               as events_json,
        payload_json #> '{next_data,props,pageProps,data,comments}'        as comments_json,
        fetched_at

    from {{ source('bronze', 'raw_partido') }}
    where payload_json is not null

),

roles as (

    -- persons_role[] trae el cuadro arbitral entero; solo nos hace falta el
    -- principal (role.id=5) y el VAR (role.id=9) — D20/D25/D36.
    select
        b.partido_natural_key,
        max(elem #>> '{person,name}') filter (where (elem #>> '{role,id}')::int = 5) as arbitro_principal_nombre,
        max(elem #>> '{person,name}') filter (where (elem #>> '{role,id}')::int = 9) as arbitro_var_nombre
    from base b,
         lateral jsonb_array_elements(b.match_json -> 'persons_role') as elem
    group by b.partido_natural_key

)

select
    b.partido_natural_key,
    b.events_json,
    b.comments_json,
    b.fetched_at,

    (b.match_json ->> 'id')::bigint                  as laliga_match_id,
    b.match_json ->> 'slug'                          as slug,
    (b.match_json ->> 'date')::timestamptz            as fecha,
    b.match_json ->> 'status'                        as status,
    (b.match_json #>> '{gameweek,week}')::smallint    as jornada,

    b.match_json #>> '{season,opta_id}'              as temporada_opta_id,

    (b.match_json #>> '{home_team,id}')::bigint      as equipo_local_laliga_id,
    b.match_json #>> '{home_team,name}'              as equipo_local_nombre,
    b.match_json #>> '{home_team,nickname}'          as equipo_local_apodo,
    b.match_json #>> '{home_team,boundname}'         as equipo_local_boundname,
    b.match_json #>> '{home_team,shortname}'         as equipo_local_shortname,

    (b.match_json #>> '{away_team,id}')::bigint      as equipo_visitante_laliga_id,
    b.match_json #>> '{away_team,name}'              as equipo_visitante_nombre,
    b.match_json #>> '{away_team,nickname}'          as equipo_visitante_apodo,
    b.match_json #>> '{away_team,boundname}'         as equipo_visitante_boundname,
    b.match_json #>> '{away_team,shortname}'         as equipo_visitante_shortname,

    r.arbitro_principal_nombre,
    r.arbitro_var_nombre

from base b
left join roles r using (partido_natural_key)
