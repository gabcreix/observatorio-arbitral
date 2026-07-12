"""Cliente HTTP mínimo (D30 — sin navegador headless)."""
import time

import httpx

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ObservatorioArbitralBot/0.1; "
        "proyecto de portfolio, uso ligero, no comercial)"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
}


def fetch(url: str, *, timeout: float = 20.0, delay_after: float = 1.5) -> httpx.Response:
    """GET simple con cabeceras de navegador y una pausa de cortesía tras cada petición."""
    with httpx.Client(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=timeout) as client:
        response = client.get(url)
    time.sleep(delay_after)
    return response
