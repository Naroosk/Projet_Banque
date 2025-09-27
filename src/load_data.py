import pandas as pd

def lire_feuille_wide(nom_fichier: str, feuille: str) -> pd.DataFrame:
    """
    Lit une feuille Excel en format large (wide) et prépare la série temporelle.

    Args:
        nom_fichier (str): chemin du fichier Excel.
        feuille (str): nom de la feuille à lire.

    Returns:
        pd.DataFrame: DataFrame avec 'Date' comme index et colonnes = catégories.
    """
    # Charger la feuille
    df = pd.read_excel(nom_fichier, sheet_name=feuille)

    # Renommer la première colonne en "Date" (sécurité)
    df.rename(columns={df.columns[0]: "Date"}, inplace=True)

    # Conversion en datetime (format jour/mois/année dans ton fichier)
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")

    # Mettre Date comme index
    df.set_index("Date", inplace=True)

    return df

def extraire_poids(poids_dict):
    """
    Extrait les poids depuis un dictionnaire ou un float.
    Retourne un dict plat : {colonne: poids}.
    """
    result = {}

    for key, value in poids_dict.items():
        # Cas 1 : poids direct (float ou int)
        if isinstance(value, (int, float)):
            result[key] = value

        # Cas 2 : dictionnaire avec "Poids" et éventuellement "Subcategories"
        elif isinstance(value, dict):
            if "Poids" in value:  # poids principal
                result[key] = value["Poids"]

            if "Subcategories" in value:  # descendre dans les sous-catégories
                for sub_key, sub_val in value["Subcategories"].items():
                    result[sub_key] = sub_val

        else:
            print(f"⚠️ Format inattendu pour {key}: {value}")

    return result

