-- D28: tabla bronze en Neon, una fila por partido, payload crudo + metadatos de procedencia.
-- D16 exime a bronze de PK surrogate/UNIQUE natural: aquí la UNIQUE es una guarda de
-- idempotencia de ingesta, no la estrategia de claves de silver.
create table if not exists bronze (
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
