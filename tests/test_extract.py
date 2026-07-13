"""Test canario (bloque 5 §3.3): si LaLiga.com cambia el formato del embebido,
este test avisa antes de que lo note el pipeline real."""
from pathlib import Path

from scraper.extract import extract_json_blobs, pick_extraction_method

FIXTURE = Path(__file__).parent / "fixtures" / "sample_match.html"


def test_extract_next_data_blob():
    html = FIXTURE.read_text()
    blobs = extract_json_blobs(html)

    assert pick_extraction_method(blobs) == "next_data"

    match = blobs["next_data"]["props"]["pageProps"]["match"]
    assert match["id"] == "12345"

    kinds = [c["kind"] for c in match["commentaries"]]
    assert kinds == [1, 4, 24, 28]


def test_no_json_script_returns_empty_blobs():
    blobs = extract_json_blobs("<html><body>sin scripts json</body></html>")
    assert blobs == {}
    assert pick_extraction_method(blobs) is None
