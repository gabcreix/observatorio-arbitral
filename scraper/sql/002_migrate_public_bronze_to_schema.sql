-- Migración de UNA SOLA VEZ, manual: mueve la tabla bronze creada antes de
-- decidir el schema propio (vivía en "public") a su sitio definitivo
-- "bronze.raw_partido", sin perder las filas ya ingeridas.
--
-- Cómo correrla: pégala en el SQL Editor de la consola de Neon (o con psql)
-- UNA vez. Después de correrla, scraper/db.py ya no la necesita — el
-- ensure_bronze_table() normal (001_create_bronze.sql) encontrará la tabla
-- ya en su sitio y no hará nada (CREATE TABLE IF NOT EXISTS).
--
-- Es un no-op seguro si ya la corriste antes o si nunca tuviste la tabla
-- vieja en "public" (los IF EXISTS / IF NOT EXISTS cubren ambos casos).

create schema if not exists bronze;

do $$
begin
    if exists (
        select 1 from information_schema.tables
        where table_schema = 'public' and table_name = 'bronze'
    ) then
        alter table public.bronze set schema bronze;
        alter table bronze.bronze rename to raw_partido;
    end if;
end $$;
