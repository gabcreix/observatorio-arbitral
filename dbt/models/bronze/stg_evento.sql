-- Desanida events[] (feed tipado Opta): una fila por evento (gol, tarjeta,
-- sustitución, VAR...). D39 §2: atribución limpia vía lineup.team/person.

with partidos as (
    select partido_natural_key, events_json
    from {{ ref('stg_partido') }}
    where events_json is not null
)

select
    p.partido_natural_key,
    (elem ->> 'id')::bigint                       as laliga_event_id,
    (elem #>> '{match_event_kind,id}')::int       as kind_id,
    elem #>> '{match_event_kind,name}'            as kind_name,
    elem #>> '{match_event_kind,collection}'      as kind_collection,
    (elem #>> '{lineup,team,id}')::bigint         as equipo_laliga_id,
    elem #>> '{lineup,person,name}'               as jugador_nombre,
    -- D39: 'minute' viene null en ~0.8% de los eventos aunque 'clock' sí
    -- está poblado ("90+7"); se recupera el minuto base de ahí antes de
    -- rendirse a NULL.
    coalesce((elem ->> 'minute')::int, split_part(elem ->> 'clock', '+', 1)::int) as minuto,
    elem ->> 'clock'                              as clock,
    elem ->> 'period'                             as period,
    elem ->> 'decision'                           as decision

from partidos p,
     lateral jsonb_array_elements(p.events_json) as elem
