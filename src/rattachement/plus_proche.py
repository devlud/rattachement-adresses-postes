"""Rattachement de chaque adresse au poste HTA/BT le plus proche.

Méthode : la jointure spatiale de GeoPandas (sjoin_nearest). Grâce à un index spatial,
chaque adresse n'est comparée qu'aux postes de son voisinage, et non à tous les postes.
On cherche parmi tous les postes de France : le plus proche peut être dans un département voisin.

Utilisation, depuis le dossier du projet :
    python -m rattachement.plus_proche 69
"""

import sys
import time

import geopandas as gpd
import pandas as pd

from rattachement.config import CRS_LAMBERT93, RAW_DIR
from rattachement.qualite import lire_adresses


def preparer_postes(postes):
    """Renomme les colonnes, fabrique un identifiant et retire les postes en double."""
    postes = postes.rename(columns={"X": "x", "Y": "y"})  # mêmes noms que pour les adresses
    # Le fichier ne contient pas d'identifiant : on le fabrique à partir de la position arrondie
    # au mètre. Contrairement au numéro de ligne, il ne change pas d'un téléchargement à l'autre.
    x_arrondi = postes["x"].round().astype(int).astype(str)
    y_arrondi = postes["y"].round().astype(int).astype(str)
    postes["poste_id"] = x_arrondi + "_" + y_arrondi  # par exemple « 976993_6273893 »
    # Deux postes au même endroit, au mètre près, ne comptent qu'une fois
    return postes.drop_duplicates("poste_id").reset_index(drop=True)


def lire_postes():
    """Lit les positions des postes HTA/BT de toute la France, puis les prépare."""
    postes = pd.read_csv(RAW_DIR / "postes-hta-bt.csv", usecols=["X", "Y"])
    return preparer_postes(postes)


def en_points(tableau, colonnes):
    """Transforme un tableau qui a des colonnes x et y en points géographiques."""
    return gpd.GeoDataFrame(
        tableau[colonnes],
        geometry=gpd.points_from_xy(tableau["x"], tableau["y"]),  # un point par ligne
        crs=CRS_LAMBERT93,  # coordonnées en mètres
    )


def rattacher(adresses, postes):
    """Trouve le poste le plus proche de chaque adresse. Renvoie : id, poste_id, distance_m."""
    resultat = gpd.sjoin_nearest(
        en_points(adresses, ["id"]),
        en_points(postes, ["poste_id"]),
        distance_col="distance_m",  # nom de la colonne qui recevra la distance, en mètres
    )
    # À égalité de distance, sjoin_nearest renvoie une ligne par poste : on garde celle
    # du plus petit identifiant, pour obtenir toujours le même résultat.
    resultat = resultat.sort_values(["id", "distance_m", "poste_id"]).drop_duplicates("id")
    return pd.DataFrame(resultat[["id", "poste_id", "distance_m"]]).reset_index(drop=True)


# Ce bloc ne s'exécute que lorsqu'on lance le fichier en ligne de commande.
if __name__ == "__main__":
    debut = time.perf_counter()
    adresses, _ = lire_adresses(sys.argv[1])  # le numéro écrit après la commande, ex. 69
    postes = lire_postes()
    liens = rattacher(adresses, postes)
    duree = time.perf_counter() - debut
    print(f"{len(liens)} adresses rattachées à un poste en {duree:.1f} s")
    print(liens["distance_m"].describe().round(1))
