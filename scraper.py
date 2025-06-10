import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def scrap_glassdoor_reviews(email, password, nb_pages=7):
    options = Options()
    options.add_argument("--headless=new")  # Retire cette ligne pour voir Chrome
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    reviews = []

    urls = [
        "https://www.glassdoor.fr/Avis/WeFiiT-Avis-E3310403.htm"
    ] + [
        f"https://www.glassdoor.fr/Avis/WeFiiT-Avis-E3310403_P{page}.htm?filter.iso3Language=fra"
        for page in range(2, nb_pages+1)
    ]

    for page_num, url in enumerate(urls, 1):
        driver.get(url)
        time.sleep(2)

        # Accepter cookies si popup
        try:
            btn = driver.find_element(By.XPATH, "//button[contains(text(),'Accepter')]")
            btn.click()
            time.sleep(1)
        except Exception:
            pass

        soup = BeautifulSoup(driver.page_source, "html.parser")
        avis_html = soup.find_all("div", attrs={"data-test": "review-details-container"})

        for avis in avis_html:
            try:
                titre = avis.select_one("[data-test='review-details-title']").get_text(strip=True)
            except: titre = ""
            try:
                note = avis.select_one("[data-test='review-rating-label']").get_text(strip=True)
            except: note = ""
            try:
                date = avis.select_one("span.timestamp_reviewDate__dsF9n").get_text(strip=True)
            except: date = ""
            try:
                poste = avis.select_one("span.review-avatar_avatarLabel__P15ey").get_text(strip=True)
            except: poste = ""
            try:
                localisation = ""
                tags = avis.select("div.review-avatar_tagsContainer__9NCNs div.text-with-icon_LabelContainer__xbtB8")
                if tags:
                    localisation = tags[-1].get_text(strip=True)
            except: localisation = ""
            try:
                recommande = "Oui" if avis.select_one("div.rating-icon_positiveStyles__LGHYG span") and "Recommande" in avis.select_one("div.rating-icon_positiveStyles__LGHYG span").get_text() else "Non"
            except: recommande = ""
            try:
                avantages = avis.select_one("span[data-test='review-text-PROS']").get_text(strip=True)
            except: avantages = ""
            try:
                inconvenients = avis.select_one("span[data-test='review-text-CONS']").get_text(strip=True)
            except: inconvenients = ""
            reviews.append({
                "titre": titre,
                "note": note,
                "date": date,
                "poste": poste,
                "localisation": localisation,
                "recommande": recommande,
                "avantages": avantages,
                "inconvenients": inconvenients
            })

    driver.quit()
    return reviews
