"""Envuelve `dbt` cargando el .env de la raíz del repo primero.

Evita depender del CLI `dotenv` (necesita el extra [cli] instalado, y en
Windows el ejecutable no siempre cae en el PATH) — esto solo necesita
`python`, que ya tienes.

Uso (desde la carpeta dbt/):
    python run.py build
    python run.py run --select tarjeta
    python run.py test
"""
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")

cmd = ["dbt", *sys.argv[1:], "--profiles-dir", str(HERE)]
sys.exit(subprocess.call(cmd))
