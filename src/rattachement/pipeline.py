"""Pipeline complet : des fichiers bruts aux adresses rattachées, département par département.

Pour chaque département :
1. télécharge le fichier de la BAN, s'il n'est pas déjà là (étape 2) ;
2. contrôle la qualité des adresses (étape 3) ;
3. ajoute le libellé normalisé (étape 4) et le poste le plus proche (étape 5) ;
4. enregistre le résultat au format Parquet, dans data/output/rattachement/.

À la fin, un bilan (une ligne par département) est affiché et enregistré dans data/output/.

Utilisation, depuis le dossier du projet :
    python -m rattachement.pipeline 69 01 38
    python -m rattachement.pipeline tous
"""

import sys
import time

import pandas as pd

from rattachement.config import (
    DEPARTEMENTS,
    OUTPUT_DIR,
    RATTACHEMENT_DIR,
    RAW_DIR,
    SEUIL_DISTANCE_M,
)
from rattachement.plus_proche import lire_postes, rattacher
from rattachement.qualite import lire_adresses
from rattachement.telechargement import telecharger_ban, telecharger_postes
from rattachement.texte import libelles_ban


def choisir_departements(arguments):
    """Liste des départements à traiter, d'après ce qui est écrit après la commande.

    On vérifie tout avant de commencer : sans cela, une faute de frappe (« 1 » au lieu de « 01 »)
    ne serait découverte qu'au téléchargement, après cinq essais et cinq minutes d'attente.
    """
    if not arguments:  # rien d'écrit après la commande
        raise ValueError("Indique au moins un département, par exemple : 69, ou tous")
    if arguments == ["tous"]:
        return DEPARTEMENTS
    for departement in arguments:
        if departement not in DEPARTEMENTS:
            raise ValueError(f"Département inconnu : {departement} (attendu : de 01 à 95, ou tous)")
    return arguments


def enrichir(adresses, postes):
    """Ajoute à chaque adresse son libellé normalisé, son poste le plus proche et la distance."""
    adresses = adresses.assign(libelle=libelles_ban(adresses))  # étape 4
    liens = rattacher(adresses, postes)  # étape 5 : un tableau id, poste_id, distance_m
    # On recolle chaque poste à son adresse, grâce à l'identifiant de l'adresse.
    # validate="one_to_one" : erreur si un identifiant apparaît deux fois d'un côté ou de l'autre,
    # ce qui recopierait une adresse en double.
    resultat = adresses.merge(liens, on="id", validate="one_to_one")
    resultat["hors_seuil"] = resultat["distance_m"] > SEUIL_DISTANCE_M  # rattachement suspect
    return resultat


def traiter_departement(departement, postes):
    """Traite un département de bout en bout. Renvoie sa ligne du bilan."""
    # Le fichier de la BAN n'est téléchargé que s'il n'est pas déjà sur le disque
    if not (RAW_DIR / f"adresses-{departement}.csv.gz").exists():
        telecharger_ban(departement)

    debut = time.perf_counter()  # le chronomètre ne compte pas le téléchargement
    adresses, mises_de_cote = lire_adresses(departement)  # étape 3
    resultat = enrichir(adresses, postes)
    resultat.to_parquet(RATTACHEMENT_DIR / f"adresses-{departement}.parquet", index=False)
    if len(mises_de_cote) > 0:  # gardées dans un fichier, pour pouvoir les examiner
        mises_de_cote.to_csv(OUTPUT_DIR / f"mises-de-cote-{departement}.csv", index=False)

    return {
        "departement": departement,
        "adresses": len(resultat),
        "mises_de_cote": len(mises_de_cote),
        "distance_mediane_m": round(resultat["distance_m"].median(), 1),
        "distance_max_m": round(resultat["distance_m"].max(), 1),
        "hors_seuil": int(resultat["hors_seuil"].sum()),  # True compte pour 1, False pour 0
        "duree_s": round(time.perf_counter() - debut, 1),
    }


def executer(departements):
    """Traite les départements un par un, puis affiche et enregistre le bilan."""
    debut = time.perf_counter()
    RATTACHEMENT_DIR.mkdir(parents=True, exist_ok=True)  # crée data/output/rattachement/
    if not (RAW_DIR / "postes-hta-bt.csv").exists():
        telecharger_postes()
    postes = lire_postes()  # lus une seule fois, puis réutilisés pour chaque département

    lignes = []
    for departement in departements:
        print(f"--- Département {departement}")
        lignes.append(traiter_departement(departement, postes))

    bilan = pd.DataFrame(lignes)  # une ligne par département
    bilan.to_csv(OUTPUT_DIR / "bilan.csv", index=False)
    print(bilan.to_string(index=False))
    duree = time.perf_counter() - debut
    print(f"Total : {bilan['adresses'].sum()} adresses rattachées en {duree:.0f} s")


# Ce bloc ne s'exécute que lorsqu'on lance le fichier en ligne de commande.
if __name__ == "__main__":
    executer(choisir_departements(sys.argv[1:]))  # par exemple ["69", "01", "38"], ou ["tous"]
