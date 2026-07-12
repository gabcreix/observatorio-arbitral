-- D18: jugador ligero, no load-bearing — solo nombre_canonico, sin
-- reconciliación de identidad todavía (puerta abierta a futuro).

select
    md5(jugador_nombre) as jugador_id,
    jugador_nombre       as nombre_canonico
from {{ ref('stg_evento') }}
where jugador_nombre is not null
group by jugador_nombre
