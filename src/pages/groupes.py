import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import locale



# -----------------------------
# VÉRIFICATION D'AUTHENTIFICATION
# -----------------------------
if not st.session_state.get('authenticated', False):
    st.switch_page("pages/loginpage.py")

# ---- Import des nouvelles fonctions ----
from calculator import (
    pipeline_global,
    extraire_inflation_mom,
    extraire_inflation_yoy
)

from visualizer import (
    tracer_inflation_grand_alger_mom,
    tracer_inflation_grand_alger_yoy,
    tracer_inflation_national_mom,
    tracer_inflation_national_yoy,
    tracer_inflation_contributions_grand_alger_mom,
    tracer_inflation_contributions_grand_alger_yoy,
    tracer_inflation_contributions_national_mom,
    tracer_inflation_contributions_national_yoy
)

# ---- Page config ----
st.set_page_config(page_title="Dashboard - Groupes", page_icon=":bar_chart:", layout="wide")

# Masquer le menu de navigation par défaut de Streamlit
hide_pages_style = """
    <style>
    div[data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_pages_style, unsafe_allow_html=True)

# ---- Global CSS ----
st.markdown("""
<style>
body, div, span, label {
    font-family: 'Segoe UI', sans-serif;
}
div.block-container{
    padding-top:1rem;
    color: #FFFFFF;
}
[data-testid="stSidebar"] {
    background-color: #0b1a2e;
    color: white;
}
[data-testid="stSidebar"] * {
    color: white;
}
[data-testid="stSidebar"] a:hover {
    background-color:#0056a3;
}
</style>
""", unsafe_allow_html=True)

# ---- Title ----
st.title(":bar_chart: Dashboard - Groupes")

# ---- Sidebar ----
with st.sidebar:
    # chemin relatif (place le logo dans src/)
    st.image("src/bankofalgerialogo.png", use_container_width=True)

    selected = option_menu(
        None,
        ["Acceuil", "Groupes", "Catégories"],
        icons=[],
        menu_icon="cast", default_index=1,
        styles={
            "container": {"padding": "0!important", "background-color": "#0b1a2e"},
            "icon": {"color": "white", "font-size": "18px"},
            "nav-link": {"color": "white", "font-size": "16px",
                         "text-align": "center", "margin": "0px",
                         "--hover-color": "#0056a3"},
            "nav-link-selected": {"background-color": "#0056a3"},
        }
    )

# ---- Configuration des chemins ----
# chemin relatif à ton projet
NOM_FICHIER = "src/Fichier_de_donnes.xlsx"
FEUILLE_GRAND_ALGER = "Grand_Alger"
FEUILLE_NATIONAL = "national"

# ---- Bouton pour exécuter tous les calculs ----
if st.sidebar.button("🔄 Calculer toutes les données"):
    with st.spinner("Calcul en cours..."):
        try:
            pipeline_global(NOM_FICHIER)
            st.sidebar.success("✅ Calculs terminés avec succès!")
        except Exception as e:
            st.sidebar.error(f"❌ Erreur: {str(e)}")

# ---- Chargement des données ----
region = st.selectbox("Région", options=["Grand Alger", "National"], key="region")
sheet_name = FEUILLE_GRAND_ALGER if region == "Grand Alger" else FEUILLE_NATIONAL

df = pd.read_excel(NOM_FICHIER, sheet_name=sheet_name)
df["date"] = pd.to_datetime(df["date"])
startDate = df["date"].min().date()
endDate = df["date"].max().date()

# ---- Filtres ----
col1, col2 = st.columns([2, 8])

with col1:
    type_glissement = st.selectbox("Type de glissement", options=["Annuel", "Mensuel"], key="glissement")

with col2:
    date_range = st.slider(
        "Période",
        min_value=startDate,
        max_value=endDate,
        value=(startDate, endDate),
        format="YYYY-MM-DD",
        key="periode"
    )

# Convert back to Timestamps for filtering
date1, date2 = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

# ---- Graphs side by side ----
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📈 Évolution des 8 groupes")

    if region == "Grand Alger":
        if type_glissement == "Annuel":
            tracer_inflation_grand_alger_yoy(NOM_FICHIER, date1.strftime("%Y-%m"), date2.strftime("%Y-%m"), export_png=False)
        else:
            tracer_inflation_grand_alger_mom(NOM_FICHIER, date1.strftime("%Y-%m"), date2.strftime("%Y-%m"), export_png=False)
    else:  # National
        if type_glissement == "Annuel":
            tracer_inflation_national_yoy(NOM_FICHIER, date1.strftime("%Y-%m"), date2.strftime("%Y-%m"), export_png=False)
        else:
            tracer_inflation_national_mom(NOM_FICHIER, date1.strftime("%Y-%m"), date2.strftime("%Y-%m"), export_png=False)

with col_right:
    st.subheader("📊 Contribution des 8 groupes en point de pourcentage")

    if region == "Grand Alger":
        if type_glissement == "Annuel":
            tracer_inflation_contributions_grand_alger_yoy(NOM_FICHIER, date1.strftime("%Y-%m"), date2.strftime("%Y-%m"), export_png=False)
        else:
            tracer_inflation_contributions_grand_alger_mom(NOM_FICHIER, date1.strftime("%Y-%m"), date2.strftime("%Y-%m"), export_png=False)
    else:  # National
        if type_glissement == "Annuel":
            tracer_inflation_contributions_national_yoy(NOM_FICHIER, date1.strftime("%Y-%m"), date2.strftime("%Y-%m"), export_png=False)
        else:
            tracer_inflation_contributions_national_mom(NOM_FICHIER, date1.strftime("%Y-%m"), date2.strftime("%Y-%m"), export_png=False)

# ---- Navigation vers les autres pages ----

if selected == "Acceuil":
    st.switch_page("front.py")
elif selected == "Catégories":
    st.switch_page("pages/categories.py")