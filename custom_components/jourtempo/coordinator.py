"""Lecture de l'API Jour Tempo (tempo.json et ejp.json)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN, REQUEST_TIMEOUT, SCAN_INTERVAL, URL_EJP, URL_TEMPO, USER_AGENT

_LOGGER = logging.getLogger(__name__)

type JourTempoConfigEntry = ConfigEntry[JourTempoCoordinator]


class JourTempoErreur(Exception):
    """L'API n'a pas répondu correctement."""


@dataclass
class JourTempoDonnees:
    """Dernières réponses valides des deux fichiers."""

    tempo: dict[str, Any] | None = None
    ejp: dict[str, Any] | None = None


async def lire_json(session: aiohttp.ClientSession, url: str) -> dict[str, Any]:
    """Télécharge un fichier JSON de l'API."""
    try:
        async with asyncio.timeout(REQUEST_TIMEOUT):
            reponse = await session.get(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            reponse.raise_for_status()
            donnees = await reponse.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError, ValueError) as err:
        raise JourTempoErreur(f"{url} : {err}") from err
    if not isinstance(donnees, dict) or donnees.get("api") != "v1":
        raise JourTempoErreur(f"{url} : réponse inattendue")
    return donnees


def est_perime(fichier: dict[str, Any] | None) -> bool:
    """Vrai si le fichier manque ou si sa date `perime_apres` est dépassée."""
    if not fichier:
        return True
    limite = fichier.get("perime_apres")
    if not limite:
        return True
    try:
        quand = datetime.fromisoformat(limite)
    except ValueError:
        return True
    if quand.tzinfo is None:
        quand = quand.replace(tzinfo=dt_util.get_default_time_zone())
    return dt_util.now() > quand


class JourTempoCoordinator(DataUpdateCoordinator[JourTempoDonnees]):
    """Interroge l'API toutes les 15 minutes."""

    config_entry: JourTempoConfigEntry

    def __init__(self, hass: HomeAssistant, entry: JourTempoConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> JourTempoDonnees:
        precedent = self.data or JourTempoDonnees()
        tempo, ejp = await asyncio.gather(
            lire_json(self._session, URL_TEMPO),
            lire_json(self._session, URL_EJP),
            return_exceptions=True,
        )
        erreurs = [r for r in (tempo, ejp) if isinstance(r, Exception)]
        for err in erreurs:
            _LOGGER.debug("Jour Tempo : %s", err)
        if len(erreurs) == 2 and precedent.tempo is None and precedent.ejp is None:
            raise UpdateFailed(f"API Jour Tempo injoignable : {erreurs[0]}")
        # Un fichier en erreur garde sa dernière valeur ; `perime_apres` passe
        # ensuite les capteurs à « inconnu » si la panne dure.
        return JourTempoDonnees(
            tempo=precedent.tempo if isinstance(tempo, Exception) else tempo,
            ejp=precedent.ejp if isinstance(ejp, Exception) else ejp,
        )
