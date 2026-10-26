"""Réglages du projet, regroupés en un seul endroit."""

from pathlib import Path

# Dossiers des données (exclus de Git par le .gitignore)
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"  # fichiers téléchargés, tels quels
OUTPUT_DIR = DATA_DIR / "output"  # résultats du projet

# Systèmes de coordonnées
CRS_WGS84 = "EPSG:4326"  # longitude / latitude en degrés, comme un GPS
CRS_LAMBERT93 = "EPSG:2154"  # x / y en mètres, projection officielle en France

# Départements de France continentale, desservis par Enedis : "01" à "95", sans la Corse
DEPARTEMENTS = [f"{i:02d}" for i in range(1, 96) if i != 20]

# Distance au-delà de laquelle un rattachement est jugé suspect (à calibrer à l'étape 8)
SEUIL_DISTANCE_M = 2000
