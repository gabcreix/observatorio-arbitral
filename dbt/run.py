"""Envuelve `dbt` cargando el .env de la raíz del repo primero.

Llama a dbt EN PROCESO (import directo, no subprocess) para no depender de
que el ejecutable `dbt` esté en el PATH del sistema — en Windows, sobre
todo con el Python de la Microsoft Store, el Scripts/ de pip no siempre
cae ahí.

Uso (desde la carpeta dbt/):
    python run.py build
    python run.py run --select tarjeta
    python run.py test
"""
import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")

from dbt.cli.main import cli  # noqa: E402 (después de cargar el .env a propósito)

cli.main(args=[*sys.argv[1:], "--profiles-dir", str(HERE)])
