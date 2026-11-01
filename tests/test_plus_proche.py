import pandas as pd
import pytest

from rattachement.plus_proche import preparer_postes, rattacher


def test_identifiant_et_doublons():
    bruts = pd.DataFrame(
        {
            "X": [976992.78, 976992.78, 842000.4],  # les deux premiers postes sont au même endroit
            "Y": [6273892.52, 6273892.52, 6519000.6],
        }
    )
    postes = preparer_postes(bruts)
    assert list(postes["poste_id"]) == ["976993_6273893", "842000_6519001"]


def test_poste_le_plus_proche():
    postes = preparer_postes(pd.DataFrame({"X": [842000.0, 843000.0], "Y": [6519000.0] * 2}))
    adresses = pd.DataFrame(
        {"id": ["a1", "a2"], "x": [842003.0, 842990.0], "y": [6519004.0, 6519000.0]}
    )
    liens = rattacher(adresses, postes)
    assert list(liens["poste_id"]) == ["842000_6519000", "843000_6519000"]
    assert list(liens["distance_m"]) == pytest.approx([5.0, 10.0])  # 3-4-5 : Pythagore


def test_egalite_de_distance():
    # L'adresse est exactement à mi-chemin entre deux postes : on garde le plus petit identifiant
    postes = preparer_postes(pd.DataFrame({"X": [843000.0, 841000.0], "Y": [6519000.0] * 2}))
    adresses = pd.DataFrame({"id": ["a1"], "x": [842000.0], "y": [6519000.0]})
    liens = rattacher(adresses, postes)
    assert len(liens) == 1
    assert liens["poste_id"].iloc[0] == "841000_6519000"
