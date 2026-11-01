"""Normalisation du texte des adresses.

But : écrire de la même façon deux libellés qui désignent la même adresse,
pour qu'un ordinateur puisse les comparer.

Exemple : « 12 bis av. Jean-Jaurès » devient « 12 BIS AVENUE JEAN JAURES ».
"""

import re
import unicodedata

# Abréviations courantes des types de voie et des titres, avec leur forme complète
ABREVIATIONS = {
    "AV": "AVENUE",
    "AVE": "AVENUE",
    "BD": "BOULEVARD",
    "BLD": "BOULEVARD",
    "CHE": "CHEMIN",
    "CHEM": "CHEMIN",
    "IMP": "IMPASSE",
    "PL": "PLACE",
    "RTE": "ROUTE",
    "RD": "ROUTE DEPARTEMENTALE",
    "RN": "ROUTE NATIONALE",
    "ALL": "ALLEE",
    "SQ": "SQUARE",
    "CRS": "COURS",
    "FG": "FAUBOURG",
    "FBG": "FAUBOURG",
    "ST": "SAINT",
    "STE": "SAINTE",
    "DR": "DOCTEUR",
    "GAL": "GENERAL",
    "MAL": "MARECHAL",
    "PDT": "PRESIDENT",
}


def sans_accents(texte):
    """Retire les accents : « È » devient « E »."""
    decompose = unicodedata.normalize("NFD", texte)  # sépare chaque lettre de son accent
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")  # garde les lettres


def normaliser(texte):
    """Écrit un libellé d'adresse sous une forme standard, pour pouvoir le comparer."""
    if not isinstance(texte, str):  # case vide (NaN) : on renvoie un texte vide
        return ""
    texte = sans_accents(texte.upper())
    texte = texte.replace("Œ", "OE").replace("Æ", "AE")  # ligatures, sans accent à retirer
    texte = re.sub(r"[^A-Z0-9]", " ", texte)  # ponctuation : tout sauf lettres et chiffres
    texte = re.sub(r"(\d)([A-Z])", r"\1 \2", texte)  # chiffre collé à une lettre : 12BIS
    texte = re.sub(r"([A-Z])(\d)", r"\1 \2", texte)  # lettre collée à un chiffre : RD386
    mots = texte.split()  # découpe en mots ; les espaces en trop disparaissent
    return " ".join(ABREVIATIONS.get(mot, mot) for mot in mots)


def libelles_ban(adresses):
    """Libellé normalisé de chaque adresse de la BAN : numéro, indice de répétition, voie."""
    libelles = (
        adresses["numero"].astype(str)
        + " "
        + adresses["rep"].fillna("")  # la plupart des adresses n'ont pas de bis ou de ter
        + " "
        + adresses["nom_voie"]
    )
    return libelles.map(normaliser)  # applique normaliser à chaque libellé
