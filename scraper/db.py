"""Escritura en bronze (D27 — el scraper solo escribe bronze, nunca transforma)."""
import os
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

_SQL_DIR = Path(__file__).parent / "sql"


def get_conn() -> psycopg.Connection:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError(
            "DATABASE_URL no está definida. Exporta la cadena de conexión de Neon "
            "(ver .env.example) antes de ingerir."
        )
    return psycopg.connect(dsn)


def ensure_bronze_table(conn: psycopg.Connection) -> None:
    ddl = (_SQL_DIR / "001_create_bronze.sql").read_text()
    conn.execute(ddl)
    conn.commit()


def upsert_bronze(
    conn: psycopg.Connection,
    *,
    fuente: str,
    natural_key: str,
    source_url: str,
    http_status: int | None,
    raw_html: str | None,
    payload_json: dict | None,
    extraction_method: str | None,
    error: str | None,
) -> None:
    conn.execute(
        """
        insert into bronze (
            fuente, partido_natural_key, source_url, http_status,
            raw_html, payload_json, extraction_method, error, fetched_at
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s, now())
        on conflict (fuente, partido_natural_key) do update set
            source_url = excluded.source_url,
            http_status = excluded.http_status,
            raw_html = excluded.raw_html,
            payload_json = excluded.payload_json,
            extraction_method = excluded.extraction_method,
            error = excluded.error,
            fetched_at = excluded.fetched_at
        """,
        (
            fuente,
            natural_key,
            source_url,
            http_status,
            raw_html,
            Jsonb(payload_json) if payload_json is not None else None,
            extraction_method,
            error,
        ),
    )
    conn.commit()
