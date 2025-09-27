import streamlit as st
# -----------------------------
# VÉRIFICATION D'AUTHENTIFICATION
# -----------------------------
if not st.session_state.get('authenticated', False):
    st.switch_page("pages/loginpage.py")
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.figure_factory as ff
import plotly.express as px
import os

# -----------------------------
# VÉRIFICATION D'AUTHENTIFICATION
# -----------------------------
if not st.session_state.get('authenticated', False):
    st.switch_page("loginpage.py")


# ---- Import des nouvelles fonctions ----
from calculator import (
    pipeline_global,
    extraire_inflation_mom,
    extraire_inflation_yoy
)

from visualizer import (
    tracer_inflation_categories_mom,
    tracer_inflation_categories_yoy,
    tracer_inflation_contributions_categories_mom,
    tracer_inflation_contributions_categories_yoy
)

# ---- Page config ----
st.set_page_config(page_title="Dashboard - Catégories", page_icon=":bar_chart:", layout="wide")
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
st.title(":bar_chart: Dashboard - Catégories")

# ---- Sidebar ----
with st.sidebar:
    st.image(r"C:\Users\HP\Downloads\BI_BA\Stage\src\bankofalgerialogo.PNG", use_container_width=True)

    selected = option_menu(
        None,
        ["Acceuil", "Groupes", "Catégories"],
        icons=[],
        menu_icon="cast", default_index=2,
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
NOM_FICHIER = (r"C:\Users\HP\Downloads\BI_BA\Stage\src\Fichier_de_donnes.xlsx")
FEUILLE_CATEGORIES = "categories"

# ---- Bouton pour exécuter tous les calculs ----
if st.sidebar.button("🔄 Calculer toutes les données"):
    with st.spinner("Calcul en cours..."):
        try:
            pipeline_global(NOM_FICHIER)
            st.sidebar.success("✅ Calculs terminés avec succès!")
        except Exception as e:
            st.sidebar.error(f"❌ Erreur: {str(e)}")

# ---- Load data from categories sheet ----
df = pd.read_excel(NOM_FICHIER, sheet_name=FEUILLE_CATEGORIES)
df["date"] = pd.to_datetime(df["date"])
startDate = df["date"].min().date()
endDate = df["date"].max().date()

# ---- Filters ----
col1, col2, col3 = st.columns([2, 2, 6])

with col1:
    region = st.selectbox("Région", options=["Grand Alger", "National"])

with col2:
    type_glissement = st.selectbox("Type de glissement", options=["Annuel", "Mensuel"])

with col3:
    date_range = st.slider(
        "Période",
        min_value=startDate,
        max_value=endDate,
        value=(startDate, endDate),
        format="YYYY-MM-DD"
    )

# Convert back to Timestamps for filtering
date1, date2 = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

# ---- Graphs side by side ----
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📈 Évolution des catégories")

    if type_glissement == "Annuel":
        tracer_inflation_categories_yoy(
            nom_fichier=NOM_FICHIER,
            date_debut=date1.strftime("%Y-%m"),
            date_fin=date2.strftime("%Y-%m"),
            export_png=False
        )
    else:
        tracer_inflation_categories_mom(
            nom_fichier=NOM_FICHIER,
            date_debut=date1.strftime("%Y-%m"),
            date_fin=date2.strftime("%Y-%m"),
            export_png=False
        )

with col_right:
    st.subheader("📊 Contribution des catégories en point de pourcentage")

    if type_glissement == "Annuel":
        tracer_inflation_contributions_categories_yoy(
            nom_fichier=NOM_FICHIER,
            date_debut=date1.strftime("%Y-%m"),
            date_fin=date2.strftime("%Y-%m"),
            export_png=False
        )
    else:
        tracer_inflation_contributions_categories_mom(
            nom_fichier=NOM_FICHIER,
            date_debut=date1.strftime("%Y-%m"),
            date_fin=date2.strftime("%Y-%m"),
            export_png=False
        )

# ---- Navigation vers les autres pages ----
if selected == "Acceuil":
    st.switch_page("front.py")           # front.py est dans src/
elif selected == "Groupes":
    st.switch_page("pages/groupes.py")