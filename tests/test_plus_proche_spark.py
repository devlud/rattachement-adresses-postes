import numpy as np
import pandas as pd
import pytest

from rattachement.plus_proche import rattacher

# Le module Spark du projet. Si PySpark n'est pas installé, son import échoue :
# les tests de ce fichier sont alors sautés, au lieu d'échouer.
plus_proche_spark = pytest.importorskip("rattachement.plus_proche_spark")
rattacher_spark = plus_proche_spark.rattacher_spark


@pytest.fixture(scope="module")
def spark():
    """Une seule session Spark pour tous les tests du fichier : la démarrer prend du temps."""
    session = plus_proche_spark.demarrer_spark()
    yield session
    session.stop()


def en_spark(spark, tableau):
    """Transforme un tableau pandas en tableau Spark, en passant par une liste de lignes."""
    return spark.createDataFrame(list(tableau.itertuples(index=False)), list(tableau.columns))


def en_dictionnaire(resultat):
    """Transforme le résultat Spark en dictionnaire : {adresse: (poste_id, distance_m)}."""
    return {ligne["id"]: (ligne["poste_id"], ligne["distance_m"]) for ligne in resultat.collect()}


def test_meme_resultat_que_geopandas(spark):
    # 500 adresses et 100 postes placés au hasard sur un carré de 20 km de côté
    hasard = np.random.default_rng(0)
    adresses = pd.DataFrame(
        {
            "id": [f"a{i}" for i in range(500)],
            "x": hasard.uniform(840_000, 860_000, 500),
            "y": hasard.uniform(6_510_000, 6_530_000, 500),
        }
    )
    postes = pd.DataFrame(
        {
            "poste_id": [f"p{i}" for i in range(100)],
            "x": hasard.uniform(840_000, 860_000, 100),
            "y": hasard.uniform(6_510_000, 6_530_000, 100),
        }
    )
    attendu = rattacher(adresses, postes)  # GeoPandas, étape 5
    obtenu = en_dictionnaire(rattacher_spark(en_spark(spark, adresses), en_spark(spark, postes)))
    assert len(obtenu) == 500  # chaque adresse a trouvé un poste
    for ligne in attendu.itertuples():
        poste_id, distance_m = obtenu[ligne.id]
        assert poste_id == ligne.poste_id
        assert distance_m == pytest.approx(ligne.distance_m)


def test_adresse_isolee(spark):
    # Le seul poste est à 30 km : on ne le trouve qu'avec les plus grandes cases
    postes = spark.createDataFrame([("p1", 842_000.0, 6_519_000.0)], ["poste_id", "x", "y"])
    adresses = spark.createDataFrame([("a1", 872_000.0, 6_519_000.0)], ["id", "x", "y"])
    assert en_dictionnaire(rattacher_spark(adresses, postes)) == {"a1": ("p1", 30_000.0)}


def test_egalite_de_distance(spark):
    # L'adresse est exactement à mi-chemin de deux postes : on garde le plus petit identifiant
    postes = spark.createDataFrame(
        [("p2", 843_000.0, 6_519_000.0), ("p1", 841_000.0, 6_519_000.0)], ["poste_id", "x", "y"]
    )
    adresses = spark.createDataFrame([("a1", 842_000.0, 6_519_000.0)], ["id", "x", "y"])
    assert en_dictionnaire(rattacher_spark(adresses, postes)) == {"a1": ("p1", 1_000.0)}
