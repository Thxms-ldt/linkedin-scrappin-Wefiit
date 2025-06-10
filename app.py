import streamlit as st
import pandas as pd
from scraper import scrap_glassdoor_reviews

st.set_page_config(page_title="Scraper Glassdoor WeFiiT", layout="centered")
st.title("📊 Scraper les avis WeFiiT sur Glassdoor")

st.info("1. Charge ton fichier **glassdoor_credentials.txt** (format texte simple, 2 lignes : email, puis mot de passe)\n2. Clique sur 'Lancer le scraping'")

uploaded_file = st.file_uploader("Charge ton fichier glassdoor_credentials.txt", type="txt")

if uploaded_file is not None:
    content = uploaded_file.read().decode().splitlines()
    if len(content) >= 2:
        email = content[0].replace("email=", "").strip()
        password = content[1].replace("password=", "").strip()

        if st.button("Lancer le scraping (7 pages)"):
            with st.spinner("Scraping en cours..."):
                avis = scrap_glassdoor_reviews(email, password)
                if avis:
                    df = pd.DataFrame(avis)
                    st.success(f"{len(df)} avis extraits !")
                    st.dataframe(df)
                    csv = df.to_csv(index=False).encode()
                    st.download_button("📥 Télécharger en CSV", csv, "avis_wefiit.csv", "text/csv")
                else:
                    st.warning("Aucun avis trouvé.")
    else:
        st.error("Le fichier doit contenir au moins 2 lignes : email, puis mot de passe.")
