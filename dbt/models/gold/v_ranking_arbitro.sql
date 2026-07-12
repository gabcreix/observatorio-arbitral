-- P1/P2/P6 (bloque 2): ranking de árbitros. D12: tasa por partido como base
-- de comparabilidad, con total bruto y partidos_dirigidos (denominador)
-- siempre visibles. D15: mediana de liga SOLO en amarillas y faltas
-- (métricas de volumen) — nada en rojas y penaltis, para no fabricar señal
-- donde una temporada sola es ruido. Añade decisiones_var_con_impacto
-- (anexo VAR, D35): solo cuenta evento_var.resultado = 'modifica'.

with partidos_dirigidos as (

    select arbitro_principal_id as arbitro_id, count(*) as partidos_dirigidos
    from {{ ref('partido') }}
    where arbitro_principal_id is not null
    group by arbitro_principal_id

),

tarjetas as (

    select
        p.arbitro_principal_id as arbitro_id,
        count(*) filter (where t.tipo = 'amarilla')         as total_amarillas,
        count(*) filter (where t.tipo = 'segunda_amarilla')  as total_segundas_amarillas,
        count(*) filter (where t.tipo = 'roja_directa')      as total_rojas_directas
    from {{ ref('tarjeta') }} t
    join {{ ref('partido') }} p on p.partido_id = t.partido_id
    where p.arbitro_principal_id is not null
    group by p.arbitro_principal_id

),

penaltis as (

    select p.arbitro_principal_id as arbitro_id, count(*) as total_penaltis
    from {{ ref('penalti') }} pe
    join {{ ref('partido') }} p on p.partido_id = pe.partido_id
    where p.arbitro_principal_id is not null
    group by p.arbitro_principal_id

),

faltas as (

    select p.arbitro_principal_id as arbitro_id, sum(f.n_faltas) as total_faltas
    from {{ ref('faltas_equipo_partido') }} f
    join {{ ref('partido') }} p on p.partido_id = f.partido_id
    where p.arbitro_principal_id is not null
    group by p.arbitro_principal_id

),

anadido as (

    select
        p.arbitro_principal_id as arbitro_id,
        avg(coalesce(a.minutos_primera, 0) + coalesce(a.minutos_segunda, 0)) as promedio_anadido_partido
    from {{ ref('anadido_partido') }} a
    join {{ ref('partido') }} p on p.partido_id = a.partido_id
    where p.arbitro_principal_id is not null
    group by p.arbitro_principal_id

),

var_impacto as (

    select arbitro_principal_id as arbitro_id, count(*) as total_var_impacto
    from {{ ref('evento_var') }}
    where resultado = 'modifica' and arbitro_principal_id is not null
    group by arbitro_principal_id

),

base as (

    select
        ar.arbitro_id,
        ar.nombre_canonico,
        pd.partidos_dirigidos,
        coalesce(t.total_amarillas, 0)         as total_amarillas,
        coalesce(t.total_segundas_amarillas, 0) as total_segundas_amarillas,
        coalesce(t.total_rojas_directas, 0)    as total_rojas_directas,
        coalesce(pe.total_penaltis, 0)          as total_penaltis,
        coalesce(fa.total_faltas, 0)            as total_faltas,
        an.promedio_anadido_partido,
        coalesce(v.total_var_impacto, 0)        as decisiones_var_con_impacto
    from (select distinct arbitro_id, nombre_canonico from {{ ref('arbitro') }}) ar
    join partidos_dirigidos pd on pd.arbitro_id = ar.arbitro_id
    left join tarjetas t   on t.arbitro_id = ar.arbitro_id
    left join penaltis pe  on pe.arbitro_id = ar.arbitro_id
    left join faltas fa    on fa.arbitro_id = ar.arbitro_id
    left join anadido an   on an.arbitro_id = ar.arbitro_id
    left join var_impacto v on v.arbitro_id = ar.arbitro_id

)

select
    b.*,
    round(b.total_amarillas::numeric / b.partidos_dirigidos, 2)          as tasa_amarillas,
    round(b.total_segundas_amarillas::numeric / b.partidos_dirigidos, 2) as tasa_segundas_amarillas,
    round(b.total_rojas_directas::numeric / b.partidos_dirigidos, 2)     as tasa_rojas_directas,
    round(b.total_penaltis::numeric / b.partidos_dirigidos, 2)           as tasa_penaltis,
    round(b.total_faltas::numeric / b.partidos_dirigidos, 2)             as tasa_faltas,
    round(b.decisiones_var_con_impacto::numeric / b.partidos_dirigidos, 2) as tasa_var_con_impacto,
    (select round(percentile_cont(0.5) within group (order by total_amarillas::numeric / partidos_dirigidos)::numeric, 2) from base) as mediana_liga_tasa_amarillas,
    (select round(percentile_cont(0.5) within group (order by total_faltas::numeric / partidos_dirigidos)::numeric, 2) from base)    as mediana_liga_tasa_faltas
from base b
