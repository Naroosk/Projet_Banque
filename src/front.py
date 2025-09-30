import streamlit as st
from streamlit_option_menu import option_menu
import plotly.graph_objects as go
import datetime
from dashboard import (
    tracer_inflation_dashboard_yoy,
    tracer_inflation_dashboard_mom,
    tracer_contributions_core_noncore_yoy,
    tracer_contributions_core_noncore_mom
)

# ============================
# Configuration Streamlit
# ============================
st.set_page_config(page_title="Dashboard Banque", page_icon=":bar_chart:", layout="wide")

# ============================
# Variables globales
# ============================
NOM_FICHIER = "fichier2.xlsx"   # <-- fichier modifié
FEUILLE_CATEGORIES = "Categories"
FEUILLE_CORE = "Core"
FEUILLE_NON_CORE = "Non Core"

# ============================
# Sidebar
# ============================
with st.sidebar:
    selected = option_menu(
        "Menu",
        ["Dashboard"],
        icons=["bar-chart"],
        menu_icon="cast",
        default_index=0
    )

# ============================
# Contenu principal
# ============================
if selected == "Dashboard":
    st.title("📊 Tableau de bord Inflation")

    # ============================
    # Période de filtrage
    # ============================
    today = datetime.date.today()
    date_debut = st.date_input("Date de début", today.replace(year=today.year - 1))
    date_fin = st.date_input("Date de fin", today)

    date_debut_str = date_debut.strftime("%Y-%m-%d")
    date_fin_str = date_fin.strftime("%Y-%m-%d")

    type_glissement = st.radio("Type de glissement :", ["Annuel", "Mensuel"])

    # ============================
    # Colonnes
    # ============================
    col_left, col_right = st.columns([1, 2])

    with col_left:
        # ===== KPI Inflation globale =====
        st.subheader("Inflation Globale")
        inflation_globale = 7.5  # 🔧 à remplacer par ta fonction de calcul
        st.metric(label="Inflation", value=f"{inflation_globale:.1f}%")

        # ===== Camembert Core vs Non Core =====
        st.subheader("Répartition Core vs Non Core")
        core_now = 60  # 🔧 à remplacer par ton extraction du fichier2
        noncore_calc = 100 - core_now

        fig_pie = go.Figure(
            data=[go.Pie(
                labels=['Core', 'Non Core'],
                values=[core_now, noncore_calc],
                hole=.4,
                marker=dict(colors=['#FFA500', '#228B22'])
            )]
        )
        fig_pie.update_layout(
            template='plotly_dark',
            showlegend=True,
            margin=dict(l=1, r=1, t=30, b=1),
            height=250
        )
        st.plotly_chart(fig_pie, use_container_width=True, key="pie_chart")

    with col_right:
        # ===== Inflation Core / Non Core / Global =====
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

        st.plotly_chart(fig, use_container_width=True, key="inflation_chart")

        # ===== Contributions Core / Non Core =====
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

        st.plotly_chart(fig_contrib, use_container_width=True, key="contrib_chart")
