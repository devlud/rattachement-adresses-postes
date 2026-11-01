import pandas as pd
import pytest

from rattachement.perimetre import ajouter_distributeur, preparer_distributeurs


def test_preparer_distributeurs():
    liste = pd.DataFrame(
        {
            "code_insee_commune": ["69381", "67482", "00001", "00002"],
            "GRD_ELEC": ["Enedis", "Strasbourg Électricité Réseaux", "Deux distributeurs", None],
            "code_grd_elec_1": ["ENED", "ESR", "XXX", None],
            "code_grd_elec_2": [None, None, "ENED", None],
        }
    )
    distributeurs = preparer_distributeurs(liste)
    assert list(distributeurs["code_insee"]) == ["69381", "67482", "00001", "00002"]
    # Enedis seul ; un autre distributeur ; Enedis en second distributeur ; aucun distributeur
    assert list(distributeurs["enedis"]) == [True, False, True, False]
    # Seule la troisième commune a deux distributeurs
    assert list(distributeurs["commune_mixte"]) == [False, False, True, False]


# Trois communes de la liste : Lyon 1er (Enedis), Strasbourg (une ELD), une commune mixte
DISTRIBUTEURS = pd.DataFrame(
    {
        "code_insee": ["69381", "67482", "00001"],
        "distributeur": ["Enedis", "Strasbourg Électricité Réseaux", "Enedis,GÉRÉDIS"],
        "enedis": [True, False, True],
        "commune_mixte": [False, False, True],
    }
)


def test_ajouter_distributeur():
    adresses = pd.DataFrame(
        {"id": ["a1", "a2", "a3", "a4"], "code_insee": ["69381", "67482", "00001", "99999"]}
    )
    resultat = ajouter_distributeur(adresses, DISTRIBUTEURS)
    assert list(resultat["id"]) == ["a1", "a2", "a3", "a4"]  # toutes les adresses sont gardées
    assert resultat["distributeur"].iloc[1] == "Strasbourg Électricité Réseaux"
    assert pd.isna(resultat["distributeur"].iloc[3])  # commune 99999 absente de la liste
    assert list(resultat["enedis"]) == [True, False, True, False]
    assert list(resultat["commune_mixte"]) == [False, False, True, False]


def test_commune_en_double_refusee():
    en_double = pd.concat([DISTRIBUTEURS, DISTRIBUTEURS.iloc[[0]]])  # Lyon 1er deux fois
    adresses = pd.DataFrame({"id": ["a1"], "code_insee": ["69381"]})
    with pytest.raises(pd.errors.MergeError):
        ajouter_distributeur(adresses, en_double)
