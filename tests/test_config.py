from rattachement.config import DEPARTEMENTS


def test_departements():
    assert len(DEPARTEMENTS) == 94  # 95 numéros, moins le 20 (Corse)
    assert DEPARTEMENTS[0] == "01"  # sur deux caractères, comme dans les fichiers de la BAN
    assert DEPARTEMENTS[-1] == "95"
    assert "20" not in DEPARTEMENTS
