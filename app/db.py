"""Conexión a Neon para la app (D33: st.connection, con caché por TTL en
cada .query() en vez de refresco manual). Reutiliza el .env de la raíz del
repo en local; en Streamlit Community Cloud (D34) usa st.secrets."""
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _database_url() -> str:
    try:
        url = st.secrets["DATABASE_URL"]
    except Exception:
        url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL no está definida (ni en .env de la raíz del repo, "
            "ni en .streamlit/secrets.toml)."
        )
    # SQLAlchemy interpreta "postgresql://" a secas como "usa psycopg2" (el
    # driver clásico). Instalamos psycopg (v3), así que hay que decírselo
    # explícito con el dialecto +psycopg — si no, falla con
    # ModuleNotFoundError: psycopg2 en cuanto se despliega donde no esté
    # instalado por casualidad.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


@st.cache_resource
def get_connection():
    return st.connection("neon", type="sql", url=_database_url())
