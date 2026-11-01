"""Statistiques et images sur les résultats du pipeline, pour toute la France.

Affiche les chiffres clés, et enregistre deux images dans le dossier docs/ (pour le README) :
- distances.png : la répartition des distances entre adresse et poste, avec le seuil ;
- carte.png : les adresses desservies par Enedis, par un autre distributeur, et les suspectes.

Utilisation, depuis le dossier du projet, après le pipeline (python -m rattachement.pipeline tous) :
    python -m rattachement.statistiques
"""

import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from rattachement.config import RACINE, RATTACHEMENT_DIR, SEUIL_DISTANCE_M

# Les images du README : contrairement à data/, ce dossier est versionné avec Git
DOCS_DIR = RACINE / "docs"

# Les seuils comparés à l'étape 9, pour montrer ce que chacun aurait signalé
SEUILS_M = [500, 1_000, 1_500, 2_000, 3_000, 5_000]

# Couleurs des images : gris (Enedis), violet (autre distributeur), corail (suspect)
GRIS, VIOLET, CORAIL = "#888780", "#7F77DD", "#D85A30"


def lire_resultats(colonnes):
    """Lit quelques colonnes des résultats de tous les départements (fichiers Parquet)."""
    return pd.read_parquet(RATTACHEMENT_DIR, columns=colonnes)


def compter_au_dela(distances, seuils):
    """Nombre d'adresses au-delà de chaque seuil."""
    comptes = {seuil: int((distances > seuil).sum()) for seuil in seuils}
    return pd.Series(comptes, name="adresses_au_dela")


def tracer_distances(distances, fichier):
    """Histogramme des distances, sur deux axes logarithmiques, avec le seuil."""
    figure = Figure(figsize=(8, 4.5))  # une image indépendante, sans fenêtre à l'écran
    axe = figure.subplots()
    # Des intervalles de plus en plus larges, de 10 cm à la plus grande distance : sur un axe
    # logarithmique, ils ont tous la même largeur à l'écran
    bornes = np.logspace(-1, np.log10(distances.max()), 80)
    axe.hist(distances, bins=bornes, color=GRIS)
    axe.set_xscale("log")
    axe.set_yscale("log")  # sinon, les rares adresses lointaines seraient invisibles
    axe.axvline(
        SEUIL_DISTANCE_M, color=CORAIL, linestyle="--", label=f"Seuil : {SEUIL_DISTANCE_M} m"
    )
    axe.set_xlabel("Distance entre l'adresse et le poste Enedis le plus proche (m)")
    axe.set_ylabel("Nombre d'adresses")
    axe.legend()
    figure.savefig(fichier, dpi=150, bbox_inches="tight")


def tracer_carte(adresses, fichier):
    """Carte des adresses : Enedis, autre distributeur, rattachement suspect."""
    figure = Figure(figsize=(8, 8))
    axe = figure.subplots()
    groupes = [  # (adresses du groupe, couleur, taille des points, légende)
        (adresses[adresses["enedis"]], GRIS, 0.01, "Desservie par Enedis"),
        (adresses[~adresses["enedis"]], VIOLET, 0.01, "Autre distributeur"),
        (adresses[adresses["hors_seuil"]], CORAIL, 0.5, f"Poste à plus de {SEUIL_DISTANCE_M} m"),
    ]
    for groupe, couleur, taille, legende in groupes:  # les suspectes en dernier, par-dessus
        axe.scatter(groupe["x"], groupe["y"], s=taille, color=couleur, label=legende, linewidths=0)
    axe.set_aspect("equal")  # même échelle en x et en y : la France n'est pas déformée
    axe.set_axis_off()  # pas d'axes gradués sur une carte
    legende = axe.legend(loc="lower left")
    for symbole in legende.legend_handles:  # des points de légende assez gros pour être vus
        symbole.set_sizes([30])
    figure.savefig(fichier, dpi=150, bbox_inches="tight")


# Ce bloc ne s'exécute que lorsqu'on lance le fichier en ligne de commande.
if __name__ == "__main__":
    colonnes = ["x", "y", "enedis", "commune_mixte", "distance_m", "hors_seuil"]
    resultats = lire_resultats(colonnes)
    enedis = resultats[resultats["enedis"]]  # les adresses rattachées à un poste Enedis
    suspectes = enedis[enedis["hors_seuil"]]

    print(f"{len(resultats)} adresses, dont {len(enedis)} desservies par Enedis")
    print(enedis["distance_m"].quantile([0.5, 0.9, 0.99, 0.999, 0.9999]).round(0))
    print(compter_au_dela(enedis["distance_m"], SEUILS_M))
    part_mixte = suspectes["commune_mixte"].mean()  # moyenne de vrai/faux : une proportion
    print(
        f"{len(suspectes)} rattachements à plus de {SEUIL_DISTANCE_M} m, "
        f"dont {part_mixte:.0%} dans une commune à deux distributeurs"
    )

    DOCS_DIR.mkdir(exist_ok=True)
    tracer_distances(enedis["distance_m"], DOCS_DIR / "distances.png")
    # Pour la carte, 2 millions d'adresses suffisent à dessiner la France, et le dessin va
    # dix fois plus vite. On garde toutes les suspectes, qui sont peu nombreuses.
    # min(...) : si l'on n'a traité que quelques départements, il peut y en avoir moins.
    taille = min(2_000_000, len(resultats))
    echantillon = pd.concat([resultats.sample(taille, random_state=0), suspectes])
    tracer_carte(echantillon, DOCS_DIR / "carte.png")
    print(f"Images enregistrées dans {DOCS_DIR}")
