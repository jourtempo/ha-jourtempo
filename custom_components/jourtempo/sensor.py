"""Capteurs Jour Tempo : couleurs, jours restants, EJP."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COULEURS, EJP_ETATS
from .coordinator import JourTempoConfigEntry, JourTempoCoordinator, est_perime
from .entity import JourTempoEntity


def _couleur(fichier: dict[str, Any], jour: str) -> str | None:
    code = (fichier.get(jour) or {}).get("code")
    return code if code in COULEURS else None  # « inconnu » avant l'annonce de RTE


def _ejp(fichier: dict[str, Any], jour: str) -> str | None:
    code = str((fichier.get(jour) or {}).get("code") or "").replace("-", "_")
    return code if code in EJP_ETATS else None


def _restants(couleur: str) -> Callable[[dict[str, Any]], int | None]:
    def lire(fichier: dict[str, Any]) -> int | None:
        compteur = ((fichier.get("saison") or {}).get("compteurs") or {}).get(couleur) or {}
        valeur = compteur.get("restants")
        return valeur if isinstance(valeur, int) else None

    return lire


def _attributs_jour(jour: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def lire(fichier: dict[str, Any]) -> dict[str, Any]:
        bloc = fichier.get(jour) or {}
        return {"date": bloc.get("date"), "libelle": bloc.get("libelle"), "perime_apres": fichier.get("perime_apres")}

    return lire


def _attributs_compteur(couleur: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def lire(fichier: dict[str, Any]) -> dict[str, Any]:
        saison = fichier.get("saison") or {}
        compteur = (saison.get("compteurs") or {}).get(couleur) or {}
        return {"saison": saison.get("periode"), "quota": compteur.get("quota"), "tombes": compteur.get("tombes")}

    return lire


@dataclass(frozen=True, kw_only=True)
class JourTempoSensorDescription(SensorEntityDescription):
    """Où lire la valeur dans l'API."""

    fichier: str  # "tempo" ou "ejp"
    valeur: Callable[[dict[str, Any]], Any]
    attributs: Callable[[dict[str, Any]], dict[str, Any]] | None = None


CAPTEURS: tuple[JourTempoSensorDescription, ...] = (
    JourTempoSensorDescription(
        key="couleur_aujourdhui",
        translation_key="couleur_aujourdhui",
        device_class=SensorDeviceClass.ENUM,
        options=COULEURS,
        fichier="tempo",
        valeur=lambda f: _couleur(f, "aujourdhui"),
        attributs=_attributs_jour("aujourdhui"),
    ),
    JourTempoSensorDescription(
        key="couleur_demain",
        translation_key="couleur_demain",
        device_class=SensorDeviceClass.ENUM,
        options=COULEURS,
        fichier="tempo",
        valeur=lambda f: _couleur(f, "demain"),
        attributs=_attributs_jour("demain"),
    ),
    *(
        JourTempoSensorDescription(
            key=f"jours_restants_{couleur}",
            translation_key=f"jours_restants_{couleur}",
            state_class=SensorStateClass.MEASUREMENT,
            fichier="tempo",
            valeur=_restants(couleur),
            attributs=_attributs_compteur(couleur),
        )
        for couleur in COULEURS
    ),
    JourTempoSensorDescription(
        key="ejp_aujourdhui",
        translation_key="ejp_aujourdhui",
        device_class=SensorDeviceClass.ENUM,
        options=EJP_ETATS,
        fichier="ejp",
        valeur=lambda f: _ejp(f, "aujourdhui"),
        attributs=_attributs_jour("aujourdhui"),
    ),
    JourTempoSensorDescription(
        key="ejp_demain",
        translation_key="ejp_demain",
        device_class=SensorDeviceClass.ENUM,
        options=EJP_ETATS,
        fichier="ejp",
        valeur=lambda f: _ejp(f, "demain"),
        attributs=_attributs_jour("demain"),
    ),
    JourTempoSensorDescription(
        key="ejp_jours_restants",
        translation_key="ejp_jours_restants",
        state_class=SensorStateClass.MEASUREMENT,
        fichier="ejp",
        valeur=_restants("ejp"),
        attributs=_attributs_compteur("ejp"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: JourTempoConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(JourTempoSensor(coordinator, description) for description in CAPTEURS)


class JourTempoSensor(JourTempoEntity, SensorEntity):
    """Un capteur lu dans tempo.json ou ejp.json."""

    entity_description: JourTempoSensorDescription
    _plateforme = "sensor"

    def __init__(self, coordinator: JourTempoCoordinator, description: JourTempoSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    def _fichier(self) -> dict[str, Any] | None:
        fichier = getattr(self.coordinator.data, self.entity_description.fichier, None)
        return None if est_perime(fichier) else fichier

    @property
    def native_value(self) -> Any:
        fichier = self._fichier()
        return None if fichier is None else self.entity_description.valeur(fichier)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        fichier = getattr(self.coordinator.data, self.entity_description.fichier, None)
        if not fichier or self.entity_description.attributs is None:
            return None
        return self.entity_description.attributs(fichier)
