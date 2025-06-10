from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")      # headless depuis Chrome > 116
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# si vous gardez webdriver-manager :
options.binary_location = "/usr/bin/chromium"  # chemin installé par apt

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),  # ou Service("/usr/bin/chromedriver")
    options=options,
)

    try:
        for page in range(1, nb_pages + 1):
            if page == 1:
                url = BASE_URL + ".htm"
            else:
                url = f"{BASE_URL}_P{page}.htm{LANG_PARAM}"

            print(f"Navigation page {page}: {url}")
            driver.get(url)
            time.sleep(random.uniform(2, 4))  # Laisse le temps au JS de charger

            soup = BeautifulSoup(driver.page_source, "html.parser")
            page_reviews = soup.select("div[data-test='review-details-container']")

            if not page_reviews:
                print(f"⚠️ Aucun avis trouvé sur la page {page}")
            else:
                print(f"✅ {len(page_reviews)} avis trouvés sur la page {page}")
                for div in page_reviews:
                    reviews.append(_extract_one_review(div))

    finally:
        driver.quit()

    print(f"🎯 Total: {len(reviews)} avis récupérés (Selenium)")
    return pd.DataFrame(reviews)
