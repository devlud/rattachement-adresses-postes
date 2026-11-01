"""Rattachement au poste le plus proche avec Spark, et comparaison avec GeoPandas.

Spark n'a pas d'index spatial. On le remplace par une grille :
1. on découpe la France en cases carrées ;
2. chaque adresse n'est comparée qu'aux postes de sa case et des 8 cases voisines ;
3. si le meilleur de ces postes est à moins d'une case de distance, c'est forcément le plus
   proche de tous : un poste situé hors des 9 cases est à plus d'une case de l'adresse ;
4. les autres adresses recommencent avec des cases plus grandes.

Le résultat est exact : il doit être identique à celui de GeoPandas (étape 5).

Utilisation, depuis le dossier du projet, après le pipeline (étapes 6 et 7) :
    python -m rattachement.plus_proche_spark 69
    python -m rattachement.plus_proche_spark tous
"""

import sys
import time

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from rattachement.config import OUTPUT_DIR, RATTACHEMENT_DIR
from rattachement.pipeline import choisir_departements
from rattachement.plus_proche import lire_postes

# Tailles des cases, en mètres : petites d'abord, car la plupart des postes sont tout près ;
# puis de plus en plus grandes, pour les adresses isolées
TAILLES_M = [200, 500, 1_000, 2_000, 5_000, 10_000, 20_000, 50_000]


def demarrer_spark():
    """Démarre Spark sur l'ordinateur, en utilisant tous ses cœurs."""
    spark = (
        SparkSession.builder.master("local[*]")  # local : sur ce Mac ; [*] : tous les cœurs
        .appName("rattachement")
        .config("spark.driver.memory", "4g")  # 1 Go par défaut : trop peu pour toute la France
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")  # n'affiche que les erreurs, pas les avertissements
    return spark


def candidats(adresses, postes, taille):
    """Associe chaque adresse aux postes de sa case et des 8 cases voisines."""
    # Numéro de la case de chaque adresse : colonne cx, ligne cy
    adresses = adresses.withColumn("cx", F.floor(F.col("x") / taille)).withColumn(
        "cy", F.floor(F.col("y") / taille)
    )
    # Chaque poste est recopié 9 fois : dans sa case et dans les 8 cases qui l'entourent
    decalages = F.array(F.lit(-1), F.lit(0), F.lit(1))
    postes = (
        postes.withColumn("dx", F.explode(decalages))  # 3 copies : à gauche, sur place, à droite
        .withColumn("dy", F.explode(decalages))  # chacune en 3 : en dessous, sur place, au-dessus
        .select(
            "poste_id",
            F.col("x").alias("px"),
            F.col("y").alias("py"),
            (F.floor(F.col("x") / taille) + F.col("dx")).alias("cx"),
            (F.floor(F.col("y") / taille) + F.col("dy")).alias("cy"),
        )
    )
    # Une adresse et un poste sont candidats quand ils se retrouvent dans la même case
    return adresses.join(postes, on=["cx", "cy"])


def le_plus_proche(candidats):
    """Pour chaque adresse, le candidat le plus proche. À égalité : le plus petit poste_id."""
    dx = F.col("x") - F.col("px")
    dy = F.col("y") - F.col("py")
    return (
        candidats.withColumn("distance_m", F.sqrt(dx * dx + dy * dy))  # Pythagore
        .groupBy("id")
        # Minimum du couple (distance, poste_id) : Spark compare d'abord les distances, puis,
        # à égalité, les identifiants. C'est le même départage qu'à l'étape 5.
        .agg(F.min(F.struct("distance_m", "poste_id")).alias("meilleur"))
        .select("id", "meilleur.poste_id", "meilleur.distance_m")
    )


def rattacher_spark(adresses, postes):
    """Trouve le poste le plus proche de chaque adresse. Renvoie : id, poste_id, distance_m."""
    restantes = adresses.select("id", "x", "y")
    trouvees = []
    for taille in TAILLES_M:
        meilleurs = le_plus_proche(candidats(restantes, postes, taille))
        # Sûr : le meilleur candidat est à moins d'une case. Les postes hors des 9 cases sont
        # tous à plus d'une case : aucun ne peut faire mieux.
        surs = meilleurs.filter(F.col("distance_m") < taille).cache()  # gardé en mémoire
        trouvees.append(surs)
        # Les autres adresses recommencent, avec des cases plus grandes
        restantes = restantes.join(surs, on="id", how="left_anti").cache()
        nb_restantes = restantes.count()
        print(f"Cases de {taille} m : {surs.count()} adresses trouvées, {nb_restantes} restantes")
        if nb_restantes == 0:  # toutes les adresses ont leur poste : inutile de continuer
            break
    if nb_restantes > 0:
        print(f"Attention : {nb_restantes} adresses à plus de {taille} m de tout poste")

    # On met bout à bout les adresses trouvées avec chaque taille de case
    resultat = trouvees[0]
    for suite in trouvees[1:]:
        resultat = resultat.unionByName(suite)
    return resultat


def lire_adresses_spark(spark, departements):
    """Adresses desservies par Enedis, avec le poste trouvé par GeoPandas (étapes 5 à 7)."""
    fichiers = [str(RATTACHEMENT_DIR / f"adresses-{d}.parquet") for d in departements]
    return (
        spark.read.parquet(*fichiers)
        .filter("enedis")  # seules ces adresses ont un poste Enedis
        .select(
            "id",
            "x",
            "y",
            F.col("poste_id").alias("poste_geopandas"),
            F.col("distance_m").alias("distance_geopandas"),
        )
    )


def lire_postes_spark(spark):
    """Les postes, préparés exactement comme à l'étape 5, pour avoir les mêmes identifiants."""
    fichier = OUTPUT_DIR / "postes.parquet"
    lire_postes().to_parquet(fichier, index=False)  # pandas écrit le fichier, Spark le relit
    return spark.read.parquet(str(fichier))


def comparer(adresses, resultat):
    """Compte les adresses pour lesquelles Spark et GeoPandas trouvent le même poste."""
    comparaison = adresses.join(resultat, on="id", how="left")  # left : toutes les adresses
    bilan = comparaison.agg(
        F.count("*").alias("adresses"),
        F.count_if(F.col("poste_id") == F.col("poste_geopandas")).alias("meme_poste"),
        F.max(F.abs(F.col("distance_m") - F.col("distance_geopandas"))).alias("ecart_max_m"),
    ).first()
    print(f"Même poste qu'avec GeoPandas : {bilan['meme_poste']} adresses sur {bilan['adresses']}")
    print(f"Plus grand écart de distance : {bilan['ecart_max_m']} m")
    if bilan["meme_poste"] < bilan["adresses"]:  # on affiche quelques différences, pour comprendre
        comparaison.filter(~F.col("poste_id").eqNullSafe(F.col("poste_geopandas"))).show(10)


# Ce bloc ne s'exécute que lorsqu'on lance le fichier en ligne de commande.
if __name__ == "__main__":
    departements = choisir_departements(sys.argv[1:])  # comme le pipeline : 69 01 38, ou tous
    debut = time.perf_counter()
    spark = demarrer_spark()
    adresses = lire_adresses_spark(spark, departements)
    resultat = rattacher_spark(adresses, lire_postes_spark(spark))
    comparer(adresses, resultat)
    print(f"Durée totale : {time.perf_counter() - debut:.0f} s")
    spark.stop()
