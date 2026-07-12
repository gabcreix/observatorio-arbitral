"""CLI de ingesta — aterriza partidos en bronze.

Uso:
    python -m scraper.ingest --jornada 1                       # descubre y aterriza la jornada 1 (D32)
    python -m scraper.ingest --temporada --only-played         # backfill de toda la temporada (D3/D32)
    python -m scraper.ingest --temporada --dry-run             # ídem, sin tocar la base
    python -m scraper.ingest                                   # ingesta la lista curada en matches_sample.yml
    python -m scraper.ingest --file otra_muestra.yml
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from . import db
from .discover import DEFAULT_SEASON, discover_jornada, discover_season
from .extract import extract_json_blobs, pick_extraction_method
from .fetch import fetch

DEFAULT_MATCHES_FILE = Path(__file__).parent / "matches_sample.yml"
FUENTE = "laliga.com"


def _normalize_match(match) -> dict:
    """Acepta tanto '- url' (texto plano) como '- {slug, url}' en matches_sample.yml."""
    if isinstance(match, str):
        return {"slug": match, "url": match}
    return match


def load_matches(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text()) or {}
    raw = data.get("partidos") or []
    if isinstance(raw, dict):
        raise ValueError(
            f"'partidos:' en {path} salió como diccionario, no como lista de partidos. "
            "Seguramente falta el '- ' delante de cada partido: si repites 'url:' sin "
            "guion, YAML lo trata como la misma clave repetida y solo se queda con el "
            "último valor, perdiendo el resto en silencio. Cada partido debe ir así:\n"
            "  - slug: mi-slug\n    url: \"https://...\""
        )
    matches = [_normalize_match(m) for m in raw]
    for i, match in enumerate(matches, start=1):
        if not isinstance(match, dict) or not match.get("url"):
            raise ValueError(f"Partido #{i} en {path} no tiene 'url' válida: {match!r}")
    return matches


def _safe_filename(slug: str) -> str:
    """slug puede ser una URL completa si no se dio 'slug' explícito; lo saneamos
    para que sirva de nombre de fichero en cualquier SO (Windows incluido)."""
    return re.sub(r"[^A-Za-z0-9_-]+", "-", slug).strip("-")[:150]


class FetchResult:
    def __init__(self, slug, url, status, raw_html, payload_json, extraction_method, error):
        self.slug = slug
        self.url = url
        self.status = status
        self.raw_html = raw_html
        self.payload_json = payload_json
        self.extraction_method = extraction_method
        self.error = error


def fetch_and_extract(match: dict) -> FetchResult:
    url = match["url"]
    slug = match.get("slug") or url
    print(f"→ {slug}: GET {url}")
    try:
        response = fetch(url)
    except Exception as exc:  # red caída, DNS, timeout...
        print(f"  ! error de red: {exc}")
        return FetchResult(slug, url, None, None, None, None, str(exc))

    blobs = extract_json_blobs(response.text) if response.status_code == 200 else {}
    method = pick_extraction_method(blobs)
    print(f"  status={response.status_code} extraccion={method or 'ninguna'} bytes={len(response.text)}")
    return FetchResult(slug, url, response.status_code, response.text, blobs or None, method, None)


def ingest_one(match: dict, *, conn) -> None:
    result = fetch_and_extract(match)
    db.upsert_bronze(
        conn, fuente=FUENTE, natural_key=result.slug, source_url=result.url,
        http_status=result.status, raw_html=result.raw_html,
        payload_json=result.payload_json, extraction_method=result.extraction_method,
        error=result.error,
    )


def dry_run(matches: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for match in matches:
        result = fetch_and_extract(match)
        filename = _safe_filename(result.slug)
        if result.raw_html is not None:
            (output_dir / f"{filename}.html").write_text(result.raw_html, encoding="utf-8")
        if result.payload_json:
            (output_dir / f"{filename}.json").write_text(
                json.dumps(result.payload_json, ensure_ascii=False, indent=2), encoding="utf-8"
            )
    print(f"Volcado en {output_dir}/ (sin escribir en la base).")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_MATCHES_FILE,
                         help="Lista curada de partidos (ignorado si se usa --jornada/--temporada).")
    parser.add_argument("--jornada", type=int, help="Descubre los partidos de esta jornada (D30/D32), en vez de leer --file.")
    parser.add_argument("--temporada", action="store_true",
                         help="Descubre y aterriza TODAS las jornadas de la temporada (backfill completo, D3/D32).")
    parser.add_argument("--season", default=DEFAULT_SEASON)
    parser.add_argument("--only-played", action="store_true",
                         help="Con --jornada/--temporada: descarta partidos con status != FullTime.")
    parser.add_argument("--dry-run", action="store_true", help="No escribe en la base; vuelca HTML/JSON a --output-dir.")
    parser.add_argument("--output-dir", type=Path, default=Path("bronze_dryrun"))
    args = parser.parse_args(argv)

    if args.temporada:
        matches = discover_season(season=args.season, only_played=args.only_played)
        print(f"{len(matches)} partidos descubiertos para toda la temporada {args.season}.")
    elif args.jornada is not None:
        matches = discover_jornada(args.jornada, season=args.season)
        if args.only_played:
            matches = [m for m in matches if m["status"] == "FullTime"]
        print(f"{len(matches)} partidos descubiertos para la jornada {args.jornada} ({args.season}).")
    else:
        matches = load_matches(args.file)

    if not matches:
        print(f"No hay partidos que ingerir (jornada={args.jornada}, temporada={args.temporada}, file={args.file}).")
        sys.exit(1)

    if args.dry_run:
        dry_run(matches, args.output_dir)
        return

    conn = db.get_conn()
    db.ensure_bronze_table(conn)
    for match in matches:
        ingest_one(match, conn=conn)
    conn.close()


if __name__ == "__main__":
    main()
