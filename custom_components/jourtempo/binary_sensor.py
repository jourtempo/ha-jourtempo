"""Capteur binaire « demain rouge »."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import JourTempoConfigEntry, est_perime
from .entity import JourTempoEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: JourTempoConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([JourTempoDemainRouge(entry.runtime_data, "demain_rouge")])


class JourTempoDemainRouge(JourTempoEntity, BinarySensorEntity):
    """Allumé quand RTE a annoncé un jour rouge pour demain."""

    _plateforme = "binary_sensor"

    @property
    def is_on(self) -> bool | None:
        tempo: dict[str, Any] | None = self.coordinator.data.tempo
        if est_perime(tempo):
            return None
        code = (tempo.get("demain") or {}).get("code")
        if code not in ("bleu", "blanc", "rouge"):
            return None  # couleur pas encore annoncée
        return code == "rouge"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        tempo = self.coordinator.data.tempo
        if not tempo:
            return None
        return {"date": (tempo.get("demain") or {}).get("date")}
