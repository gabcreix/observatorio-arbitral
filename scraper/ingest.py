"""CLI de ingesta — aterriza la muestra de D39 en bronze.

Uso:
    python -m scraper.ingest                          # ingesta real contra Neon
    python -m scraper.ingest --dry-run                 # sin tocar la base; vuelca a disco
    python -m scraper.ingest --file otra_muestra.yml
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from . import db
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
    return [_normalize_match(m) for m in (data.get("partidos") or [])]


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
    parser.add_argument("--file", type=Path, default=DEFAULT_MATCHES_FILE)
    parser.add_argument("--dry-run", action="store_true", help="No escribe en la base; vuelca HTML/JSON a --output-dir.")
    parser.add_argument("--output-dir", type=Path, default=Path("bronze_dryrun"))
    args = parser.parse_args(argv)

    matches = load_matches(args.file)
    if not matches:
        print(f"No hay partidos en {args.file}. Rellénalo con URLs reales (ver D39: jornada + expulsión/penalti/VAR).")
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
