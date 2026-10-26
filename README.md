# Rattachement des adresses aux postes électriques

Pour chacune des 25 millions d'adresses de la Base Adresse Nationale (BAN), trouver le poste de
distribution HTA/BT d'Enedis le plus proche, à partir de données ouvertes.

Projet en construction, un commit par étape.

## Installation

```bash
git clone https://github.com/devlud/rattachement-adresses-postes.git
cd rattachement-adresses-postes
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Licence

Code sous licence MIT. Données de la BAN et d'Enedis sous Licence Ouverte 2.0.
