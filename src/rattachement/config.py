"""Réglages du projet, regroupés en un seul endroit."""

from pathlib import Path

# Dossier racine du projet, calculé à partir de l'emplacement de ce fichier :
# config.py est dans src/rattachement/, on remonte donc de deux dossiers.
# Ainsi, les chemins restent justes même depuis un notebook rangé dans brouillon/.
RACINE = Path(__file__).resolve().parents[2]

# Dossiers des données (exclus de Git par le .gitignore)
DATA_DIR = RACINE / "data"
RAW_DIR = DATA_DIR / "raw"  # fichiers téléchargés, tels quels
OUTPUT_DIR = DATA_DIR / "output"  # résultats du projet
RATTACHEMENT_DIR = OUTPUT_DIR / "rattachement"  # adresses rattachées : un fichier par département

# Systèmes de coordonnées
CRS_WGS84 = "EPSG:4326"  # longitude / latitude en degrés, comme un GPS
CRS_LAMBERT93 = "EPSG:2154"  # x / y en mètres, projection officielle en France

# Départements de France continentale : "01" à "95", sans la Corse (où Enedis n'est pas présent).
# Même là, Enedis ne dessert pas toutes les communes : voir perimetre.py.
DEPARTEMENTS = [f"{i:02d}" for i in range(1, 96) if i != 20]

# Distance au-delà de laquelle un rattachement est jugé suspect (à calibrer à l'étape 9)
SEUIL_DISTANCE_M = 2000
