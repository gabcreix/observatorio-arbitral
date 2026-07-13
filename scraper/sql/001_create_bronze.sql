-- D28: tabla bronze en Neon, una fila por partido, payload crudo + metadatos de procedencia.
-- Schema propio "bronze" (simétrico con "silver"/"gold" que vendrán vía dbt);
-- la tabla se llama raw_partido para no repetir el nombre del schema.
-- D16 exime a bronze de PK surrogate/UNIQUE natural: aquí la UNIQUE es una guarda de
-- idempotencia de ingesta, no la estrategia de claves de silver.
create schema if not exists bronze;

create table if not exists bronze.raw_partido (
    id bigint generated always as identity primary key,
    fuente text not null default 'laliga.com',
    partido_natural_key text not null,
    source_url text not null,
    fetched_at timestamptz not null default now(),
    http_status int,
    raw_html text,
    payload_json jsonb,
    extraction_method text,
    error text,
    unique (fuente, partido_natural_key)
);
