"""Configuration par l'interface : un clic, sans clé ni compte."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, NAME, URL_TEMPO
from .coordinator import JourTempoErreur, lire_json


class JourTempoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ajout de Jour Tempo."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        erreurs: dict[str, str] = {}
        if user_input is not None:
            try:
                await lire_json(async_get_clientsession(self.hass), URL_TEMPO)
            except JourTempoErreur:
                erreurs["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=NAME, data={})

        return self.async_show_form(step_id="user", errors=erreurs)
