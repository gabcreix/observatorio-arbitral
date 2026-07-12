-- P3 (bloque 2): desglose por equipo dentro de la ficha, en conteos brutos
-- (D2, D14) — sin analizador de sesgo, solo agregación descriptiva.
-- Penalti cuenta en ambos lados (D2, bloque 3 §6): el equipo que lo lanza
-- (a_favor) y el que lo comete (en_contra) son ambos hechos legítimos sobre
-- ese equipo bajo ese árbitro.

with tarjetas as (

    select
        p.arbitro_principal_id as arbitro_id,
        t.equipo_id,
        count(*) filter (where t.tipo = 'amarilla')         as total_amarillas,
        count(*) filter (where t.tipo = 'segunda_amarilla')  as total_segundas_amarillas,
        count(*) filter (where t.tipo = 'roja_directa')      as total_rojas_directas
    from {{ ref('tarjeta') }} t
    join {{ ref('partido') }} p on p.partido_id = t.partido_id
    where p.arbitro_principal_id is not null and t.equipo_id is not null
    group by p.arbitro_principal_id, t.equipo_id

),

penaltis_favor as (

    select p.arbitro_principal_id as arbitro_id, pe.equipo_a_favor_id as equipo_id, count(*) as total_penaltis_a_favor
    from {{ ref('penalti') }} pe
    join {{ ref('partido') }} p on p.partido_id = pe.partido_id
    where p.arbitro_principal_id is not null
    group by p.arbitro_principal_id, pe.equipo_a_favor_id

),

penaltis_contra as (

    select p.arbitro_principal_id as arbitro_id, pe.equipo_en_contra_id as equipo_id, count(*) as total_penaltis_en_contra
    from {{ ref('penalti') }} pe
    join {{ ref('partido') }} p on p.partido_id = pe.partido_id
    where p.arbitro_principal_id is not null
    group by p.arbitro_principal_id, pe.equipo_en_contra_id

),

faltas as (

    select p.arbitro_principal_id as arbitro_id, f.equipo_id, sum(f.n_faltas) as total_faltas
    from {{ ref('faltas_equipo_partido') }} f
    join {{ ref('partido') }} p on p.partido_id = f.partido_id
    where p.arbitro_principal_id is not null
    group by p.arbitro_principal_id, f.equipo_id

),

claves as (

    select arbitro_id, equipo_id from tarjetas
    union
    select arbitro_id, equipo_id from penaltis_favor
    union
    select arbitro_id, equipo_id from penaltis_contra
    union
    select arbitro_id, equipo_id from faltas

)

select
    c.arbitro_id,
    c.equipo_id,
    coalesce(t.total_amarillas, 0)          as total_amarillas,
    coalesce(t.total_segundas_amarillas, 0)  as total_segundas_amarillas,
    coalesce(t.total_rojas_directas, 0)      as total_rojas_directas,
    coalesce(pf.total_penaltis_a_favor, 0)   as total_penaltis_a_favor,
    coalesce(pc.total_penaltis_en_contra, 0) as total_penaltis_en_contra,
    coalesce(fa.total_faltas, 0)             as total_faltas
from claves c
left join tarjetas t         on t.arbitro_id = c.arbitro_id  and t.equipo_id = c.equipo_id
left join penaltis_favor pf  on pf.arbitro_id = c.arbitro_id and pf.equipo_id = c.equipo_id
left join penaltis_contra pc on pc.arbitro_id = c.arbitro_id and pc.equipo_id = c.equipo_id
left join faltas fa          on fa.arbitro_id = c.arbitro_id and fa.equipo_id = c.equipo_id
