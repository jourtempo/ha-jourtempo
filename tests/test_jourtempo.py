"""Tests : config flow, capteurs, péremption, panne."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util

from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.jourtempo.const import DOMAIN, URL_EJP, URL_TEMPO, USER_AGENT

TEMPO = {
    "api": "v1",
    "perime_apres": "2026-12-04T12:00:00+01:00",
    "aujourdhui": {"date": "2026-12-03", "code": "blanc", "libelle": "Blanc"},
    "demain": {"date": "2026-12-04", "code": "rouge", "libelle": "Rouge"},
    "saison": {
        "periode": "2026-2027",
        "compteurs": {
            "bleu": {"quota": 300, "tombes": 80, "restants": 220},
            "blanc": {"quota": 43, "tombes": 5, "restants": 38},
            "rouge": {"quota": 22, "tombes": 3, "restants": 19},
        },
    },
}
EJP = {
    "api": "v1",
    "perime_apres": "2026-12-04T12:00:00+01:00",
    "aujourdhui": {"date": "2026-12-03", "ejp": False, "code": "normal", "libelle": "Jour normal"},
    "demain": {"date": "2026-12-04", "ejp": None, "code": "non-verifie", "libelle": "Pas encore publié"},
    "saison": {"periode": "2026-2027", "compteurs": {"ejp": {"quota": 22, "tombes": 4, "restants": 18}}},
}
MAINTENANT = "2026-12-03T14:00:00+01:00"


def _api(aioclient_mock: AiohttpClientMocker, tempo=TEMPO, ejp=EJP) -> None:
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL_TEMPO, json=tempo)
    aioclient_mock.get(URL_EJP, json=ejp)


async def _installer(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, title="Jour Tempo", data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.mark.freeze_time(MAINTENANT)
async def test_config_flow(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    _api(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Jour Tempo"
    await hass.async_block_till_done()
    # Une seule instance possible.
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.ABORT


async def test_config_flow_injoignable(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(URL_TEMPO, status=403)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.freeze_time(MAINTENANT)
async def test_capteurs(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    _api(aioclient_mock)
    await _installer(hass)
    attendu = {
        "sensor.jourtempo_couleur_aujourdhui": "blanc",
        "sensor.jourtempo_couleur_demain": "rouge",
        "sensor.jourtempo_jours_restants_bleu": "220",
        "sensor.jourtempo_jours_restants_blanc": "38",
        "sensor.jourtempo_jours_restants_rouge": "19",
        "sensor.jourtempo_ejp_aujourdhui": "normal",
        "sensor.jourtempo_ejp_demain": "non_verifie",
        "sensor.jourtempo_ejp_jours_restants": "18",
        "binary_sensor.jourtempo_demain_rouge": "on",
    }
    for entity_id, etat in attendu.items():
        state = hass.states.get(entity_id)
        assert state is not None, entity_id
        assert state.state == etat, (entity_id, state.state)
    # User-Agent explicite, sinon Cloudflare répond 403.
    for _method, _url, _data, headers in aioclient_mock.mock_calls:
        assert headers["User-Agent"] == USER_AGENT


@pytest.mark.freeze_time(MAINTENANT)
async def test_demain_inconnu(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    tempo = {**TEMPO, "demain": {"date": "2026-12-04", "code": "inconnu", "libelle": "Pas encore annoncée"}}
    _api(aioclient_mock, tempo=tempo)
    await _installer(hass)
    assert hass.states.get("sensor.jourtempo_couleur_demain").state == "unknown"
    assert hass.states.get("binary_sensor.jourtempo_demain_rouge").state == "unknown"
    assert hass.states.get("sensor.jourtempo_couleur_aujourdhui").state == "blanc"


@pytest.mark.freeze_time(MAINTENANT)
async def test_perime_puis_panne(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    _api(aioclient_mock)
    await _installer(hass)
    assert hass.states.get("sensor.jourtempo_couleur_aujourdhui").state == "blanc"

    # Panne de l'API : la dernière valeur reste tant qu'elle n'est pas périmée.
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL_TEMPO, status=500)
    aioclient_mock.get(URL_EJP, status=500)
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get("sensor.jourtempo_couleur_aujourdhui").state == "blanc"

    # Au-delà de perime_apres : inconnu partout.
    freezer.move_to("2026-12-04T12:05:00+01:00")
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done(wait_background_tasks=True)
    for entity_id in (
        "sensor.jourtempo_couleur_aujourdhui",
        "sensor.jourtempo_couleur_demain",
        "sensor.jourtempo_jours_restants_rouge",
        "sensor.jourtempo_ejp_demain",
        "binary_sensor.jourtempo_demain_rouge",
    ):
        assert hass.states.get(entity_id).state == "unknown", entity_id

    # Retour de l'API : les valeurs reviennent.
    _api(aioclient_mock, tempo={**TEMPO, "perime_apres": "2026-12-05T12:00:00+01:00"})
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get("sensor.jourtempo_couleur_aujourdhui").state == "blanc"


@pytest.mark.freeze_time(MAINTENANT)
async def test_dechargement(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    _api(aioclient_mock)
    entry = await _installer(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED
