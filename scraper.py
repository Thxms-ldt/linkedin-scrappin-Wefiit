import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.glassdoor.fr/Avis/WeFiiT-Avis-E3310403"
LANG_PARAM = "?filter.iso3Language=fra"

# Headers plus complets pour éviter la détection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

def create_session():
    """Crée une session avec retry automatique."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504, 403, 404],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

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
    """Scrape les avis Glassdoor WeFiiT (langue FR) avec gestion d'erreurs améliorée."""
    reviews: List[Dict[str, str]] = []
    session = create_session()
    
    for page in range(1, nb_pages + 1):
        try:
            if page == 1:
                url = BASE_URL + ".htm"
            else:
                url = f"{BASE_URL}_P{page}.htm{LANG_PARAM}"
            
            print(f"Téléchargement page {page}: {url}")
            
            # Délai aléatoire entre les requêtes (1-4 secondes)
            if page > 1:
                delay = random.uniform(1, 4)
                print(f"Attente de {delay:.1f}s...")
                time.sleep(delay)
            
            resp = session.get(url, headers=HEADERS, timeout=30)
            
            # Vérification du code de statut
            if resp.status_code == 403:
                print(f"❌ Accès refusé (403) pour la page {page}")
                print("Glassdoor bloque probablement les requêtes automatisées")
                break
            elif resp.status_code == 429:
                print(f"❌ Trop de requêtes (429) pour la page {page}")
                print("Attente de 60 secondes...")
                time.sleep(60)
                continue
            
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            page_reviews = soup.select("div[data-test='review-details-container']")
            
            if not page_reviews:
                print(f"⚠️ Aucun avis trouvé sur la page {page}")
                # Afficher un extrait de la réponse pour debug
                print(f"Début de la réponse HTML: {resp.text[:500]}...")
            else:
                print(f"✅ {len(page_reviews)} avis trouvés sur la page {page}")
                for div in page_reviews:
                    reviews.append(_extract_one_review(div))
                    
        except requests.exceptions.HTTPError as e:
            print(f"❌ Erreur HTTP sur la page {page}: {e}")
            print(f"Code de statut: {resp.status_code}")
            if resp.status_code == 403:
                print("🚫 Glassdoor bloque l'accès - IP ou User-Agent détecté")
            elif resp.status_code == 429:
                print("⏱️ Rate limit atteint - trop de requêtes")
            break
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de requête sur la page {page}: {e}")
            break
            
        except Exception as e:
            print(f"❌ Erreur inattendue sur la page {page}: {e}")
            break
    
    print(f"🎯 Total: {len(reviews)} avis récupérés")
    return pd.DataFrame(reviews)

if __name__ == "__main__":
    df = scrape_reviews()
    print(df.head())
