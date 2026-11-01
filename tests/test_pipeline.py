import pandas as pd
import pytest

from rattachement.config import DEPARTEMENTS
from rattachement.pipeline import choisir_departements, enrichir
from rattachement.plus_proche import preparer_postes


def test_choisir_tous_les_departements():
    assert choisir_departements(["tous"]) == DEPARTEMENTS


def test_choisir_quelques_departements():
    assert choisir_departements(["69", "01", "38"]) == ["69", "01", "38"]


# Refusés : rien d'écrit, « 1 » au lieu de « 01 », la Corse (que n'alimente pas Enedis)
@pytest.mark.parametrize("arguments", [[], ["1"], ["69", "2A"]])
def test_departements_refuses(arguments):
    with pytest.raises(ValueError):
        choisir_departements(arguments)


def test_enrichir():
    adresses = pd.DataFrame(
        {
            "id": ["a1", "a2"],
            "numero": [12, 3],
            "rep": ["bis", None],
            "nom_voie": ["Avenue Jean-Jaurès", "Rue de la Paix"],
            "x": [842_003.0, 872_000.0],
            "y": [6_519_004.0, 6_519_000.0],
        }
    )
    postes = preparer_postes(pd.DataFrame({"X": [842_000.0], "Y": [6_519_000.0]}))  # un seul
    resultat = enrichir(adresses, postes)
    assert list(resultat["libelle"]) == ["12 BIS AVENUE JEAN JAURES", "3 RUE DE LA PAIX"]
    assert list(resultat["poste_id"]) == ["842000_6519000", "842000_6519000"]
    assert list(resultat["distance_m"]) == pytest.approx([5.0, 30_000.0])  # 5 m, puis 30 km
    assert list(resultat["hors_seuil"]) == [False, True]  # à 30 km : rattachement suspect
