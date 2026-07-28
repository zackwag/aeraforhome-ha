"""Time platform for Aera for Home schedules."""

from __future__ import annotations

from datetime import time as dt_time
from typing import Any

from aera import AeraDevice

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AeraCoordinator, AeraScheduleSlot


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aera schedule time entities."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracked_keys: set[str] = set()

    @callback
    def _sync_entities() -> None:
        new_entities: list[TimeEntity] = []
        for dsn, data in coordinator.data.items():
            for idx, slot in enumerate(data.schedules):
                start_key = f"{slot.schedule_key}_start"
                end_key = f"{slot.schedule_key}_end"
                if start_key not in tracked_keys:
                    tracked_keys.add(start_key)
                    new_entities.append(AeraScheduleStartTime(coordinator, dsn, idx))
                if end_key not in tracked_keys:
                    tracked_keys.add(end_key)
                    new_entities.append(AeraScheduleEndTime(coordinator, dsn, idx))
        if new_entities:
            async_add_entities(new_entities)

    _sync_entities()
    coordinator.register_new_device_callback(lambda _: _sync_entities())
    coordinator.register_schedule_change_callback(_sync_entities)


def _parse_time(time_str: str) -> dt_time:
    """Parse HH:MM:SS to a time object."""
    parts = time_str.split(":")
    return dt_time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)


class AeraScheduleBaseTime(CoordinatorEntity[AeraCoordinator], TimeEntity):
    """Base class for schedule time entities."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator: AeraCoordinator, dsn: str, slot_idx: int) -> None:
        super().__init__(coordinator)
        self._dsn = dsn
        self._slot_idx = slot_idx

    @property
    def _device(self) -> AeraDevice:
        return self.coordinator.data[self._dsn].device

    @property
    def _slot(self) -> AeraScheduleSlot:
        return self.coordinator.data[self._dsn].schedules[self._slot_idx]

    @property
    def device_info(self) -> dict[str, Any]:
        device = self._device
        return {
            "identifiers": {(DOMAIN, self._dsn)},
            "name": device.device_name,
            "manufacturer": "Aera",
            "model": device.device_type.name.replace("_", " ").title(),
            "sw_version": device.firmware_version,
            "suggested_area": device.room_name,
        }

    @property
    def available(self) -> bool:
        return super().available and self._slot_idx < len(
            self.coordinator.data[self._dsn].schedules
        )


class AeraScheduleStartTime(AeraScheduleBaseTime):
    """Start time for a schedule slot."""

    def __init__(self, coordinator: AeraCoordinator, dsn: str, slot_idx: int) -> None:
        super().__init__(coordinator, dsn, slot_idx)
        slot = self._slot
        self._attr_unique_id = f"{dsn}_schedule_{slot.schedule_key}_start"
        self._attr_name = f"Schedule {slot_idx + 1} start time"

    @property
    def native_value(self) -> dt_time | None:
        return _parse_time(self._slot.start_time)

    async def async_set_value(self, value: dt_time) -> None:
        time_str = value.strftime("%H:%M:%S")
        await self.coordinator.api.update_schedule(
            self._slot.schedule_key, {"start_time_each_day": time_str}
        )
        self.coordinator.force_schedule_refresh()
        await self.coordinator.async_request_refresh()


class AeraScheduleEndTime(AeraScheduleBaseTime):
    """End time for a schedule slot."""

    def __init__(self, coordinator: AeraCoordinator, dsn: str, slot_idx: int) -> None:
        super().__init__(coordinator, dsn, slot_idx)
        slot = self._slot
        self._attr_unique_id = f"{dsn}_schedule_{slot.schedule_key}_end"
        self._attr_name = f"Schedule {slot_idx + 1} end time"

    @property
    def native_value(self) -> dt_time | None:
        return _parse_time(self._slot.end_time)

    async def async_set_value(self, value: dt_time) -> None:
        time_str = value.strftime("%H:%M:%S")
        await self.coordinator.api.update_schedule(
            self._slot.schedule_key, {"end_time_each_day": time_str}
        )
        self.coordinator.force_schedule_refresh()
        await self.coordinator.async_request_refresh()
