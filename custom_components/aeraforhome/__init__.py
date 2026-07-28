"""The Aera for Home integration."""

from __future__ import annotations

import voluptuous as vol

from aera import AeraApi
from aera.api import AeraAuthError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN
from .coordinator import AeraCoordinator

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.FAN,
    Platform.IMAGE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TIME,
]

SERVICE_CREATE_SCHEDULE = "create_schedule"
SERVICE_DELETE_SCHEDULE = "delete_schedule"

CREATE_SCHEDULE_SCHEMA = vol.Schema({
    vol.Required("entity_id"): str,
    vol.Required("start_time"): str,
    vol.Required("end_time"): str,
    vol.Optional("days", default="every_day"): vol.In(
        ["every_day", "weekdays", "weekends"]
    ),
    vol.Optional("intensity", default=5): vol.All(
        vol.Coerce(int), vol.Range(min=1, max=10)
    ),
})

DELETE_SCHEDULE_SCHEMA = vol.Schema({
    vol.Required("entity_id"): str,
})

DAYS_MAP = {
    "every_day": [2, 3, 4, 5, 6, 7, 1],
    "weekdays": [2, 3, 4, 5, 6],
    "weekends": [7, 1],
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aera for Home from a config entry."""
    session = async_get_clientsession(hass)
    api = AeraApi(
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        session=session,
    )
    try:
        await api.login()
    except AeraAuthError as err:
        raise ConfigEntryAuthFailed from err

    coordinator = AeraCoordinator(hass, api)
    coordinator.config_entry_id = entry.entry_id
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _handle_create_schedule(call: ServiceCall) -> None:
        entity_id = call.data["entity_id"]
        dsn = _dsn_from_entity_id(hass, entity_id)
        if not dsn:
            return
        coord = _get_coordinator(hass, dsn)
        if not coord:
            return
        days = DAYS_MAP[call.data["days"]]
        await coord.async_create_schedule(
            dsn=dsn,
            start_time=call.data["start_time"],
            end_time=call.data["end_time"],
            days_of_week=days,
            intensity=call.data["intensity"],
        )

    async def _handle_delete_schedule(call: ServiceCall) -> None:
        entity_id = call.data["entity_id"]
        ent_reg = er.async_get(hass)
        entity_entry = ent_reg.async_get(entity_id)
        if not entity_entry:
            return
        unique_id = entity_entry.unique_id
        parts = unique_id.split("_schedule_")
        if len(parts) != 2:
            return
        dsn = parts[0]
        schedule_key = int(parts[1])
        coord = _get_coordinator(hass, dsn)
        if not coord:
            return
        await coord.async_delete_schedule(dsn, schedule_key)

    if not hass.services.has_service(DOMAIN, SERVICE_CREATE_SCHEDULE):
        hass.services.async_register(
            DOMAIN, SERVICE_CREATE_SCHEDULE, _handle_create_schedule, CREATE_SCHEDULE_SCHEMA
        )
        hass.services.async_register(
            DOMAIN, SERVICE_DELETE_SCHEDULE, _handle_delete_schedule, DELETE_SCHEDULE_SCHEMA
        )

    return True


def _dsn_from_entity_id(hass: HomeAssistant, entity_id: str) -> str | None:
    """Extract the DSN from any Aera entity's device identifiers."""
    ent_reg = er.async_get(hass)
    entity_entry = ent_reg.async_get(entity_id)
    if not entity_entry or not entity_entry.device_id:
        return None
    dev_reg = dr.async_get(hass)
    device_entry = dev_reg.async_get(entity_entry.device_id)
    if not device_entry:
        return None
    for identifier in device_entry.identifiers:
        if identifier[0] == DOMAIN:
            return identifier[1]
    return None


def _get_coordinator(hass: HomeAssistant, dsn: str) -> AeraCoordinator | None:
    """Find the coordinator that manages a given DSN."""
    for entry_data in hass.data.get(DOMAIN, {}).values():
        if isinstance(entry_data, AeraCoordinator) and dsn in entry_data.data:
            return entry_data
    return None


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: AeraCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.close()
    if not hass.data.get(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_CREATE_SCHEDULE)
        hass.services.async_remove(DOMAIN, SERVICE_DELETE_SCHEDULE)
    return unload_ok
