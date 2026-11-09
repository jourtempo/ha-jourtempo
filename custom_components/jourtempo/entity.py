"""Base commune des entités Jour Tempo."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME, URL_DOC
from .coordinator import JourTempoCoordinator


class JourTempoEntity(CoordinatorEntity[JourTempoCoordinator]):
    """Entité rattachée à l'appareil « Jour Tempo »."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _plateforme: str  # "sensor" ou "binary_sensor"

    def __init__(self, coordinator: JourTempoCoordinator, cle: str) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = cle
        self._attr_unique_id = f"{DOMAIN}_{cle}"
        # Identifiant stable, quelle que soit la langue de Home Assistant.
        self.entity_id = f"{self._plateforme}.{DOMAIN}_{cle}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name=NAME,
            manufacturer=NAME,
            model="API v1",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=URL_DOC,
        )
