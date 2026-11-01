import pandas as pd

from rattachement.statistiques import compter_au_dela, tracer_carte, tracer_distances


def test_compter_au_dela():
    distances = pd.Series([100.0, 600.0, 1_200.0, 5_000.0])
    assert compter_au_dela(distances, [500, 1_000]).to_dict() == {500: 3, 1_000: 2}


def test_images(tmp_path):  # tmp_path : un dossier temporaire, fourni par pytest
    adresses = pd.DataFrame(
        {
            "x": [842_000.0, 850_000.0, 1_050_000.0],
            "y": [6_519_000.0, 6_520_000.0, 6_841_000.0],
            "enedis": [True, True, False],
            "hors_seuil": [False, True, False],
            "distance_m": [100.0, 1_500.0, None],  # pas de distance : autre distributeur
        }
    )
    tracer_distances(adresses["distance_m"].dropna(), tmp_path / "distances.png")
    tracer_carte(adresses, tmp_path / "carte.png")
    assert (tmp_path / "distances.png").exists()
    assert (tmp_path / "carte.png").exists()
