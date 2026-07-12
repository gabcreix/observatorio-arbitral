"""Inspecciona una URL suelta de LaLiga.com para localizar el JSON embebido (D30/D39).

No escribe en bronze. Pensado para correrlo a mano, una URL cada vez, mientras
se busca dónde vive el feed real antes de rellenar matches_sample.yml.

Uso:
    python -m scraper.inspect_match "https://www.laliga.com/partido/..."
"""
import argparse
import json

from .extract import extract_json_blobs
from .fetch import fetch


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--dump-file", default="inspect_dump.json")
    args = parser.parse_args(argv)

    response = fetch(args.url)
    print(f"status={response.status_code} bytes={len(response.text)}")

    blobs = extract_json_blobs(response.text)
    if not blobs:
        print("No se encontró ningún <script> con JSON parseable. Revisa el HTML a mano:")
        print(f"  (guardado el HTML crudo en inspect_dump.html)")
        with open("inspect_dump.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        return

    for name, blob in blobs.items():
        if name == "other_json_scripts":
            for i, item in enumerate(blob):
                keys = sorted(item.keys()) if isinstance(item, dict) else type(item).__name__
                print(f"- other_json_scripts[{i}]: {keys}")
        else:
            keys = sorted(blob.keys()) if isinstance(blob, dict) else type(blob).__name__
            print(f"- {name}: {keys}")

    with open(args.dump_file, "w", encoding="utf-8") as f:
        json.dump(blobs, f, ensure_ascii=False, indent=2)
    print(f"Volcado completo en {args.dump_file} para explorar a mano.")


if __name__ == "__main__":
    main()
