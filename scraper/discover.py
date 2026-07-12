"""Descubrimiento de partidos por jornada.

Resuelve el hueco que D30 no cerraba: D30 dice cómo leer UNA página de
partido ya conocida, pero nadie decidía cómo averiguar qué partidos existen
para una jornada dada. La página de resultados de LaLiga.com trae la misma
técnica ya decidida (HTTP + JSON embebido en __NEXT_DATA__), así que no es
una decisión nueva de arquitectura — es la misma aplicada a otra página.

Formato de URL confirmado a mano (ver docs/d39-anatomia-feed.md):
    https://www.laliga.com/laliga-easports/resultados/{season}/jornada-{week}
"""
import argparse
from pathlib import Path

import yaml

from .extract import extract_json_blobs
from .fetch import fetch

RESULTS_URL_TEMPLATE = "https://www.laliga.com/laliga-easports/resultados/{season}/jornada-{week}"
MATCH_URL_TEMPLATE = "https://www.laliga.com/partido/{slug}"
DEFAULT_SEASON = "2025-26"


def discover_jornada(week: int, *, season: str = DEFAULT_SEASON) -> list[dict]:
    """Devuelve los partidos de una jornada: slug, url de detalle y status.

    status viene tal cual de LaLiga.com ("FullTime", "PreMatch", ...); filtrar
    por status queda a cargo de quien llame, no de esta función (D18: no
    pre-filtrar en el scraper).
    """
    url = RESULTS_URL_TEMPLATE.format(season=season, week=week)
    response = fetch(url)
    if response.status_code != 200:
        raise RuntimeError(f"GET {url} -> status {response.status_code}")

    blobs = extract_json_blobs(response.text)
    try:
        page_props = blobs["next_data"]["props"]["pageProps"]
    except KeyError as exc:
        raise RuntimeError(f"No se encontró __NEXT_DATA__.props.pageProps en {url}") from exc

    matches = page_props.get("matches") or []
    return [
        {
            "slug": m["slug"],
            "url": MATCH_URL_TEMPLATE.format(slug=m["slug"]),
            "status": m.get("status"),
            "jornada": week,
        }
        for m in matches
    ]


def discover_gameweek_list(*, season: str = DEFAULT_SEASON) -> list[dict]:
    """Lista de jornadas de la temporada (id, week, date), leída de cualquier
    página de resultados (trae siempre la temporada completa en gameweekList).
    Útil para saber cuántas jornadas backfillear sin hardcodear "38".
    """
    url = RESULTS_URL_TEMPLATE.format(season=season, week=1)
    response = fetch(url)
    blobs = extract_json_blobs(response.text)
    page_props = blobs["next_data"]["props"]["pageProps"]
    return page_props.get("gameweekList") or []


def _to_yaml_matches(matches: list[dict]) -> dict:
    return {
        "partidos": [
            {"slug": m["slug"], "url": m["url"], "status": m["status"]}
            for m in matches
        ]
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", type=int, required=True, help="Número de jornada (1-38).")
    parser.add_argument("--season", default=DEFAULT_SEASON)
    parser.add_argument("--only-played", action="store_true", help="Filtra a status == FullTime.")
    parser.add_argument("--write-yaml", type=Path, help="Escribe el resultado en formato matches_sample.yml.")
    args = parser.parse_args(argv)

    matches = discover_jornada(args.week, season=args.season)
    if args.only_played:
        matches = [m for m in matches if m["status"] == "FullTime"]

    for m in matches:
        print(f"{m['slug']:<70} status={m['status']}")
    print(f"\n{len(matches)} partidos encontrados para la jornada {args.week} ({args.season}).")

    if args.write_yaml:
        args.write_yaml.write_text(
            yaml.dump(_to_yaml_matches(matches), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        print(f"Escrito en {args.write_yaml}")


if __name__ == "__main__":
    main()
