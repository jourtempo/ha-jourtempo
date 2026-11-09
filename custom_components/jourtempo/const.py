"""Constantes de l'intégration Jour Tempo."""

from datetime import timedelta

DOMAIN = "jourtempo"
NAME = "Jour Tempo"

URL_TEMPO = "https://jourtempo.fr/api/v1/tempo.json"
URL_EJP = "https://jourtempo.fr/api/v1/ejp.json"
URL_DOC = "https://jourtempo.fr/api/"

# Sans ce User-Agent explicite, Cloudflare refuse les clients HTTP génériques.
USER_AGENT = "ha-jourtempo/1.0"

SCAN_INTERVAL = timedelta(minutes=15)
REQUEST_TIMEOUT = 20

ATTRIBUTION = "Couleurs Tempo : RTE. Jours EJP : EDF. Diffusé par Jour Tempo (jourtempo.fr)"

COULEURS = ["bleu", "blanc", "rouge"]
# Valeurs de l'API EJP, avec des tirets remplacés par des soulignés pour les traductions.
EJP_ETATS = ["ejp", "normal", "non_verifie", "hors_saison"]
