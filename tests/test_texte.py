import pandas as pd
import pytest

from rattachement.texte import libelles_ban, normaliser


# Le même test est lancé une fois par exemple : (texte saisi, résultat attendu)
@pytest.mark.parametrize(
    ("saisie", "attendu"),
    [
        ("12 bis av. Jean-Jaurès", "12 BIS AVENUE JEAN JAURES"),  # abréviation, accent, tiret
        ("12bis rue St-Éloi", "12 BIS RUE SAINT ELOI"),  # numéro collé à l'indice
        ("3 Bd de l'Hôpital", "3 BOULEVARD DE L HOPITAL"),  # apostrophe
        ("RD386", "ROUTE DEPARTEMENTALE 386"),  # lettres collées au numéro
        ("  Place   des Terreaux ", "PLACE DES TERREAUX"),  # espaces en trop
        ("Œuvre de Notre-Dame", "OEUVRE DE NOTRE DAME"),  # ligature
    ],
)
def test_normaliser(saisie, attendu):
    assert normaliser(saisie) == attendu


def test_case_vide():
    assert normaliser(None) == ""


def test_libelles_ban():
    adresses = pd.DataFrame(
        {
            "numero": [12, 3],
            "rep": ["bis", None],
            "nom_voie": ["Avenue Jean-Jaurès", "Rue de la Félodière"],
        }
    )
    assert list(libelles_ban(adresses)) == ["12 BIS AVENUE JEAN JAURES", "3 RUE DE LA FELODIERE"]
