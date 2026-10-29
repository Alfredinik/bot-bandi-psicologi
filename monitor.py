import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}


def fetch_page(url: str) -> str | None:
    """Scarica il contenuto di una pagina."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException:
        return None


def extract_links(html: str, base_url: str) -> list[dict]:
    """Estrae i link che contengono la parola chiave."""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]

        if "psicolog" in text.lower() or "psicolog" in href.lower():
            full_url = urljoin(base_url, href)
            results.append({"title": text, "url": full_url})

    return results


def link_hash(link: dict) -> str:
    """Genera un hash univoco per un link."""
    raw = f"{link['title']}|{link['url']}"
    return hashlib.sha256(raw.encode()).hexdigest()