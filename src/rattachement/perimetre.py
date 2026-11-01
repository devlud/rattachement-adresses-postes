"""Périmètre d'Enedis : quel distributeur gère le réseau électrique de chaque commune ?

Enedis gère le réseau de distribution sur environ 95 % du territoire. Le reste est géré par des
entreprises locales de distribution (ELD) : Strasbourg Électricité Réseaux dans le Bas-Rhin,
Gérédis dans les Deux-Sèvres, SRD dans la Vienne... Leurs postes ne sont pas dans les données
d'Enedis : on ne rattache donc à un poste Enedis que les adresses desservies par Enedis.

Source : la liste des distributeurs de chaque commune, publiée par l'Agence ORE (data.gouv.fr).
Limite connue : la liste est par commune. Si une commune a deux distributeurs, on ne sait pas
lequel dessert chaque adresse : ces communes sont signalées par la colonne commune_mixte.
"""

import pandas as pd

from rattachement.config import RAW_DIR

CODE_ENEDIS = "ENED"  # le code court d'Enedis dans la liste de l'Agence ORE


def preparer_distributeurs(liste):
    """Garde, pour chaque commune : code INSEE, distributeur, Enedis ou non, mixte ou non."""
    # Une commune peut avoir deux distributeurs d'électricité (code_grd_elec_1 et code_grd_elec_2) :
    # elle compte comme desservie par Enedis si Enedis est l'un des deux.
    enedis = (liste["code_grd_elec_1"] == CODE_ENEDIS) | (liste["code_grd_elec_2"] == CODE_ENEDIS)
    return pd.DataFrame(
        {
            "code_insee": liste["code_insee_commune"],  # même nom de colonne que dans la BAN
            "distributeur": liste["GRD_ELEC"],
            "enedis": enedis,
            # Commune mixte : deux distributeurs, donc un rattachement moins sûr (étape 9)
            "commune_mixte": liste["code_grd_elec_2"].notna(),
        }
    )


def lire_distributeurs():
    """Lit la liste des distributeurs de chaque commune, puis la prépare."""
    liste = pd.read_csv(
        RAW_DIR / "distributeurs-par-commune.csv",
        sep=";",
        usecols=["code_insee_commune", "GRD_ELEC", "code_grd_elec_1", "code_grd_elec_2"],
        dtype=str,  # que du texte : « 01001 » garde son zéro
    )
    return preparer_distributeurs(liste)


def ajouter_distributeur(adresses, distributeurs):
    """Ajoute à chaque adresse le distributeur de sa commune, et s'il s'agit d'Enedis."""
    # how="left" : on garde toutes les adresses, même si leur commune n'est pas dans la liste.
    # validate="many_to_one" : plusieurs adresses par commune, mais une seule ligne par commune
    # dans la liste. Une commune en double dans la liste provoquerait une erreur.
    adresses = adresses.merge(distributeurs, on="code_insee", how="left", validate="many_to_one")
    # Commune absente de la liste : les cases restent vides, et .eq(True) les transforme en False
    adresses["enedis"] = adresses["enedis"].eq(True)
    adresses["commune_mixte"] = adresses["commune_mixte"].eq(True)
    return adresses
