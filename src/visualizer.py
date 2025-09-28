import os , json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import locale
import zipfile



def safe_read_excel(path, **kwargs):
    """Lit un fichier Excel, même s'il est contenu dans un .zip"""
    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            # prendre le premier .xlsx trouvé
            for name in z.namelist():
                if name.endswith(".xlsx") or name.endswith(".xls"):
                    with z.open(name) as f:
                        return pd.read_excel(f, engine="openpyxl", **kwargs)
        raise FileNotFoundError("Aucun .xlsx trouvé dans le zip")
    else:
        return pd.read_excel(path, engine="openpyxl", **kwargs)


def tracer_inflation_dashboard_yoy(nom_fichier: str,
                                   feuille_categories: str,
                                   feuille_core: str,
                                   feuille_non_core: str,
                                   date_debut: str,
                                   date_fin: str,
                                   export_png: bool = True):
    """
    Trace un graphique interactif (Plotly) de l'inflation IPC, Core et Non Core.
    Affiche le résultat dans Streamlit et enregistre une copie PNG si demandé.
    """

    # --- 1. Construire le chemin du fichier enrichi
    base, _ = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs.xlsx"

    # --- 2. Lire les résultats calculés
    df_global = safe_read_excel(fichier_calculs, sheet_name=feuille_categories,
                                index_col=0, parse_dates=True)
    df_core = safe_read_excel(fichier_calculs, sheet_name=feuille_core,
                              index_col=0, parse_dates=True)
    df_noncore = safe_read_excel(fichier_calculs, sheet_name=feuille_non_core,
                                 index_col=0, parse_dates=True)

    # --- 3. Trouver la colonne "Inflation (%, yoy)"
    def trouver_colonne_yoy(cols):
        cible = "Inflation (%, yoy)"
        for col in cols:
            if col.strip() == cible:
                return col
        return None

    col_global = trouver_colonne_yoy(df_global.columns)
    col_core = trouver_colonne_yoy(df_core.columns)
    col_noncore = trouver_colonne_yoy(df_noncore.columns)

    if not col_global or not col_core or not col_noncore:
        st.error("Impossible de trouver la colonne exacte 'Inflation (%, yoy)' dans l’un des fichiers Excel.")
        return None

    # --- 4. Gérer les bornes de dates
    first_valid_date = max(
        df_global.first_valid_index(),
        df_core.first_valid_index(),
        df_noncore.first_valid_index(),
    )

    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)

    real_start = max(first_valid_date, date_debut_dt)

    df_global = df_global.loc[real_start:date_fin_dt]
    df_core = df_core.loc[real_start:date_fin_dt]
    df_noncore = df_noncore.loc[real_start:date_fin_dt]

    # --- 5. Axe X avec labels en FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")  # Linux/Mac
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")  # Windows
        except:
            st.warning("⚠️ Impossible de définir la locale française, les mois resteront en anglais.")

    x = df_global.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")  # Ex: janv. 2023

    # --- 6. Création du graphique interactif
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x, y=df_global[col_global],
        mode="lines+markers",
        name="Inflation IPC",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC: %{y:.2f}%",
        text=x_labels
    ))

    fig.add_trace(go.Scatter(
        x=x, y=df_core[col_core],
        mode="lines+markers",
        name="Inflation Core",
        line=dict(color="#ff7f0e", width=2.0, dash="dash"),
        hovertemplate="Date: %{text}<br>Core: %{y:.2f}%",
        text=x_labels
    ))

    fig.add_trace(go.Scatter(
        x=x, y=df_noncore[col_noncore],
        mode="lines+markers",
        name="Inflation Non Core",
        line=dict(color="#2ca02c", width=2.0, dash="dot"),
        hovertemplate="Date: %{text}<br>Non Core: %{y:.2f}%",
        text=x_labels
    ))

    # Ligne horizontale cible
    fig.add_hline(
        y=4, line_dash="dash", line_color="red",
        annotation_text="Cible 4%", annotation_position="top right"
    )

    # Habillage
    fig.update_layout(
        title="Inflation IPC, core et non_core (%) - YoY",
        xaxis_title="Date",
        yaxis_title="Inflation annuelle (%)",
        template="plotly_white",
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=600,
    )

    fig.update_yaxes(ticksuffix=" %")

    # Alléger l’axe X → un tick par trimestre
    fig.update_xaxes(
        tickmode="array",
        tickvals=x[::3],
        ticktext=x_labels[::3]
    )

    # --- 7. Affichage Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # --- 8. Export PNG pour rapport
    # --- 7. Export PNG pour rapport
    if export_png:
        # Créer le dossier 'graphes' s'il n'existe pas
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)

        # Définir le chemin complet du fichier
        output_png = os.path.join(dossier_graphes, "inflation_core_noncore_yoy.png")

        # Sauvegarder l'image
        fig.write_image(output_png, width=1200, height=600, scale=2)


    return fig

def tracer_inflation_dashboard_mom(nom_fichier: str,
                                   feuille_categories: str,
                                   feuille_core: str,
                                   feuille_non_core: str,
                                   date_debut: str,
                                   date_fin: str,
                                   export_png: bool = True):
    """
    Trace un graphique interactif (Plotly) de l'inflation IPC, Core et Non Core en glissement mensuel (MoM).
    Les axes sont alignés pour que Core/Non-Core et IPC soient comparables.
    """

    import os, locale, pandas as pd, plotly.graph_objects as go, streamlit as st

    # --- 1. Construire le chemin du fichier enrichi
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 2. Lire les résultats calculés
    df_global = pd.read_excel(fichier_calculs, sheet_name=feuille_categories,
                              index_col=0, parse_dates=True)
    df_core = pd.read_excel(fichier_calculs, sheet_name=feuille_core,
                            index_col=0, parse_dates=True)
    df_noncore = pd.read_excel(fichier_calculs, sheet_name=feuille_non_core,
                               index_col=0, parse_dates=True)

    # --- 3. Trouver la colonne "Inflation (%, mom)"
    def trouver_colonne_mom(cols):
        cible = "Inflation (%, mom)"
        for col in cols:
            if col.strip() == cible:
                return col
        return None

    col_global = trouver_colonne_mom(df_global.columns)
    col_core = trouver_colonne_mom(df_core.columns)
    col_noncore = trouver_colonne_mom(df_noncore.columns)

    if not col_global or not col_core or not col_noncore:
        st.error("Impossible de trouver la colonne exacte 'Inflation (%, mom)' dans l’un des fichiers Excel.")
        return None

    # --- 4. Gérer les bornes de dates
    first_valid_date = max(
        df_global.first_valid_index(),
        df_core.first_valid_index(),
        df_noncore.first_valid_index(),
    )

    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)

    real_start = max(first_valid_date, date_debut_dt)

    df_global = df_global.loc[real_start:date_fin_dt]
    df_core = df_core.loc[real_start:date_fin_dt]
    df_noncore = df_noncore.loc[real_start:date_fin_dt]

    # --- 5. Axe X avec labels en FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")
        except:
            st.warning("⚠️ Impossible de définir la locale française, les mois resteront en anglais.")

    x = df_global.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 6. Création du graphique interactif
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x, y=df_global[col_global],
        mode="lines+markers",
        name="Inflation IPC (MoM)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC MoM: %{y:.2f}%",
        text=x_labels
    ))

    fig.add_trace(go.Scatter(
        x=x, y=df_core[col_core],
        mode="lines+markers",
        name="Inflation Core (MoM)",
        line=dict(color="#ff7f0e", width=2.0, dash="dash"),
        hovertemplate="Date: %{text}<br>Core MoM: %{y:.2f}%",
        text=x_labels
    ))

    fig.add_trace(go.Scatter(
        x=x, y=df_noncore[col_noncore],
        mode="lines+markers",
        name="Inflation Non Core (MoM)",
        line=dict(color="#2ca02c", width=2.0, dash="dot"),
        hovertemplate="Date: %{text}<br>Non Core MoM: %{y:.2f}%",
        text=x_labels
    ))

    # --- 7. Habillage
    fig.update_layout(
        title="Inflation IPC, core et non_core (%) - MoM",
        xaxis_title="Date",
        yaxis=dict(title="Inflation mensuelle (%)", ticksuffix=" %"),
        template="plotly_white",
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=600,
    )

    # Tick X un par trimestre
    fig.update_xaxes(tickmode="array", tickvals=x[::3], ticktext=x_labels[::3])

    # --- 8. Affichage Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG pour rapport
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "inflation_core_noncore_mom.png")
        fig.write_image(output_png, width=1200, height=600, scale=2)

    return fig


def tracer_contributions_core_noncore_yoy(nom_fichier: str,
                                                 feuille_categories: str,
                                                 date_debut: str,
                                                 date_fin: str,
                                                 export_png: bool = True):
    import os, locale, pandas as pd, plotly.graph_objects as go, streamlit as st

    # --- 1. Chemin du fichier
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 2. Lire les données
    df = pd.read_excel(fichier_calculs, sheet_name=feuille_categories,
                       index_col=0, parse_dates=True)

    colonnes_requises = ["Inflation (%, yoy)", "Contrib_Core_YoY (pp)", "Contrib_Non_Core_YoY (pp)"]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante : '{col}'")
            return None

    # --- 3. Bornes de dates
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)
    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 4. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")
        except:
            st.warning("⚠️ Locale FR non dispo, les mois resteront en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 5. Calcul plage y commune
    min_val = min(df["Inflation (%, yoy)"].min(),
                  df["Contrib_Core_YoY (pp)"].min(),
                  df["Contrib_Non_Core_YoY (pp)"].min())
    max_val = max(df["Inflation (%, yoy)"].max(),
                  df["Contrib_Core_YoY (pp)"].max(),
                  df["Contrib_Non_Core_YoY (pp)"].max())

    buffer = (max_val - min_val) * 0.1  # marge 10%
    y_range = [min_val - buffer, max_val + buffer]

    # --- 6. Graphique
    fig = go.Figure()

    # Ligne IPC
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, yoy)"],
        mode="lines+markers",
        name="Inflation IPC",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC: %{y:.2f} %",
        text=x_labels
    ))

    # Barres Core et Non-Core sur le même axe Y
    fig.add_trace(go.Bar(
        x=x, y=df["Contrib_Core_YoY (pp)"],
        name="Contribution Core",
        marker_color="#ff7f0e",
        hovertemplate="Date: %{text}<br>Core: %{y:.2f} pp",
        text=x_labels
    ))

    fig.add_trace(go.Bar(
        x=x, y=df["Contrib_Non_Core_YoY (pp)"],
        name="Contribution Non-Core",
        marker_color="#2ca02c",
        hovertemplate="Date: %{text}<br>Non-Core: %{y:.2f} pp",
        text=x_labels
    ))

    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et contributions core & non_core (YoY)",
        xaxis=dict(title="Date", tickmode="array", tickvals=x[::3], ticktext=x_labels[::3]),
        yaxis=dict(title="Inflation & Contributions (pp / %)", range=y_range),
        template="plotly_white",
        barmode="relative",  # stack mais négatif sous zéro
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=600
    )

    # --- 8. Affichage Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "contributions_inflation_core_noncore_yoy.png")
        fig.write_image(output_png, width=1200, height=600, scale=2)

    return fig

def tracer_contributions_core_noncore_mom(nom_fichier: str,
                                                 feuille_categories: str,
                                                 date_debut: str,
                                                 date_fin: str,
                                                 export_png: bool = True):

    # --- 1. Chemin du fichier
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 2. Lire les données
    df = pd.read_excel(fichier_calculs, sheet_name=feuille_categories,
                       index_col=0, parse_dates=True)

    colonnes_requises = ["Inflation (%, mom)", "Contrib_Core_MoM (pp)", "Contrib_Non_Core_MoM (pp)"]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante : '{col}'")
            return None

    # --- 3. Bornes de dates
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)
    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 4. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")
        except:
            st.warning("⚠️ Locale FR non dispo, les mois resteront en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 5. Calcul plage y commune
    min_val = min(df["Inflation (%, mom)"].min(),
                  df["Contrib_Core_MoM (pp)"].min(),
                  df["Contrib_Non_Core_MoM (pp)"].min())
    max_val = max(df["Inflation (%, mom)"].max(),
                  df["Contrib_Core_MoM (pp)"].max(),
                  df["Contrib_Non_Core_MoM (pp)"].max())
    buffer = (max_val - min_val) * 0.1
    y_range = [min_val - buffer, max_val + buffer]

    # --- 6. Graphique
    fig = go.Figure()

    # Ligne IPC
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, mom)"],
        mode="lines+markers",
        name="Inflation IPC (MoM)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC MoM: %{y:.2f} %",
        text=x_labels
    ))

    # Barres Core et Non-Core sur le même axe Y
    fig.add_trace(go.Bar(
        x=x, y=df["Contrib_Core_MoM (pp)"],
        name="Contribution Core",
        marker_color="#ff7f0e",
        hovertemplate="Date: %{text}<br>Core: %{y:.2f} pp",
        text=x_labels
    ))

    fig.add_trace(go.Bar(
        x=x, y=df["Contrib_Non_Core_MoM (pp)"],
        name="Contribution Non-Core",
        marker_color="#2ca02c",
        hovertemplate="Date: %{text}<br>Non-Core: %{y:.2f} pp",
        text=x_labels
    ))


    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et contributions core & non_core (MoM)",
        xaxis=dict(title="Date", tickmode="array", tickvals=x[::3], ticktext=x_labels[::3]),
        yaxis=dict(title="Inflation & Contributions (pp / %)", range=y_range),
        template="plotly_white",
        barmode="relative",
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=600
    )

    # --- 8. Affichage Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "contributions_inflation_core_noncore_yoy.png")
        fig.write_image(output_png, width=1200, height=600, scale=2)

    return fig

def tracer_inflation_grand_alger_mom(nom_fichier: str,
                                     date_debut: str,
                                     date_fin: str,
                                     export_png: bool = True):
    """
    Trace l'inflation IPC mensuelle (MoM) du Grand Alger
    ainsi que les 8 éléments du panier (définis dans config/categories.json).
    """

    # --- 1. Charger la config JSON (chemin intégré)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # remonte d'un dossier
    chemin_json = os.path.join(base_dir, "config", "categories.json")

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"❌ Fichier JSON introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Les 8 éléments du panier
    elements_panier = config.get("Grand_Alger", [])

    if not elements_panier:
        st.error("❌ Aucune catégorie trouvée dans config/categories.json")
        return None

    # --- 2. Construire le chemin du fichier enrichi
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 3. Lire les données Excel
    df = pd.read_excel(fichier_calculs, sheet_name="Grand_Alger",
                       index_col=0, parse_dates=True)

    # Vérification des colonnes
    colonnes_requises = ["Inflation (%, mom)"] + [
        f"Inflation_MoM (%)_{cat}" for cat in elements_panier
    ]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante dans Excel : {col}")
            return None

    # --- 4. Gestion des bornes temporelles
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)

    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 5. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")  # Linux/Mac
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")  # Windows
        except:
            st.warning("⚠️ Locale FR non disponible, mois en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 6. Graphique interactif
    fig = go.Figure()

    # IPC global
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, mom)"],
        mode="lines+markers",
        name="Inflation IPC (MoM)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC: %{y:.2f} %",
        text=x_labels
    ))

    # Les 8 éléments du panier
    couleurs = [
        "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22"
    ]

    for i, cat in enumerate(elements_panier):
        col_name = f"Inflation_MoM (%)_{cat}"
        fig.add_trace(go.Scatter(
            x=x, y=df[col_name],
            mode="lines+markers",
            name=cat,
            line=dict(width=2.0, dash="dot", color=couleurs[i % len(couleurs)]),
            hovertemplate=f"Date: %{{text}}<br>{cat}: %{{y:.2f}} %",
            text=x_labels
        ))

    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et Composantes du Panier (MoM) - Grand Alger",
        xaxis_title="Date",
        yaxis_title="Inflation mensuelle (%)",
        template="plotly_white",
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=700
    )

    # Axe Y en pourcentage
    fig.update_yaxes(ticksuffix=" %")

    # Alléger l’axe X → 1 tick par trimestre
    fig.update_xaxes(
        tickmode="array",
        tickvals=x[::3],
        ticktext=x_labels[::3]
    )

    # --- 8. Affichage
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "inflation_grand_alger_mom.png")
        fig.write_image(output_png, width=1200, height=700, scale=2)

    return fig

def tracer_inflation_grand_alger_yoy(nom_fichier: str,
                                     date_debut: str,
                                     date_fin: str,
                                     export_png: bool = True):
    """
    Trace l'inflation IPC annuelle (YoY) du Grand Alger
    ainsi que les 8 éléments du panier (définis dans config/categories.json).
    """

    # --- 1. Charger la config JSON (chemin intégré)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # remonte d'un dossier
    chemin_json = os.path.join(base_dir, "config", "categories.json")

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"❌ Fichier JSON introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Les 8 éléments du panier
    elements_panier = config.get("Grand_Alger", [])

    if not elements_panier:
        st.error("❌ Aucune catégorie trouvée dans config/categories.json")
        return None

    # --- 2. Construire le chemin du fichier enrichi
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 3. Lire les données Excel
    df = pd.read_excel(fichier_calculs, sheet_name="Grand_Alger",
                       index_col=0, parse_dates=True)

    # Vérification des colonnes
    colonnes_requises = ["Inflation (%, yoy)"] + [
        f"Inflation_YoY (%)_{cat}" for cat in elements_panier
    ]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante dans Excel : {col}")
            return None

    # --- 4. Gestion des bornes temporelles
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)

    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 5. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")  # Linux/Mac
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")  # Windows
        except:
            st.warning("⚠️ Locale FR non disponible, mois en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 6. Graphique interactif
    fig = go.Figure()

    # IPC global
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, yoy)"],
        mode="lines+markers",
        name="Inflation IPC (YoY)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC: %{y:.2f} %",
        text=x_labels
    ))

    # Les 8 éléments du panier
    couleurs = [
        "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22"
    ]

    for i, cat in enumerate(elements_panier):
        col_name = f"Inflation_YoY (%)_{cat}"
        fig.add_trace(go.Scatter(
            x=x, y=df[col_name],
            mode="lines+markers",
            name=cat,
            line=dict(width=2.0, dash="dot", color=couleurs[i % len(couleurs)]),
            hovertemplate=f"Date: %{{text}}<br>{cat}: %{{y:.2f}} %",
            text=x_labels
        ))

    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et Composantes du Panier (YoY) - Grand Alger",
        xaxis_title="Date",
        yaxis_title="Inflation annuelle (%)",
        template="plotly_white",
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=700
    )

    # Axe Y en pourcentage
    fig.update_yaxes(ticksuffix=" %")

    # Alléger l’axe X → 1 tick par trimestre
    fig.update_xaxes(
        tickmode="array",
        tickvals=x[::3],
        ticktext=x_labels[::3]
    )

    # --- 8. Affichage
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "inflation_grand_alger_yoy.png")
        fig.write_image(output_png, width=1200, height=700, scale=2)

    return fig

def tracer_inflation_contributions_grand_alger_mom(
    nom_fichier: str,
    date_debut: str,
    date_fin: str,
    export_png: bool = True
):
    """
    Trace l'inflation IPC (MoM) + contributions des éléments du panier (barres).
    """

    # --- 1. Charger config JSON (catégories)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    chemin_json = os.path.join(base_dir, "config", "categories.json")

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"❌ Fichier JSON introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        config = json.load(f)

    elements_panier = config.get("Grand_Alger", [])
    if not elements_panier:
        st.error("❌ Aucune catégorie trouvée dans config/categories.json")
        return None

    # --- 2. Construire chemin fichier enrichi
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 3. Charger données
    df = pd.read_excel(fichier_calculs, sheet_name="Grand_Alger",
                       index_col=0, parse_dates=True)

    colonnes_requises = ["Inflation (%, mom)"] + [
        f"Contrib_MoM_{cat} (pp)" for cat in elements_panier
    ]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante dans Excel : {col}")
            return None

    # --- 4. Bornes temporelles
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)
    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 5. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")
        except:
            st.warning("⚠️ Locale FR non dispo, mois en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 6. Graphique
    fig = go.Figure()

    # Ligne IPC
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, mom)"],
        mode="lines+markers",
        name="Inflation IPC (MoM)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC MoM: %{y:.2f} %",
        text=x_labels
    ))

    # Barres des contributions des 8 éléments
    couleurs = [
        "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22"
    ]

    for i, cat in enumerate(elements_panier):
        col_name = f"Contrib_MoM_{cat} (pp)"
        fig.add_trace(go.Bar(
            x=x, y=df[col_name],
            name=cat,
            marker_color=couleurs[i % len(couleurs)],
            hovertemplate=f"Date: %{{x|%b %Y}}<br>{cat}: %{{y:.2f}} pp"
        ))

    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et Contributions des Composantes - Grand Alger (MoM)",
        xaxis=dict(title="Date", tickmode="array", tickvals=x[::3], ticktext=x_labels[::3]),
        yaxis=dict(title="Inflation & Contributions (pp / %)", ticksuffix=" %"),
        template="plotly_white",
        barmode="relative",  # empilement
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=700
    )

    # --- 8. Affichage Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "inflation_contributions_grand_alger_mom.png")
        fig.write_image(output_png, width=1200, height=700, scale=2)

    return fig

def tracer_inflation_contributions_grand_alger_yoy(
    nom_fichier: str,
    date_debut: str,
    date_fin: str,
    export_png: bool = True
):
    """
    Trace l'inflation IPC (MoM) + contributions des éléments du panier (barres).
    """

    # --- 1. Charger config JSON (catégories)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    chemin_json = os.path.join(base_dir, "config", "categories.json")

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"❌ Fichier JSON introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        config = json.load(f)

    elements_panier = config.get("Grand_Alger", [])
    if not elements_panier:
        st.error("❌ Aucune catégorie trouvée dans config/categories.json")
        return None

    # --- 2. Construire chemin fichier enrichi
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 3. Charger données
    df = pd.read_excel(fichier_calculs, sheet_name="Grand_Alger",
                       index_col=0, parse_dates=True)

    colonnes_requises = ["Inflation (%, yoy)"] + [
        f"Contrib_YoY_{cat} (pp)" for cat in elements_panier
    ]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante dans Excel : {col}")
            return None

    # --- 4. Bornes temporelles
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)
    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 5. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")
        except:
            st.warning("⚠️ Locale FR non dispo, mois en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 6. Graphique
    fig = go.Figure()

    # Ligne IPC
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, yoy)"],
        mode="lines+markers",
        name="Inflation IPC (YoY)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC MoM: %{y:.2f} %",
        text=x_labels
    ))

    # Barres des contributions des 8 éléments
    couleurs = [
        "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22"
    ]

    for i, cat in enumerate(elements_panier):
        col_name = f"Contrib_YoY_{cat} (pp)"
        fig.add_trace(go.Bar(
            x=x, y=df[col_name],
            name=cat,
            marker_color=couleurs[i % len(couleurs)],
            hovertemplate=f"Date: %{{x|%b %Y}}<br>{cat}: %{{y:.2f}} pp"
        ))

    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et Contributions des Composantes - Grand Alger (YoY)",
        xaxis=dict(title="Date", tickmode="array", tickvals=x[::3], ticktext=x_labels[::3]),
        yaxis=dict(title="Inflation & Contributions (pp / %)", ticksuffix=" %"),
        template="plotly_white",
        barmode="relative",  # empilement
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=700
    )

    # --- 8. Affichage Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "inflation_contributions_grand_alger_yoy.png")
        fig.write_image(output_png, width=1200, height=700, scale=2)

    return fig


def tracer_inflation_national_mom(nom_fichier: str,
                                     date_debut: str,
                                     date_fin: str,
                                     export_png: bool = True):
    """
    Trace l'inflation IPC mensuelle (MoM) du National
    ainsi que les 8 éléments du panier (définis dans config/categories.json).
    """

    # --- 1. Charger la config JSON (chemin intégré)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # remonte d'un dossier
    chemin_json = os.path.join(base_dir, "config", "categories.json")

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"❌ Fichier JSON introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Les 8 éléments du panier
    elements_panier = config.get("national", [])

    if not elements_panier:
        st.error("❌ Aucune catégorie trouvée dans config/categories.json")
        return None

    # --- 2. Construire le chemin du fichier enrichi
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 3. Lire les données Excel
    df = pd.read_excel(fichier_calculs, sheet_name="national",
                       index_col=0, parse_dates=True)

    # Vérification des colonnes
    colonnes_requises = ["Inflation (%, mom)"] + [
        f"Inflation_MoM (%)_{cat}" for cat in elements_panier
    ]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante dans Excel : {col}")
            return None

    # --- 4. Gestion des bornes temporelles
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)

    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 5. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")  # Linux/Mac
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")  # Windows
        except:
            st.warning("⚠️ Locale FR non disponible, mois en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 6. Graphique interactif
    fig = go.Figure()

    # IPC global
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, mom)"],
        mode="lines+markers",
        name="Inflation IPC (MoM)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC: %{y:.2f} %",
        text=x_labels
    ))

    # Les 8 éléments du panier
    couleurs = [
        "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22"
    ]

    for i, cat in enumerate(elements_panier):
        col_name = f"Inflation_MoM (%)_{cat}"
        fig.add_trace(go.Scatter(
            x=x, y=df[col_name],
            mode="lines+markers",
            name=cat,
            line=dict(width=2.0, dash="dot", color=couleurs[i % len(couleurs)]),
            hovertemplate=f"Date: %{{text}}<br>{cat}: %{{y:.2f}} %",
            text=x_labels
        ))

    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et Composantes du Panier (MoM) - National",
        xaxis_title="Date",
        yaxis_title="Inflation mensuelle (%)",
        template="plotly_white",
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=700
    )

    # Axe Y en pourcentage
    fig.update_yaxes(ticksuffix=" %")

    # Alléger l’axe X → 1 tick par trimestre
    fig.update_xaxes(
        tickmode="array",
        tickvals=x[::3],
        ticktext=x_labels[::3]
    )

    # --- 8. Affichage
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "inflation_national_mom.png")
        fig.write_image(output_png, width=1200, height=700, scale=2)

    return fig

def tracer_inflation_national_yoy(nom_fichier: str,
                                     date_debut: str,
                                     date_fin: str,
                                     export_png: bool = True):
    """
    Trace l'inflation IPC annuelle (YoY) du National
    ainsi que les 8 éléments du panier (définis dans config/categories.json).
    """

    # --- 1. Charger la config JSON (chemin intégré)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # remonte d'un dossier
    chemin_json = os.path.join(base_dir, "config", "categories.json")

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"❌ Fichier JSON introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Les 8 éléments du panier
    elements_panier = config.get("national", [])

    if not elements_panier:
        st.error("❌ Aucune catégorie trouvée dans config/categories.json")
        return None

    # --- 2. Construire le chemin du fichier enrichi
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 3. Lire les données Excel
    df = pd.read_excel(fichier_calculs, sheet_name="national",
                       index_col=0, parse_dates=True)

    # Vérification des colonnes
    colonnes_requises = ["Inflation (%, yoy)"] + [
        f"Inflation_YoY (%)_{cat}" for cat in elements_panier
    ]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante dans Excel : {col}")
            return None

    # --- 4. Gestion des bornes temporelles
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)

    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 5. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")  # Linux/Mac
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")  # Windows
        except:
            st.warning("⚠️ Locale FR non disponible, mois en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 6. Graphique interactif
    fig = go.Figure()

    # IPC global
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, yoy)"],
        mode="lines+markers",
        name="Inflation IPC (YoY)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC: %{y:.2f} %",
        text=x_labels
    ))

    # Les 8 éléments du panier
    couleurs = [
        "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22"
    ]

    for i, cat in enumerate(elements_panier):
        col_name = f"Inflation_YoY (%)_{cat}"
        fig.add_trace(go.Scatter(
            x=x, y=df[col_name],
            mode="lines+markers",
            name=cat,
            line=dict(width=2.0, dash="dot", color=couleurs[i % len(couleurs)]),
            hovertemplate=f"Date: %{{text}}<br>{cat}: %{{y:.2f}} %",
            text=x_labels
        ))

    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et Composantes du Panier (YoY) - National",
        xaxis_title="Date",
        yaxis_title="Inflation annuelle (%)",
        template="plotly_white",
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=700
    )

    # Axe Y en pourcentage
    fig.update_yaxes(ticksuffix=" %")

    # Alléger l’axe X → 1 tick par trimestre
    fig.update_xaxes(
        tickmode="array",
        tickvals=x[::3],
        ticktext=x_labels[::3]
    )

    # --- 8. Affichage
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "inflation_national_yoy.png")
        fig.write_image(output_png, width=1200, height=700, scale=2)

    return fig

def tracer_inflation_contributions_national_mom(
    nom_fichier: str,
    date_debut: str,
    date_fin: str,
    export_png: bool = True
):
    """
    Trace l'inflation IPC (MoM) + contributions des éléments du panier (barres).
    """

    # --- 1. Charger config JSON (catégories)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    chemin_json = os.path.join(base_dir, "config", "categories.json")

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"❌ Fichier JSON introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        config = json.load(f)

    elements_panier = config.get("national", [])
    if not elements_panier:
        st.error("❌ Aucune catégorie trouvée dans config/categories.json")
        return None

    # --- 2. Construire chemin fichier enrichi
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 3. Charger données
    df = pd.read_excel(fichier_calculs, sheet_name="national",
                       index_col=0, parse_dates=True)

    colonnes_requises = ["Inflation (%, mom)"] + [
        f"Contrib_MoM_{cat} (pp)" for cat in elements_panier
    ]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante dans Excel : {col}")
            return None

    # --- 4. Bornes temporelles
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)
    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 5. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")
        except:
            st.warning("⚠️ Locale FR non dispo, mois en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 6. Graphique
    fig = go.Figure()

    # Ligne IPC
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, mom)"],
        mode="lines+markers",
        name="Inflation IPC (MoM)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC MoM: %{y:.2f} %",
        text=x_labels
    ))

    # Barres des contributions des 8 éléments
    couleurs = [
        "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22"
    ]

    for i, cat in enumerate(elements_panier):
        col_name = f"Contrib_MoM_{cat} (pp)"
        fig.add_trace(go.Bar(
            x=x, y=df[col_name],
            name=cat,
            marker_color=couleurs[i % len(couleurs)],
            hovertemplate=f"Date: %{{x|%b %Y}}<br>{cat}: %{{y:.2f}} pp"
        ))

    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et Contributions des Composantes - National (MoM)",
        xaxis=dict(title="Date", tickmode="array", tickvals=x[::3], ticktext=x_labels[::3]),
        yaxis=dict(title="Inflation & Contributions (pp / %)", ticksuffix=" %"),
        template="plotly_white",
        barmode="relative",  # empilement
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=700
    )

    # --- 8. Affichage Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "inflation_contributions_national_mom.png")
        fig.write_image(output_png, width=1200, height=700, scale=2)

    return fig

def tracer_inflation_contributions_national_yoy(
    nom_fichier: str,
    date_debut: str,
    date_fin: str,
    export_png: bool = True
):
    """
    Trace l'inflation IPC (MoM) + contributions des éléments du panier (barres).
    """

    # --- 1. Charger config JSON (catégories)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    chemin_json = os.path.join(base_dir, "config", "categories.json")

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"❌ Fichier JSON introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        config = json.load(f)

    elements_panier = config.get("national", [])
    if not elements_panier:
        st.error("❌ Aucune catégorie trouvée dans config/categories.json")
        return None

    # --- 2. Construire chemin fichier enrichi
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 3. Charger données
    df = pd.read_excel(fichier_calculs, sheet_name="national",
                       index_col=0, parse_dates=True)

    colonnes_requises = ["Inflation (%, mom)"] + [
        f"Contrib_YoY_{cat} (pp)" for cat in elements_panier
    ]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante dans Excel : {col}")
            return None

    # --- 4. Bornes temporelles
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)
    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 5. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")
        except:
            st.warning("⚠️ Locale FR non dispo, mois en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 6. Graphique
    fig = go.Figure()

    # Ligne IPC
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, yoy)"],
        mode="lines+markers",
        name="Inflation IPC (YoY)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC MoM: %{y:.2f} %",
        text=x_labels
    ))

    # Barres des contributions des 8 éléments
    couleurs = [
        "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22"
    ]

    for i, cat in enumerate(elements_panier):
        col_name = f"Contrib_YoY_{cat} (pp)"
        fig.add_trace(go.Bar(
            x=x, y=df[col_name],
            name=cat,
            marker_color=couleurs[i % len(couleurs)],
            hovertemplate=f"Date: %{{x|%b %Y}}<br>{cat}: %{{y:.2f}} pp"
        ))

    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et Contributions des Composantes - National (YOY)",
        xaxis=dict(title="Date", tickmode="array", tickvals=x[::3], ticktext=x_labels[::3]),
        yaxis=dict(title="Inflation & Contributions (pp / %)", ticksuffix=" %"),
        template="plotly_white",
        barmode="relative",  # empilement
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=700
    )

    # --- 8. Affichage Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "inflation_contributions_national_yoy.png")
        fig.write_image(output_png, width=1200, height=700, scale=2)

    return fig

def tracer_inflation_categories_mom(nom_fichier: str,
                                    date_debut: str,
                                    date_fin: str,
                                    export_png: bool = True):
    """
    Trace l'inflation IPC mensuelle (MoM) du panier 'categories'
    ainsi que ses 3 éléments (définis dans config/categories.json).
    """

    # --- 1. Charger la config JSON (chemin intégré)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # remonte d'un dossier
    chemin_json = os.path.join(base_dir, "config", "categories.json")

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"❌ Fichier JSON introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Les 3 éléments du panier "categories"
    elements_panier = config.get("categories", [])

    if not elements_panier:
        st.error("❌ Aucune catégorie trouvée dans config/categories.json pour 'categories'")
        return None

    # --- 2. Construire le chemin du fichier enrichi
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 3. Lire les données Excel
    df = pd.read_excel(fichier_calculs, sheet_name="categories",
                       index_col=0, parse_dates=True)

    # Vérification des colonnes
    colonnes_requises = ["Inflation (%, mom)"] + [
        f"Inflation_MoM (%)_{cat}" for cat in elements_panier
    ]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante dans Excel : {col}")
            return None

    # --- 4. Gestion des bornes temporelles
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)

    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 5. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")  # Linux/Mac
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")  # Windows
        except:
            st.warning("⚠️ Locale FR non disponible, mois en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 6. Graphique interactif
    fig = go.Figure()

    # IPC global du panier "categories"
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, mom)"],
        mode="lines+markers",
        name="Inflation IPC (MoM)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC: %{y:.2f} %",
        text=x_labels
    ))

    # Les 3 éléments du panier
    couleurs = ["#e41a1c", "#377eb8", "#4daf4a"]  # palette spéciale 3 couleurs

    for i, cat in enumerate(elements_panier):
        col_name = f"Inflation_MoM (%)_{cat}"
        fig.add_trace(go.Scatter(
            x=x, y=df[col_name],
            mode="lines+markers",
            name=cat,
            line=dict(width=2.0, dash="dot", color=couleurs[i]),
            hovertemplate=f"Date: %{{text}}<br>{cat}: %{{y:.2f}} %",
            text=x_labels
        ))

    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et des composantes par catégories (MoM)",
        xaxis_title="Date",
        yaxis_title="Inflation mensuelle (%)",
        template="plotly_white",
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=700
    )

    # Axe Y en pourcentage
    fig.update_yaxes(ticksuffix=" %")

    # Alléger l’axe X → 1 tick par trimestre
    fig.update_xaxes(
        tickmode="array",
        tickvals=x[::3],
        ticktext=x_labels[::3]
    )

    # --- 8. Affichage
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "inflation_catégories_mom.png")
        fig.write_image(output_png, width=1200, height=700, scale=2)

    return fig

def tracer_inflation_categories_yoy(nom_fichier: str,
                                    date_debut: str,
                                    date_fin: str,
                                    export_png: bool = True):
    """
    Trace l'inflation IPC mensuelle (MoM) du panier 'categories'
    ainsi que ses 3 éléments (définis dans config/categories.json).
    """

    # --- 1. Charger la config JSON (chemin intégré)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # remonte d'un dossier
    chemin_json = os.path.join(base_dir, "config", "categories.json")

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"❌ Fichier JSON introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Les 3 éléments du panier "categories"
    elements_panier = config.get("categories", [])

    if not elements_panier:
        st.error("❌ Aucune catégorie trouvée dans config/categories.json pour 'categories'")
        return None

    # --- 2. Construire le chemin du fichier enrichi
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 3. Lire les données Excel
    df = pd.read_excel(fichier_calculs, sheet_name="categories",
                       index_col=0, parse_dates=True)

    # Vérification des colonnes
    colonnes_requises = ["Inflation (%, yoy)"] + [
        f"Inflation_YoY (%)_{cat}" for cat in elements_panier
    ]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante dans Excel : {col}")
            return None

    # --- 4. Gestion des bornes temporelles
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)

    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 5. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")  # Linux/Mac
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")  # Windows
        except:
            st.warning("⚠️ Locale FR non disponible, mois en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 6. Graphique interactif
    fig = go.Figure()

    # IPC global du panier "categories"
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, yoy)"],
        mode="lines+markers",
        name="Inflation IPC (YoY)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC: %{y:.2f} %",
        text=x_labels
    ))

    # Les 3 éléments du panier
    couleurs = ["#e41a1c", "#377eb8", "#4daf4a"]  # palette spéciale 3 couleurs

    for i, cat in enumerate(elements_panier):
        col_name = f"Inflation_YoY (%)_{cat}"
        fig.add_trace(go.Scatter(
            x=x, y=df[col_name],
            mode="lines+markers",
            name=cat,
            line=dict(width=2.0, dash="dot", color=couleurs[i]),
            hovertemplate=f"Date: %{{text}}<br>{cat}: %{{y:.2f}} %",
            text=x_labels
        ))

    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et des composantes par catégories (YoY)",
        xaxis_title="Date",
        yaxis_title="Inflation annuelle (%)",
        template="plotly_white",
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=700
    )

    # Axe Y en pourcentage
    fig.update_yaxes(ticksuffix=" %")

    # Alléger l’axe X → 1 tick par trimestre
    fig.update_xaxes(
        tickmode="array",
        tickvals=x[::3],
        ticktext=x_labels[::3]
    )

    # --- 8. Affichage
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "inflation_catégories_yoy.png")
        fig.write_image(output_png, width=1200, height=700, scale=2)

    return fig

def tracer_inflation_contributions_categories_mom(
    nom_fichier: str,
    date_debut: str,
    date_fin: str,
    export_png: bool = True
):
    """
    Trace l'inflation IPC (MoM) + contributions des éléments du panier (barres).
    """

    # --- 1. Charger config JSON (catégories)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    chemin_json = os.path.join(base_dir, "config", "categories.json")

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"❌ Fichier JSON introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        config = json.load(f)

    elements_panier = config.get("categories", [])
    if not elements_panier:
        st.error("❌ Aucune catégorie trouvée dans config/categories.json")
        return None

    # --- 2. Construire chemin fichier enrichi
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 3. Charger données
    df = pd.read_excel(fichier_calculs, sheet_name="categories",
                       index_col=0, parse_dates=True)

    colonnes_requises = ["Inflation (%, mom)"] + [
        f"Contrib_MoM_{cat} (pp)" for cat in elements_panier
    ]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante dans Excel : {col}")
            return None

    # --- 4. Bornes temporelles
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)
    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 5. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")
        except:
            st.warning("⚠️ Locale FR non dispo, mois en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 6. Graphique
    fig = go.Figure()

    # Ligne IPC
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, mom)"],
        mode="lines+markers",
        name="Inflation IPC (MoM)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC MoM: %{y:.2f} %",
        text=x_labels
    ))

    # Barres des contributions des 8 éléments
    couleurs = ["#e41a1c", "#377eb8", "#4daf4a"]

    for i, cat in enumerate(elements_panier):
        col_name = f"Contrib_MoM_{cat} (pp)"
        fig.add_trace(go.Bar(
            x=x, y=df[col_name],
            name=cat,
            marker_color=couleurs[i % len(couleurs)],
            hovertemplate=f"Date: %{{x|%b %Y}}<br>{cat}: %{{y:.2f}} pp"
        ))

    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et Contributions des Composantes - Catégories (MoM)",
        xaxis=dict(title="Date", tickmode="array", tickvals=x[::3], ticktext=x_labels[::3]),
        yaxis=dict(title="Inflation & Contributions (pp / %)", ticksuffix=" %"),
        template="plotly_white",
        barmode="relative",  # empilement
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=700
    )

    # --- 8. Affichage Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "inflation_contributions_catégories_mom.png")
        fig.write_image(output_png, width=1200, height=700, scale=2)

    return fig

def tracer_inflation_contributions_categories_yoy(
    nom_fichier: str,
    date_debut: str,
    date_fin: str,
    export_png: bool = True
):
    """
    Trace l'inflation IPC (MoM) + contributions des éléments du panier (barres).
    """

    # --- 1. Charger config JSON (catégories)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    chemin_json = os.path.join(base_dir, "config", "categories.json")

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"❌ Fichier JSON introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        config = json.load(f)

    elements_panier = config.get("categories", [])
    if not elements_panier:
        st.error("❌ Aucune catégorie trouvée dans config/categories.json")
        return None

    # --- 2. Construire chemin fichier enrichi
    base, ext = os.path.splitext(nom_fichier)
    fichier_calculs = base + "_et_calculs" + ext

    # --- 3. Charger données
    df = pd.read_excel(fichier_calculs, sheet_name="categories",
                       index_col=0, parse_dates=True)

    colonnes_requises = ["Inflation (%, yoy)"] + [
        f"Contrib_YoY_{cat} (pp)" for cat in elements_panier
    ]
    for col in colonnes_requises:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante dans Excel : {col}")
            return None

    # --- 4. Bornes temporelles
    first_valid_date = df.first_valid_index()
    date_debut_dt = pd.to_datetime(date_debut)
    date_fin_dt = pd.to_datetime(date_fin) + pd.offsets.MonthEnd(1)
    real_start = max(first_valid_date, date_debut_dt)
    df = df.loc[real_start:date_fin_dt]

    # --- 5. Axe X FR
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except:
        try:
            locale.setlocale(locale.LC_TIME, "French_France.1252")
        except:
            st.warning("⚠️ Locale FR non dispo, mois en anglais.")

    x = df.index.to_period("M").to_timestamp(how="start")
    x_labels = x.strftime("%b %Y")

    # --- 6. Graphique
    fig = go.Figure()

    # Ligne IPC
    fig.add_trace(go.Scatter(
        x=x, y=df["Inflation (%, yoy)"],
        mode="lines+markers",
        name="Inflation IPC (YoY)",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate="Date: %{text}<br>IPC YoY: %{y:.2f} %",
        text=x_labels
    ))

    # Barres des contributions des 8 éléments
    couleurs = ["#e41a1c", "#277eb8", "#4daf4a"]

    for i, cat in enumerate(elements_panier):
        col_name = f"Contrib_YoY_{cat} (pp)"
        fig.add_trace(go.Bar(
            x=x, y=df[col_name],
            name=cat,
            marker_color=couleurs[i % len(couleurs)],
            hovertemplate=f"Date: %{{x|%b %Y}}<br>{cat}: %{{y:.2f}} pp"
        ))

    # --- 7. Layout
    fig.update_layout(
        title="Inflation IPC et Contributions des Composantes - Catégories (YoY)",
        xaxis=dict(title="Date", tickmode="array", tickvals=x[::3], ticktext=x_labels[::3]),
        yaxis=dict(title="Inflation & Contributions (pp / %)", ticksuffix=" %"),
        template="plotly_white",
        barmode="relative",  # empilement
        legend=dict(title="", orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified",
        height=700
    )

    # --- 8. Affichage Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. Export PNG
    if export_png:
        dossier_graphes = "graphes"
        os.makedirs(dossier_graphes, exist_ok=True)
        output_png = os.path.join(dossier_graphes, "inflation_contributions_catégories_yoy.png")
        fig.write_image(output_png, width=1200, height=700, scale=2)

    return fig


# --- Lancement direct ---
if __name__ == "__main__":
    # --- Paramètres de test ---
    nom_fichier = "Fichier_de_donnes.xlsx"
    date_debut = "2023-01"
    date_fin = "2025-07"

    # --- Appel de la fonction ---
    fig = tracer_inflation_dashboard_yoy(
        nom_fichier=nom_fichier,
        date_debut=date_debut,
        date_fin=date_fin,
        export_png=True
    )

    # Vérification retour
    if fig:
        print("✅ Graphe généré avec succès.")
    else:
        print("❌ Erreur lors de la génération du graphe.")



