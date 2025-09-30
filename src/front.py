import streamlit as st
from pathlib import Path
from PIL import Image
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import warnings
import locale

# ---- Import des fonctions de CALCUL ----
from calculator import (
    extraire_inflation_mom,
    extraire_inflation_yoy,
    get_max_date
)

# ---- Import des fonctions de VISUALISATION ----
from visualizer import (
    tracer_inflation_dashboard_yoy,
    tracer_inflation_dashboard_mom,
    tracer_contributions_core_noncore_yoy,
    tracer_contributions_core_noncore_mom
)

# ---- VÉRIFICATION D'AUTHENTIFICATION ----
if not st.session_state.get('authenticated', False):
    st.switch_page("pages/loginpage.py")

# ---- Page config ----
st.set_page_config(page_title="Dashboard", page_icon=":bar_chart:", layout="wide")

# Masquer le menu de navigation par défaut de Streamlit
hide_pages_style = """
<style>
div[data-testid="stSidebarNav"] {display: none;}
</style>
"""
st.markdown(hide_pages_style, unsafe_allow_html=True)

# Global CSS
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
    background-color: #0b1a2e; /* dark navy */
    color: white;
}
[data-testid="stSidebar"] * {
    color: white;
}
[data-testid="stSidebar"] a:hover {
    background-color:#0056a3; /* lighter navy on hover */
}
</style>
""", unsafe_allow_html=True)

st.title(":bar_chart: Tableau de bord - Bank d'Algérie")

# ------------------ NOUVELLES CONFIG DE CHEMINS -------------------
BASE_DIR = Path(__file__).parent  # = src/

# image
IMG_PATH = BASE_DIR / "bankofalgerialogo.png"

# Excel files
NOM_FICHIER = BASE_DIR / "Fichier_de_donnes.xlsx"
NOM_FICHIER2 = BASE_DIR / "Fichier_de_donnes_et_calculs.xlsx"

FEUILLE_GRAND_ALGER = "Grand_Alger"
FEUILLE_CORE = "core"
FEUILLE_NON_CORE = "Produits_agricoles_frais"
FEUILLE_CATEGORIES = "categories"

# ---- Sidebar ----
with st.sidebar:
    if IMG_PATH.exists():
        logo = Image.open(IMG_PATH)
        st.image(logo, use_container_width=True)
    else:
        st.error(f"Image non trouvée : {IMG_PATH}")

    selected = option_menu(
        None,
        ["Acceuil", "Groupes", "Catégories"],
        icons=[],
        menu_icon="cast", default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#0b1a2e"},
            "icon": {"color": "white", "font-size": "18px"},
            "nav-link": {"color": "white", "font-size": "16px",
                         "text-align": "center", "margin": "0px",
                         "--hover-color": "#0056a3"},
            "nav-link-selected": {"background-color": "#0056a3"},
        }
    )

# ---- Load data from Grand_Alger sheet ----
df = pd.read_excel(NOM_FICHIER, sheet_name=FEUILLE_GRAND_ALGER)
df["date"] = pd.to_datetime(df["date"])
startDate = df["date"].min()
endDate = df["date"].max()

col1, col2, col3 = st.columns([2, 2, 6])
with col1:
    region = st.selectbox("Portée", options=["Grand Alger", "National"])
with col2:
    type_glissement = st.selectbox("Type de glissement", options=["Annuel", "Mensuel"])
with col3:
    # Convert pandas.Timestamp → datetime.date
    startDate = df["date"].min().date()
    endDate = df["date"].max().date()
    date_range = st.slider(
        "Période",
        min_value=startDate, max_value=endDate,
        value=(startDate, endDate),
        format="YYYY-MM-DD"
    )
    # Convert back to datetime for filtering
    date1, date2 = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

df = df[(df["date"] >= date1) & (df["date"] <= date2)].copy()

# ---- Contributions ----
df_full = pd.read_excel(NOM_FICHIER, sheet_name=FEUILLE_CATEGORIES)

# ---- Nouvelles variables pour l'analyse ----
date_debut_str = date1.strftime("%Y-%m")
date_fin_str = date2.strftime("%Y-%m")

# ---- Layout ----
col_left, col_right = st.columns([1, 3])

with col_left:
    def kpi_card(title, value, delta, unit="%", up_color="#2ecc40", down_color="#ff4136"):
        arrow = "▲" if delta >= 0 else "▼"
        color = up_color if delta >= 0 else down_color
        return f"""
        <div style="
            background-color:#1b1b1b;
            padding:25px;
            border-radius:12px;
            text-align:center;
            width:100%;
            margin-bottom:15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        ">
            <div style="font-size:20px; color:#ffffff; font-weight:600;">{title}</div>
            <div style="font-size:42px; color:#ffffff; font-weight:700;">
                {value:.1f}{unit}
            </div>
            <div style="font-size:20px; color:{color}; font-weight:600;">
                {arrow} {abs(delta):.1f}{unit}
            </div>
        </div>
        """

    try:
        # ⚠️ Ici on utilise NOM_FICHIER2 pour les KPI
        inflation_now, inflation_prev = extraire_inflation_yoy(
            NOM_FICHIER2, FEUILLE_CATEGORIES, endDate.strftime("%Y-%m-%d")
        )
        core_now, core_prev = extraire_inflation_yoy(
            NOM_FICHIER2, FEUILLE_CORE, endDate.strftime("%Y-%m-%d")
        )
        noncore_now, noncore_prev = extraire_inflation_yoy(
            NOM_FICHIER2, FEUILLE_NON_CORE, endDate.strftime("%Y-%m-%d")
        )

        inflation_now = float(inflation_now.replace('%', ''))
        inflation_prev = float(inflation_prev)
        core_now = float(core_now.replace('%', ''))
        core_prev = float(core_prev)
        noncore_now = float(noncore_now.replace('%', ''))
        noncore_prev = float(noncore_prev)

    except Exception as e:
        st.error(f"Erreur lors du calcul des KPIs: {e}")
        inflation_now, inflation_prev, core_now, core_prev, noncore_now, noncore_prev = 0, 0, 0, 0, 0, 0

    st.markdown(kpi_card("Inflation", inflation_now, inflation_now - inflation_prev), unsafe_allow_html=True)
    st.markdown(kpi_card("Core", core_now, core_now - core_prev), unsafe_allow_html=True)
    st.markdown(kpi_card("Non Core", noncore_now, noncore_now - noncore_prev), unsafe_allow_html=True)

    # Camembert Core vs Non Core
    st.subheader("Répartition Core vs Non Core")
    noncore_calc = 100 - core_now  # complément

    fig_pie = go.Figure(
        data=[go.Pie(
            labels=['Core', 'Non Core'],
            values=[core_now, noncore_calc],
            hole=.4,
            marker=dict(colors=['#FFA500', '#228B22'])  # orange core, vert non-core
        )]
    )


    fig_pie.update_layout(
        template='plotly_dark',
        showlegend=True,
        margin=dict(l=1, r=1, t=30, b=1),
        height=250
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.subheader("📈 Inflation du Core, Non Core et Indice global")
    if type_glissement == "Annuel":
        fig = tracer_inflation_dashboard_yoy(
            nom_fichier=NOM_FICHIER,
            feuille_categories=FEUILLE_CATEGORIES,
            feuille_core=FEUILLE_CORE,
            feuille_non_core=FEUILLE_NON_CORE,
            date_debut=date_debut_str,
            date_fin=date_fin_str,
            export_png=False
        )
    else:
        fig = tracer_inflation_dashboard_mom(
            nom_fichier=NOM_FICHIER,
            feuille_categories=FEUILLE_CATEGORIES,
            feuille_core=FEUILLE_CORE,
            feuille_non_core=FEUILLE_NON_CORE,
            date_debut=date_debut_str,
            date_fin=date_fin_str,
            export_png=False
        )

    st.subheader("📊 Contribution du Core et Non Core à l'indice global")
    if type_glissement == "Annuel":
        fig_contrib = tracer_contributions_core_noncore_yoy(
            nom_fichier=NOM_FICHIER,
            feuille_categories=FEUILLE_CATEGORIES,
            date_debut=date_debut_str,
            date_fin=date_fin_str,
            export_png=False
        )
    else:
        fig_contrib = tracer_contributions_core_noncore_mom(
            nom_fichier=NOM_FICHIER,
            feuille_categories=FEUILLE_CATEGORIES,
            date_debut=date_debut_str,
            date_fin=date_fin_str,
            export_png=False
        )

# ---- Navigation automatique vers les autres pages ----
if selected == "Acceuil":
    st.switch_page("front.py")
elif selected == "Groupes":
    st.switch_page("pages/groupes.py")
elif selected == "Catégories":
    st.switch_page("pages/categories.py")
