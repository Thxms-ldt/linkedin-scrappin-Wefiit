import streamlit as st
import pandas as pd
from scraper import scrape_reviews

st.set_page_config(page_title="Scraper Glassdoor WeFiiT", page_icon="📊")
st.title("📊 Scraper des avis WeFiiT sur Glassdoor (langue FR)")

st.markdown("""
**Instructions :**
1. Cliquez sur le bouton **« Lancer le scraping »** pour récupérer les 7 pages d'avis (cela peut prendre ~30 s).
2. Une fois terminé, un aperçu s'affiche et vous pouvez **télécharger le CSV**.
""")

if st.button("Lancer le scraping"):
    with st.spinner("Scraping en cours …"):
        df = scrape_reviews()
    if not df.empty:
        st.success(f"{len(df)} avis récupérés ✅")
        st.dataframe(df)
        csv_bytes = df.to_csv(index=False).encode()
        st.download_button("📥 Télécharger le CSV", csv_bytes, "avis_wefiit.csv", mime="text/csv")
    else:
        st.warning("Aucun avis trouvé. Essayez plus tard.")
