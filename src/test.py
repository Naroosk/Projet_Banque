import json
from pathlib import Path
from load_data import extraire_poids  # ta fonction


def test_afficher_poids():
    """
    Test : charger les poids de weights.json et les afficher pour une feuille donnée.
    """
    feuille = "categories"  # <-- adapte selon ton fichier Excel

    # Chemin vers config/weights.json
    BASE_DIR = Path(__file__).resolve().parent.parent
    CONFIG_PATH = BASE_DIR / "config" / "weights.json"

    # Charger le fichier JSON
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        all_weights = json.load(f)

    # Extraire les poids pour la feuille demandée
    poids = extraire_poids(all_weights.get(feuille, {}))

    # Vérifications simples
    assert poids, f"Aucun poids trouvé pour la feuille {feuille}"
    print(f"Poids pour la feuille '{feuille}':")
    for categorie, valeur in poids.items():
        print(f"  - {categorie} : {valeur}")

    # Vérifier que la somme ≈ 100
    total = sum(poids.values())
    print(f"\nSomme des poids = {total}")
    assert abs(total - 100) < 1e-6, "⚠️ Les poids ne totalisent pas 100"

