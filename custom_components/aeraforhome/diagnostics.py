"""Diagnostics support for Aera for Home."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import AeraCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]
    devices_diag: dict[str, Any] = {}

    for dsn, data in coordinator.data.items():
        device = data.device
        devices_diag[dsn] = {
            "device_name": device.device_name,
            "room_name": device.room_name,
            "device_type": device.device_type.name,
            "oem_model": device.oem_model,
            "is_online": device.is_online,
            "is_power_on": device.is_power_on,
            "intensity": device.intensity,
            "max_intensity": device.max_intensity,
            "fragrance_name": device.fragrance_name,
            "fragrance_remaining": device.fragrance_remaining,
            "is_cartridge_present": device.is_cartridge_present,
            "session_active": device.session_active,
            "session_time_remaining": device.session_time_remaining,
            "has_error": device.has_error,
            "error_condition": device.error_condition,
            "sw_version": device.sw_version,
            "firmware_version": device.firmware_version,
            "schedules": [
                {
                    "schedule_key": slot.schedule_key,
                    "slot_name": slot.slot_name,
                    "active": slot.active,
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                    "days_of_week": slot.days_of_week,
                    "intensity": slot.intensity,
                    "action_key": slot.action_key,
                }
                for slot in data.schedules
            ],
        }

    return {
        "device_count": len(devices_diag),
        "devices": devices_diag,
    }
