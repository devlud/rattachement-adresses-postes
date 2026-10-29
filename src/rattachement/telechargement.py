"""Téléchargement des données du projet.

Deux sources :
1. la Base Adresse Nationale (BAN) : un fichier par département ;
2. les postes électriques HTA/BT d'Enedis : servis par une API, page par page.

Utilisation, depuis le dossier du projet :
    python -m rattachement.telechargement 69
"""

import sys
import time
from datetime import datetime

import requests

from rattachement.config import RAW_DIR

# Adresse du fichier de la BAN d'un département : {departement} sera remplacé par "69", "75"...
URL_BAN = "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-{departement}.csv.gz"

# Adresse de l'API des postes : 10 000 lignes par page (le maximum autorisé), au format CSV
URL_POSTES = (
    "https://opendata.enedis.fr/data-fair/api/v1/datasets/poste-electrique/lines"
    "?size=10000&format=csv"
)


def telecharger_url(url, essais=5):
    """Télécharge une adresse. En cas d'échec (coupure, serveur saturé), attend puis réessaie."""
    for essai in range(1, essais + 1):
        try:
            reponse = requests.get(url, timeout=120)
            reponse.raise_for_status()  # une réponse d'erreur du serveur compte comme un échec
            return reponse  # réussi : on renvoie la réponse
        except requests.RequestException as erreur:
            if essai == essais:
                raise  # dernier essai raté : on abandonne et on affiche l'erreur
            attente = 30 * essai  # 30 s, puis 60 s, 90 s... pour laisser le serveur souffler
            print(f"Échec ({type(erreur).__name__}), nouvel essai dans {attente} s")
            time.sleep(attente)


def noter_dans_le_journal(fichier, url):
    """Ajoute une ligne au journal des téléchargements : quand, quel fichier, d'où."""
    date = datetime.now().astimezone().isoformat(timespec="seconds")
    with open(RAW_DIR / "journal.csv", "a", encoding="utf-8") as journal:
        journal.write(f"{date},{fichier},{url}\n")


def telecharger_ban(departement):
    """Télécharge les adresses d'un département : un seul fichier, compressé."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)  # crée data/raw s'il n'existe pas encore
    url = URL_BAN.format(departement=departement)
    reponse = telecharger_url(url)

    fichier = RAW_DIR / f"adresses-{departement}.csv.gz"
    fichier.write_bytes(reponse.content)  # on garde le fichier tel quel, compressé
    noter_dans_le_journal(fichier.name, url)
    print(f"Adresses du {departement} : {fichier}")


def retirer_premiere_ligne(texte):
    """Retire la première ligne d'un texte : ici, les noms de colonnes."""
    return texte.split("\n", 1)[1]


def telecharger_postes():
    """Télécharge les postes HTA/BT, page par page."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    pages = []
    url = URL_POSTES
    while url:  # tant qu'il reste une page à télécharger
        reponse = telecharger_url(url)
        texte = reponse.content.decode("utf-8")
        if pages:  # chaque page répète les noms de colonnes : on ne les garde qu'une fois
            texte = retirer_premiere_ligne(texte)
        pages.append(texte)
        print(f"Postes : page {len(pages)} téléchargée")
        # Le serveur donne l'adresse de la page suivante dans l'en-tête « Link » de sa réponse.
        # Après la dernière page, il n'y en a plus : url vaut None et la boucle s'arrête.
        url = reponse.links.get("next", {}).get("url")

    # On écrit le fichier seulement à la fin : une coupure en route ne laisse pas de fichier tronqué.
    fichier = RAW_DIR / "postes-hta-bt.csv"
    fichier.write_text("".join(pages), encoding="utf-8")
    noter_dans_le_journal(fichier.name, URL_POSTES)
    print(f"Postes : {fichier}")


# Ce bloc ne s'exécute que lorsqu'on lance le fichier en ligne de commande.
if __name__ == "__main__":
    for departement in sys.argv[1:]:  # les numéros écrits après la commande, ex. 69 75
        telecharger_ban(departement)
    telecharger_postes()
