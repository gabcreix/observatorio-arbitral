-- Desanida comments[] (feed en prosa): una fila por comentario. D39 §3: sin
-- equipo/jugador estructurado, solo texto libre en 'content'.

with partidos as (
    select partido_natural_key, comments_json
    from {{ ref('stg_partido') }}
    where comments_json is not null
)

select
    p.partido_natural_key,
    (elem #>> '{match_comment_kind,id}')::int as kind_id,
    elem ->> 'content'                         as content,
    (elem ->> 'time')::int                    as time,
    elem ->> 'period'                         as period

from partidos p,
     lateral jsonb_array_elements(p.comments_json) as elem
