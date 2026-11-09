"""Jour Tempo : couleur Tempo et jour EJP depuis l'API gratuite de jourtempo.fr."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import JourTempoConfigEntry, JourTempoCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: JourTempoConfigEntry) -> bool:
    """Démarre l'intégration."""
    coordinator = JourTempoCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: JourTempoConfigEntry) -> bool:
    """Arrête l'intégration."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
