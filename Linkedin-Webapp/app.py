import streamlit as st
import csv
import time
from playwright.sync_api import sync_playwright

st.title("🔎 Scraper LinkedIn par poste et envoyer 10 invitations max")

email = st.text_input("Email LinkedIn")
password = st.text_input("Mot de passe LinkedIn", type="password")
keyword = st.text_input("Mot-clé à rechercher (ex: Product Owner)", value="Product Owner")
run = st.button("Lancer le scraping et les invitations")

def scrape_and_connect(email, password, keyword):
    data = []
    invitations = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.linkedin.com/login")
        page.fill('input#username', email)
        page.fill('input#password', password)
        page.click('button[type=\"submit\"]')
        time.sleep(5)

        # Recherche directe
        search_url = f"https://www.linkedin.com/search/results/all/?keywords={keyword.replace(' ', '%20')}"
        page.goto(search_url)
        time.sleep(5)

        try:
            personnes_btn = page.locator('button.search-reusables__filter-pill-button', has_text="Personnes")
            personnes_btn.first.click()
        except Exception:
            pass
        time.sleep(5)

        profils = page.locator('div.eVytruVtVXrXkDMKvkhgcMbUTTJOCyVMU')
        count = profils.count()

        for i in range(count):
            profil = profils.nth(i)
            try:
                name_elem = profil.locator('span[aria-hidden="true"]').first
                name = name_elem.inner_text().strip()
            except Exception:
                name = ""
            try:
                job_elem = profil.locator('div.t-14.t-black.t-normal').first
                job = job_elem.inner_text().strip()
            except Exception:
                job = ""
            try:
                company_elem = profil.locator('p.entity-result__summary--2-lines').first
                company = company_elem.inner_text().strip()
            except Exception:
                company = ""
            try:
                link_elem = profil.locator('a.PDuZgTTJniSbcpBCzeHjMlcFFsgCxLEhvw').first
                link = link_elem.get_attribute('href')
            except Exception:
                link = ""
            data.append([name, job, company, link])

            # Limiter à 10 invitations maximum
            if invitations < 10:
                try:
                    connect_btn = profil.locator('button:has-text("Se connecter")')
                    if connect_btn.count() > 0:
                        connect_btn.first.click()
                        time.sleep(2)
                        send_btn = page.locator('button span.artdeco-button__text', has_text="Envoyer sans note")

                        if send_btn.count() > 0:
                            send_btn.first.evaluate('node => node.closest("button").click()')
                            invitations += 1
                            time.sleep(2)
                except Exception:
                    pass

        browser.close()
    return data, invitations

if run and email and password and keyword:
    st.info("Scraping en cours... Patientez 20 à 30 secondes")
    rows, invitations = scrape_and_connect(email, password, keyword)
    if rows:
        st.success(f"{len(rows)} profils extraits ! {invitations} demandes de connexion envoyées.")
        with open("profils_linkedin.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Nom", "Poste", "Entreprise", "Lien LinkedIn"])
            writer.writerows(rows)
        with open("profils_linkedin.csv", "rb") as f:
            st.download_button("Télécharger le CSV", f, "profils_linkedin.csv")
    else:
        st.error("Aucun profil trouvé ou identifiants incorrects.")

