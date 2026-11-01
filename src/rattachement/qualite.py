"""Lecture et contrôle de qualité des adresses de la BAN.

Chaque règle vient d'une observation faite pendant l'exploration (notebook du brouillon) :
- certains identifiants apparaissent plusieurs fois : on garde la première ligne de chacun ;
- les colonnes utiles au projet ne doivent jamais être vides ;
- le code INSEE compte 5 chiffres ;
- les coordonnées doivent tomber en France métropolitaine.

Une adresse qui ne respecte pas une règle est mise de côté, jamais supprimée en silence.

Utilisation, depuis le dossier du projet :
    python -m rattachement.qualite 69
"""

import sys

import pandas as pd
import pandera.pandas as pa

from rattachement.config import RAW_DIR

# Les colonnes utiles au projet (la BAN en compte 23)
COLONNES = [
    "id",
    "numero",
    "rep",
    "nom_voie",
    "code_insee",
    "nom_commune",
    "type_position",
    "x",
    "y",
    "lon",
    "lat",
]

# Les règles de qualité, colonne par colonne.
# Par défaut, pandera refuse les cases vides : chaque colonne listée ici doit être remplie.
REGLES_ADRESSES = pa.DataFrameSchema(
    {
        "id": pa.Column(str, unique=True),  # un identifiant par adresse
        "code_insee": pa.Column(str, pa.Check.str_matches(r"^\d{5}$")),  # exactement 5 chiffres
        "x": pa.Column(float, pa.Check.in_range(0, 1_300_000)),  # en mètres (Lambert-93)
        "y": pa.Column(float, pa.Check.in_range(6_000_000, 7_200_000)),
        "lon": pa.Column(float, pa.Check.in_range(-5.5, 10)),  # en degrés
        "lat": pa.Column(float, pa.Check.in_range(41, 51.5)),
    },
    drop_invalid_rows=True,  # retire les lignes en faute au lieu de tout arrêter
)


def controler_adresses(adresses):
    """Applique les règles de qualité. Renvoie les adresses valides et celles mises de côté."""
    # 1. Doublons d'identifiant : même adresse saisie deux fois, on garde la première ligne
    sans_doublons = adresses.drop_duplicates("id")
    nb_doublons = len(adresses) - len(sans_doublons)

    # 2. Règles de qualité : pandera renvoie le tableau sans les lignes en faute.
    #    lazy=True : il examine toutes les lignes au lieu de s'arrêter à la première erreur.
    valides = REGLES_ADRESSES.validate(sans_doublons, lazy=True)

    # 3. Les adresses mises de côté sont celles qui ont disparu à l'étape 2
    mises_de_cote = sans_doublons[~sans_doublons.index.isin(valides.index)]

    print(
        f"{nb_doublons} doublons retirés, {len(mises_de_cote)} adresses mises de côté, "
        f"{len(valides)} adresses valides"
    )
    return valides, mises_de_cote


def lire_adresses(departement):
    """Lit les adresses d'un département, puis les contrôle."""
    adresses = pd.read_csv(
        RAW_DIR / f"adresses-{departement}.csv.gz",
        sep=";",  # la BAN sépare ses colonnes par des points-virgules
        usecols=COLONNES,  # on ne charge que les colonnes utiles
        dtype={"id": str, "code_insee": str},  # des codes, pas des nombres
        low_memory=False,  # lit le fichier d'un seul bloc : types de colonnes plus fiables
    )
    return controler_adresses(adresses)


# Ce bloc ne s'exécute que lorsqu'on lance le fichier en ligne de commande.
if __name__ == "__main__":
    lire_adresses(sys.argv[1])  # le numéro écrit après la commande, ex. 69
