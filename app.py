import streamlit as st
import pandas as pd
from scraper import scrape_reviews, scrape_with_selenium
import time

# Configuration de la page
st.set_page_config(
    page_title="Glassdoor Scraper",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Glassdoor Reviews Scraper")
st.markdown("---")

# Sidebar pour les options
with st.sidebar:
    st.header("Options de scraping")
    
    scraping_method = st.selectbox(
        "Méthode de scraping",
        ["Requests + BeautifulSoup", "Selenium (plus lent mais plus fiable)"]
    )
    
    max_pages = st.slider("Nombre maximum de pages", 1, 10, 3)
    
    if st.button("🚀 Lancer le scraping", type="primary"):
        st.session_state.start_scraping = True

# Zone principale
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Données scrapées")
    results_container = st.container()

with col2:
    st.subheader("Statut")
    status_container = st.container()

# Logique de scraping
if st.session_state.get('start_scraping', False):
    
    with status_container:
        st.info("🔄 Scraping en cours...")
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    try:
        # Choix de la méthode
        if scraping_method == "Requests + BeautifulSoup":
            status_text.text("Utilisation de Requests + BeautifulSoup...")
            df = scrape_reviews()
        else:
            status_text.text("Utilisation de Selenium...")
            df = scrape_with_selenium()
        
        progress_bar.progress(100)
        
        # Affichage des résultats
        with results_container:
            if not df.empty:
                st.success(f"✅ Scraping terminé ! {len(df)} reviews récupérées")
                
                # Métriques
                col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
                with col_metrics1:
                    st.metric("Total Reviews", len(df))
                with col_metrics2:
                    if 'rating' in df.columns:
                        try:
                            avg_rating = df['rating'].str.extract(r'(\d+\.?\d*)').astype(float).mean()
                            st.metric("Note Moyenne", f"{avg_rating:.1f}/5")
                        except:
                            st.metric("Note Moyenne", "N/A")
                with col_metrics3:
                    st.metric("Colonnes", len(df.columns))
                
                # Aperçu des données
                st.subheader("Aperçu des données")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Options de téléchargement
                st.subheader("Téléchargement")
                col_dl1, col_dl2 = st.columns(2)
                
                with col_dl1:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name=f"glassdoor_reviews_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                with col_dl2:
                    try:
                        excel_buffer = pd.io.common.BytesIO()
                        df.to_excel(excel_buffer, index=False)
                        st.download_button(
                            label="📥 Télécharger Excel",
                            data=excel_buffer.getvalue(),
                            file_name=f"glassdoor_reviews_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except ImportError:
                        st.warning("Excel export non disponible. Utilisez CSV.")
                
            else:
                st.error("❌ Aucune donnée récupérée. Vérifiez les logs ci-dessus.")
        
        with status_container:
            if not df.empty:
                st.success("✅ Scraping terminé avec succès")
            else:
                st.error("❌ Scraping échoué")
    
    except Exception as e:
        with status_container:
            st.error(f"❌ Erreur durant le scraping: {str(e)}")
        
        with results_container:
            st.error("Le scraping a échoué. Voici quelques solutions :")
            
            st.markdown("""
            ### Solutions possibles :
            
            1. **Glassdoor bloque les bots** - Essayez la méthode Selenium
            2. **Rate limiting** - Réduisez le nombre de pages
            3. **URL incorrecte** - Vérifiez l'URL dans le code
            4. **Changement de structure** - Le site a peut-être changé
            
            ### Debug :
            - Vérifiez les logs dans la console Streamlit
            - Testez avec une seule page d'abord
            - Vérifiez votre connexion internet
            """)
    
    # Reset du flag
    st.session_state.start_scraping = False

# Informations
with st.expander("ℹ️ Informations et limitations"):
    st.markdown("""
    ### À propos de ce scraper
    
    Ce scraper permet d'extraire les avis Glassdoor de manière automatisée.
    
    ### Limitations importantes :
    - **Anti-bot** : Glassdoor détecte et bloque les bots
    - **Rate limiting** : Limite du nombre de requêtes par minute
    - **Légalité** : Respectez les conditions d'utilisation de Glassdoor
    - **Stabilité** : La structure du site peut changer
    
    ### Conseils d'utilisation :
    1. Commencez par tester avec 1-2 pages
    2. Utilisez Selenium si les requêtes HTTP échouent
    3. Respectez les délais entre les requêtes
    4. Vérifiez les logs en cas d'erreur
    
    ### Dépendances requises (requirements.txt) :
    ```
    streamlit
    requests
    beautifulsoup4
    pandas
    selenium
    webdriver-manager
    lxml
    openpyxl
    ```
    """)

# Footer
st.markdown("---")
st.markdown("💡 **Tip**: Si le scraping échoue, essayez la méthode Selenium ou réduisez le nombre de pages.")
