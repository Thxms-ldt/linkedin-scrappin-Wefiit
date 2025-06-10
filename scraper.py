import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st

def create_session():
    """Crée une session avec retry strategy et headers appropriés"""
    session = requests.Session()
    
    # Strategy de retry
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Headers pour éviter la détection de bot
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    })
    
    return session

def scrape_reviews():
    """Fonction principale de scraping avec gestion d'erreurs améliorée"""
    session = create_session()
    reviews_data = []
    
    try:
        # URL de base (remplacez par votre URL réelle)
        base_url = "https://www.glassdoor.com/Reviews/Example-Company-Reviews-E12345.htm"  # À adapter
        
        # Boucle pour plusieurs pages si nécessaire
        for page in range(1, 6):  # 5 pages maximum
            try:
                st.info(f"Scraping page {page}...")
                
                # Délai aléatoire entre les requêtes
                if page > 1:
                    delay = random.uniform(2, 5)
                    time.sleep(delay)
                
                # Construction de l'URL avec pagination
                url = f"{base_url}?p={page}" if page > 1 else base_url
                
                # Requête avec timeout
                resp = session.get(url, timeout=15)
                
                # Vérification détaillée du statut
                if resp.status_code == 403:
                    st.warning("Accès bloqué (403) - Arrêt du scraping")
                    break
                elif resp.status_code == 429:
                    st.warning("Rate limit atteint (429) - Pause plus longue")
                    time.sleep(30)
                    continue
                elif resp.status_code == 404:
                    st.warning(f"Page {page} non trouvée (404)")
                    break
                
                # Lève l'exception si code d'erreur
                resp.raise_for_status()
                
                # Parsing HTML
                soup = BeautifulSoup(resp.content, 'html.parser')
                
                # Extraction des reviews (à adapter selon la structure HTML réelle)
                reviews = extract_reviews_from_page(soup)
                reviews_data.extend(reviews)
                
                st.success(f"Page {page} scrapée avec succès - {len(reviews)} reviews trouvées")
                
                # Si pas de reviews trouvées, arrêter
                if len(reviews) == 0:
                    st.warning("Aucune review trouvée sur cette page - Arrêt")
                    break
                    
            except requests.exceptions.HTTPError as e:
                st.error(f"Erreur HTTP page {page}: {e}")
                st.error(f"Code de statut: {resp.status_code}")
                if resp.status_code in [403, 429]:
                    st.error("Détection anti-bot probable - Arrêt du scraping")
                    break
                continue
                
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur de requête page {page}: {e}")
                continue
                
            except Exception as e:
                st.error(f"Erreur inattendue page {page}: {e}")
                continue
    
    except Exception as e:
        st.error(f"Erreur générale dans scrape_reviews: {e}")
        return pd.DataFrame()
    
    finally:
        session.close()
    
    # Conversion en DataFrame
    if reviews_data:
        df = pd.DataFrame(reviews_data)
        st.success(f"Scraping terminé - {len(df)} reviews récupérées au total")
        return df
    else:
        st.warning("Aucune donnée récupérée")
        return pd.DataFrame()

def extract_reviews_from_page(soup):
    """Extrait les reviews d'une page HTML"""
    reviews = []
    
    try:
        # À adapter selon la structure HTML réelle de Glassdoor
        # Exemple générique - vous devez adapter les sélecteurs CSS
        review_elements = soup.find_all('div', class_='review')  # Sélecteur à adapter
        
        for review_elem in review_elements:
            try:
                # Extraction des données (à adapter)
                title = review_elem.find('span', class_='review-title')
                rating = review_elem.find('span', class_='rating')
                text = review_elem.find('div', class_='review-text')
                date = review_elem.find('time')
                
                review_data = {
                    'title': title.get_text().strip() if title else '',
                    'rating': rating.get_text().strip() if rating else '',
                    'text': text.get_text().strip() if text else '',
                    'date': date.get_text().strip() if date else '',
                }
                
                reviews.append(review_data)
                
            except Exception as e:
                st.warning(f"Erreur lors de l'extraction d'une review: {e}")
                continue
    
    except Exception as e:
        st.error(f"Erreur lors de l'extraction des reviews: {e}")
    
    return reviews

def scrape_with_selenium():
    """Alternative avec Selenium si HTTP requests ne fonctionnent plus"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Configuration Chrome
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=options)
        reviews_data = []
        
        try:
            url = "https://www.glassdoor.com/Reviews/Example-Company-Reviews-E12345.htm"  # Votre URL
            driver.get(url)
            
            # Attendre que la page se charge
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "review"))
            )
            
            # Extraction avec Selenium
            review_elements = driver.find_elements(By.CLASS_NAME, "review")
            
            for elem in review_elements:
                # Extraction similaire mais avec Selenium
                try:
                    title = elem.find_element(By.CLASS_NAME, "review-title").text
                    rating = elem.find_element(By.CLASS_NAME, "rating").text
                    text = elem.find_element(By.CLASS_NAME, "review-text").text
                    
                    review_data = {
                        'title': title,
                        'rating': rating,
                        'text': text,
                        'date': ''
                    }
                    
                    reviews_data.append(review_data)
                except Exception as e:
                    continue
            
        finally:
            driver.quit()
            
        return pd.DataFrame(reviews_data)
        
    except ImportError:
        st.error("Selenium non installé. Ajoutez 'selenium' à requirements.txt")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur Selenium: {e}")
        return pd.DataFrame()
