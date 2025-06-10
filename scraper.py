import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict

BASE_URL = "https://www.glassdoor.fr/Avis/WeFiiT-Avis-E3310403"
LANG_PARAM = "?filter.iso3Language=fra"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
}

def _extract_one_review(div) -> Dict[str, str]:
    """Parse un bloc <div data-test='review-details-container'> et renvoie un dict."""
    def _safe(sel):
        el = div.select_one(sel)
        return el.get_text(strip=True) if el else ""

    # Tags positifs (recommande / PDG / perspective)
    tags = [span.get_text(strip=True) for span in div.select("div.rating-icon_ratingContainer__9UoJ6 span")]
    return {
        "note": _safe("span[data-test='review-rating-label']"),
        "date": _safe("span.timestamp_reviewDate__dsF9n"),
        "titre": _safe("h3[data-test='review-details-title']"),
        "poste": _safe("span[data-test='review-avatar-label']"),
        "avantages": _safe("span[data-test='review-text-PROS']"),
        "inconvenients": _safe("span[data-test='review-text-CONS']"),
        "recommande": "Oui" if any("Recommande" in t for t in tags) else "Non",
        "approbation_PDG": "Oui" if any("PDG" in t for t in tags) else "Non",
        "perspective": "Oui" if any("Perspective" in t for t in tags) else "Non"
    }


def scrape_reviews(nb_pages: int = 7) -> pd.DataFrame:
    """Scrape les avis Glassdoor WeFiiT (langue FR) sans Selenium."""
    reviews: List[Dict[str, str]] = []
    for page in range(1, nb_pages + 1):
        if page == 1:
            url = BASE_URL + ".htm"
        else:
            url = f"{BASE_URL}_P{page}.htm{LANG_PARAM}"
        print(f"Téléchargement {url}")
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for div in soup.select("div[data-test='review-details-container']"):
            reviews.append(_extract_one_review(div))
    return pd.DataFrame(reviews)

if __name__ == "__main__":
    df = scrape_reviews()
    print(df.head())
