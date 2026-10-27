from rattachement.telechargement import URL_BAN, retirer_premiere_ligne


def test_retirer_premiere_ligne():
    page = "X,Y\n1,2\n3,4\n"
    assert retirer_premiere_ligne(page) == "1,2\n3,4\n"


def test_adresse_ban_d_un_departement():
    url = URL_BAN.format(departement="69")
    assert url.endswith("/adresses-69.csv.gz")