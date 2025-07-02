import time
import urllib.parse
import pandas as pd
import streamlit as st
import csv
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

# ---- Liste complète des écoles avec IDs LinkedIn ----
ECOLES = {
    "DAUPHINE": "15092700",
    "Arts et Métiers": "1280025",
    "GEM": "18927",
    "NOE": "42878938",
    "ESCP": "308907",
    "Cergy Université": "86580",
    "Audencia": "15104766",
    "INSA Rennes": "10438659",
    "Sorbonne": "18423073",
    "PPA": "15097420",
    "Edhec": "16001",
    "ESIEE": "15106279",
    "ESG": "1883450",
    "INSEEC": "12635396",
    "SKEMA": "2413397",
    "Rennes Bs": "15092681",
    "KEDGE": "2757210",
    "ECE": "280138",
    "TBS": "47992",
    "Institut Mines-Télécom Business School": "328768",
    "IESEG": "319911",
    "ESGI": "15251121",
    "EPF": "15094113",
    "EM Lyon": "18361",
    "PSTB": "77002277",
    "Neoma": "3330082",
    "ESSEC": "11415",
    "HEC Paris": "235785"
}

st.title("🔍 LinkedIn Scraper / Inviter / Messagerie (2024-2025, filtres écoles + entreprise)")

cookie = st.text_input("Session cookie 'li_at' LinkedIn", "", type="password")
keyword = st.text_input("Mots-clés à rechercher", "Product Manager")
entreprise_filtre = st.text_input("Filtrer par entreprise (optionnel, nom exact sur LinkedIn, ex: Sanofi)", "")
nb_profils = st.number_input("Nombre de profils à scraper", min_value=1, max_value=100, value=10)

# SECTION ÉCOLE (cases à cocher en grille)
st.markdown("### 🎓 Filtrer par école (optionnel)")
st.caption("Coche **UNE seule école** pour cibler les alumni. Si tu coches plusieurs écoles, la recherche va cibler uniquement les personnes ayant fait *toutes* ces écoles à la fois (ce qui est très rare).")

ecoles_choisies = []
ecole_list = list(ECOLES.items())
cols = st.columns(4)
for idx, (nom, id_) in enumerate(ecole_list):
    if cols[idx % 4].checkbox(nom):
        ecoles_choisies.append(id_)

if len(ecoles_choisies) > 1:
    st.warning("⚠️ Attention : LinkedIn ne retourne que les personnes ayant fait *toutes* ces écoles à la fois. Nous recommandons de ne cocher qu’une seule école à la fois pour obtenir une vraie liste d’alumni.")

st.markdown("### Fonction 1 : Scraper & Inviter")
INVITATIONS_FILE = "invitations_envoyees.csv"

def charger_urls_envoyees():
    if not os.path.exists(INVITATIONS_FILE):
        return set()
    with open(INVITATIONS_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return set(row.get("URL du profil", "") for row in reader)

def sauvegarder_invitation(nom, poste, entreprise, ecole, url, invite_envoyee):
    deja = charger_urls_envoyees()
    champ = ["Nom prénom", "Poste", "Entreprise", "École", "URL du profil", "Date d'envoi", "Invitation envoyée"]
    existe = os.path.exists(INVITATIONS_FILE)
    with open(INVITATIONS_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=champ)
        if not existe:
            writer.writeheader()
        if url not in deja:
            writer.writerow({
                "Nom prénom": nom,
                "Poste": poste,
                "Entreprise": entreprise,
                "École": ecole,
                "URL du profil": url,
                "Date d'envoi": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Invitation envoyée": invite_envoyee
            })

def linkedin_url(keyword, entreprise="", page_num=1, ecoles=[]):
    kw = keyword.strip()
    if entreprise.strip():
        kw = kw + " " + entreprise.strip()
    url = (
        "https://www.linkedin.com/search/results/people/"
        f"?keywords={urllib.parse.quote(kw)}"
        f"&origin=FACETED_SEARCH"
        f"&page={page_num}"
    )
    if ecoles:
        school_filter_url = "&schoolFilter=" + urllib.parse.quote(str(ecoles).replace('\'', '"'))
        url += school_filter_url
    return url

def fermer_popups_linkedin(page):
    for _ in range(8):
        croix = page.query_selector_all("button > svg[data-test-icon='close-small']")
        for svg in croix:
            try:
                btn = svg.evaluate_handle("node => node.closest('button')")
                btn.click()
                time.sleep(0.2)
            except:
                pass
        containers = page.query_selector_all("div.msg-overlay-bubble-header__badge-container")
        for cont in containers:
            try:
                btn = cont.evaluate_handle("node => node.parentElement.querySelector('button')")
                svg = btn.query_selector("svg")
                if svg and "compose-small" not in (svg.get_attribute("data-test-icon") or ""):
                    btn.click()
                    time.sleep(0.2)
            except:
                pass
        chevrons = page.query_selector_all("button > svg[data-test-icon='chevron-up-small']")
        for svg in chevrons:
            try:
                btn = svg.evaluate_handle("node => node.closest('button')")
                btn.click()
                time.sleep(0.2)
            except:
                pass
        if not page.query_selector("div.msg-overlay-bubble-header__badge-container"):
            break

def run_scraper(inviter=False):
    donnees = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.add_cookies([{
            'name': 'li_at',
            'value': cookie,
            'domain': '.linkedin.com',
            'path': '/',
            'httpOnly': True,
            'secure': True
        }])
        page = context.new_page()
        page.goto("https://www.linkedin.com/feed/", timeout=60000)
        time.sleep(2)
        fermer_popups_linkedin(page)
        if "/feed" not in page.url:
            st.error("❌ Le cookie n'est pas valide ou a expiré.")
            browser.close()
            return
        profils_scrapes = 0
        current_page = 1
        deja_urls = charger_urls_envoyees() if inviter else set()
        invitation_bloquee = False

        while profils_scrapes < nb_profils:
            search_url = linkedin_url(keyword, entreprise_filtre, page_num=current_page, ecoles=ecoles_choisies)
            st.markdown(f"🔍 Recherche sur LinkedIn : {search_url}")
            try:
                page.goto(search_url, timeout=60000)
            except Exception as e:
                st.warning(f"⚠️ Erreur de chargement de la page : {e}")
                break
            time.sleep(3)
            for _ in range(3):
                page.mouse.wheel(0, 2000)
                time.sleep(1)

            profils = page.query_selector_all("li.reusable-search__result-container")
            if not profils:
                profils = page.query_selector_all("div.entity-result__item")
            if not profils:
                profils = [li for li in page.query_selector_all("li") if li.query_selector("a[href*='/in/']")]

            profils_page = []
            for block in profils:
                try:
                    url_elem = block.query_selector("a[href*='/in/']")
                    url_profil = url_elem.get_attribute("href") if url_elem else ""
                except:
                    url_profil = ""
                if not url_profil or url_profil in deja_urls:
                    continue
                deja_urls.add(url_profil)

                # NOM
                try:
                    nom = block.query_selector("a[href*='/in/'] span[aria-hidden='true']").inner_text().strip()
                except:
                    try:
                        nom = block.query_selector("span[aria-hidden='true']").inner_text().strip()
                    except:
                        nom = ""

                # POSTE
                try:
                    poste = block.query_selector("div.t-14.t-black.t-normal").inner_text().strip()
                except:
                    try:
                        poste = block.query_selector("div.ChoOqJiqYCCuGBLuHKTvuTmZYMUnKHNXVnZao").inner_text().strip()
                    except:
                        poste = ""

                # ENTREPRISE
                try:
                    p_ent = block.query_selector("p.entity-result__summary--2-lines")
                    if p_ent:
                        texte_ent = p_ent.inner_text().strip()
                        if "chez " in texte_ent:
                            entreprise = texte_ent.split("chez ")[-1].split()[0]
                        else:
                            entreprise = texte_ent
                    else:
                        entreprise = ""
                except:
                    entreprise = ""

                # -- École (nom) --
                ecole_nom = ", ".join([k for k, v in ECOLES.items() if v in ecoles_choisies]) if ecoles_choisies else ""

                invite_envoyee = "Non"
                if inviter and not invitation_bloquee:
                    try:
                        btns = block.query_selector_all("button")
                        for btn in btns:
                            txt = btn.inner_text().strip().lower()
                            if "se connecter" in txt or "connect" in txt:
                                btn.click()
                                time.sleep(2)
                                fermer_popups_linkedin(page)
                                popup_limit = page.query_selector("div[data-test-modal-id='fuse-limit-alert']")
                                if popup_limit:
                                    ok_btn = page.query_selector("button[aria-label='OK']")
                                    if ok_btn:
                                        ok_btn.click()
                                    st.warning("❗️ Limite d'invitations atteinte, plus aucune invitation ne sera envoyée.")
                                    invitation_bloquee = True
                                    invite_envoyee = "Non (limite atteinte)"
                                    break
                                envoyer_btn = page.query_selector("button[aria-label*='Envoyer']") or page.query_selector("button:has-text('Envoyer')")
                                if envoyer_btn:
                                    envoyer_btn.click()
                                    invite_envoyee = "Oui"
                                    st.success(f"✅ Invitation envoyée à {nom}.")
                                else:
                                    st.warning("⚠️ Bouton 'Envoyer' introuvable.")
                                fermer_popups_linkedin(page)
                                time.sleep(2)
                                break
                    except Exception as e:
                        st.warning(f"❌ Erreur lors de l'invitation : {str(e)}")
                elif invitation_bloquee:
                    invite_envoyee = "Non (limite atteinte)"

                donnees.append({
                    "Nom prénom": nom,
                    "Poste": poste,
                    "Entreprise": entreprise,
                    "École": ecole_nom,
                    "URL du profil": url_profil,
                    "Invitation envoyée": invite_envoyee
                })
                if inviter:
                    sauvegarder_invitation(nom, poste, entreprise, ecole_nom, url_profil, invite_envoyee)
                profils_scrapes += 1
                profils_page.append(nom)
                if profils_scrapes >= nb_profils:
                    break
            st.write(f"{len(profils_page)} profils récupérés sur la page {current_page}")
            if not profils_page:
                st.warning("⚠️ Aucun profil détecté sur la page (structure ou sélecteur LinkedIn changé).")
                break
            current_page += 1
        browser.close()
        df = pd.DataFrame(donnees)
        st.write(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Télécharger le CSV", data=csv, file_name="linkedin_profils.csv", mime="text/csv")

col1, col2 = st.columns(2)
with col1:
    if st.button("Lancer le scraping + invitations", key="inviter"):
        if not cookie:
            st.warning("Veuillez fournir votre cookie de session 'li_at'.")
        else:
            run_scraper(inviter=True)
with col2:
    if st.button("Scraper uniquement les profils", key="scraper_seul"):
        if not cookie:
            st.warning("Veuillez fournir votre cookie de session 'li_at'.")
        else:
            run_scraper(inviter=False)

# ------------------- MESSAGERIE -------------------
st.markdown("---")
st.markdown("### Fonction 2 : Envoyer un message à une liste de contacts déjà acceptés")

message_mode = st.checkbox("Activer l'envoi de messages personnalisés")
if message_mode:
    message_txt = st.text_area("Message à envoyer", "Bonjour, ravi d’être en contact !")
    message_file = st.file_uploader("CSV avec URLs de profils à contacter (colonne 1 = URL)", type="csv")
    if st.button("Envoyer les messages"):
        if not cookie:
            st.warning("Veuillez fournir votre cookie de session 'li_at'.")
        elif not message_file:
            st.warning("Veuillez uploader un fichier CSV avec une colonne 'URL du profil'.")
        else:
            df_msg = pd.read_csv(message_file)
            urls = [str(u).strip().rstrip("; /") for u in df_msg[df_msg.columns[0]].dropna().unique()]
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                context.add_cookies([{
                    'name': 'li_at',
                    'value': cookie,
                    'domain': '.linkedin.com',
                    'path': '/',
                    'httpOnly': True,
                    'secure': True
                }])
                page = context.new_page()
                page.goto("https://www.linkedin.com/feed/", timeout=60000)
                time.sleep(2)
                fermer_popups_linkedin(page)
                if "/feed" not in page.url:
                    st.error("❌ Le cookie n'est pas valide ou a expiré.")
                    browser.close()
                else:
                    count_sent = 0
                    for url in urls:
                        try:
                            st.info(f"Envoi à {url} ...")
                            page.goto(url, timeout=30000)
                            time.sleep(2)
                            fermer_popups_linkedin(page)
                            for _ in range(5):
                                if not page.query_selector("div.msg-overlay-bubble-header__badge-container"):
                                    break
                                fermer_popups_linkedin(page)
                                time.sleep(0.2)
                            btn_msg = None
                            for btn in page.query_selector_all("button"):
                                try:
                                    if btn.inner_text().strip().lower() == "message":
                                        btn_msg = btn
                                        break
                                except:
                                    continue
                            if not btn_msg:
                                btn_msg_link = page.query_selector("a[aria-label^='Message']")
                                if btn_msg_link:
                                    btn_msg = btn_msg_link
                            if btn_msg:
                                try:
                                    btn_msg.scroll_into_view_if_needed()
                                    time.sleep(0.5)
                                    btn_msg.click(timeout=10000)
                                    time.sleep(1.5)
                                except Exception as e:
                                    st.warning(f"⚠️ Impossible de cliquer sur le bouton Message pour {url} : {e}")
                                    fermer_popups_linkedin(page)
                                    continue
                                # Ecrire et envoyer le message
                                try:
                                    textarea = page.wait_for_selector("div.msg-form__contenteditable", timeout=9000)
                                    textarea.scroll_into_view_if_needed()
                                    time.sleep(0.4)
                                    textarea.click()
                                    time.sleep(0.4)
                                    textarea.fill("")
                                    textarea.type(message_txt)
                                    time.sleep(0.7)
                                    send_btn = page.query_selector("button.msg-form__send-button") or \
                                               page.query_selector("button[aria-label*='Envoyer']") or \
                                               page.query_selector("button:has-text('Envoyer')")
                                    if send_btn:
                                        send_btn.click()
                                        count_sent += 1
                                        st.success(f"Message envoyé à {url}")
                                    else:
                                        st.warning(f"⚠️ Bouton Envoyer introuvable pour {url}")
                                except Exception as e:
                                    st.warning(f"⚠️ Zone de texte non trouvée ou non éditable pour {url} : {e}")
                            else:
                                st.warning(f"⚠️ Pas de bouton Message sur {url} (pas dans tes contacts ?)")
                            time.sleep(0.5)
                            fermer_popups_linkedin(page)
                        except Exception as e:
                            st.warning(f"❌ Erreur pour {url}: {e}")
                            fermer_popups_linkedin(page)
                    st.success(f"✅ {count_sent} message(s) envoyé(s).")
                browser.close()
