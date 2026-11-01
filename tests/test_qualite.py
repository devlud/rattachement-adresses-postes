import pandas as pd

from rattachement.qualite import controler_adresses


def adresse(identifiant, **modifications):
    """Une adresse valide, à Lyon. On peut modifier certaines colonnes pour la rendre fausse."""
    ligne = {
        "id": identifiant,
        "code_insee": "69381",
        "x": 842_000.0,
        "y": 6_519_000.0,
        "lon": 4.83,
        "lat": 45.76,
    }
    ligne.update(modifications)
    return ligne


def test_adresse_valide_conservee():
    valides, mises_de_cote = controler_adresses(pd.DataFrame([adresse("a1")]))
    assert len(valides) == 1
    assert len(mises_de_cote) == 0


def test_doublon_d_identifiant_retire():
    tableau = pd.DataFrame([adresse("a1"), adresse("a1", x=842_010.0)])  # même id, autre position
    valides, _ = controler_adresses(tableau)
    assert len(valides) == 1
    assert valides["x"].iloc[0] == 842_000.0  # c'est la première ligne qui est gardée


def test_adresses_invalides_mises_de_cote():
    tableau = pd.DataFrame(
        [
            adresse("a1"),
            adresse("a2", lat=95.0),  # latitude impossible
            adresse("a3", x=None),  # coordonnée manquante
            adresse("a4", code_insee="ABCDE"),  # code INSEE mal formé
        ]
    )
    valides, mises_de_cote = controler_adresses(tableau)
    assert list(valides["id"]) == ["a1"]
    assert sorted(mises_de_cote["id"]) == ["a2", "a3", "a4"]
