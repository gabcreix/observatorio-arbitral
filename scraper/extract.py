"""Extracción del JSON embebido en el HTML de LaLiga.com (D30).

Scraper "tonto" (D18): no se asume de antemano cuál es el bloque de JSON
"bueno" — se capturan TODOS los <script> con JSON parseable y se guardan
verbatim en bronze. La elección de cuál es el feed relevante se hace en el
análisis exploratorio de D39, no aquí.
"""
import json

from bs4 import BeautifulSoup


def extract_json_blobs(html: str) -> dict:
    """Devuelve un dict con todos los bloques JSON encontrados en <script>.

    - "next_data": contenido de <script id="__NEXT_DATA__"> si existe y parsea.
    - "other_json_scripts": lista con el resto de <script type="application/json">
      que parseen como JSON válido.
    """
    soup = BeautifulSoup(html, "lxml")
    blobs: dict = {}

    next_data_tag = soup.find("script", id="__NEXT_DATA__")
    if next_data_tag and next_data_tag.string:
        try:
            blobs["next_data"] = json.loads(next_data_tag.string)
        except json.JSONDecodeError:
            pass

    other = []
    for tag in soup.find_all("script", type="application/json"):
        if tag is next_data_tag or not tag.string:
            continue
        try:
            other.append(json.loads(tag.string))
        except json.JSONDecodeError:
            continue
    if other:
        blobs["other_json_scripts"] = other

    return blobs


def pick_extraction_method(blobs: dict) -> str | None:
    if "next_data" in blobs:
        return "next_data"
    if blobs.get("other_json_scripts"):
        return "other_json_scripts"
    return None
