"""Select platform for Aera for Home."""

from __future__ import annotations

from typing import Any

from aera import AeraDevice

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AeraCoordinator, AeraScheduleSlot

DAYS_EVERY_DAY = [2, 3, 4, 5, 6, 7, 1]
DAYS_WEEKDAYS = [2, 3, 4, 5, 6]
DAYS_WEEKENDS = [7, 1]

DAYS_OPTIONS = ["Every day", "Weekdays", "Weekends"]

SESSION_OPTIONS = ["Off", "2 hours", "4 hours", "8 hours"]
SESSION_DURATIONS = {"Off": 0, "2 hours": 120, "4 hours": 240, "8 hours": 480}


def _days_to_option(days: list[int]) -> str:
    """Convert days_of_week list to a display option."""
    sorted_days = sorted(days)
    if sorted_days == sorted(DAYS_EVERY_DAY):
        return "Every day"
    if sorted_days == sorted(DAYS_WEEKDAYS):
        return "Weekdays"
    if sorted_days == sorted(DAYS_WEEKENDS):
        return "Weekends"
    return "Every day"


def _option_to_days(option: str) -> list[int]:
    """Convert a display option to days_of_week list."""
    if option == "Weekdays":
        return DAYS_WEEKDAYS
    if option == "Weekends":
        return DAYS_WEEKENDS
    return DAYS_EVERY_DAY


def _minutes_to_option(minutes: int | None) -> str:
    """Convert remaining minutes to the closest session option."""
    if not minutes or minutes <= 0:
        return "Off"
    if minutes <= 120:
        return "2 hours"
    if minutes <= 240:
        return "4 hours"
    return "8 hours"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aera select entities."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracked_dsns: set[str] = set()
    tracked_schedule_keys: set[int] = set()

    @callback
    def _add_device_entities(dsns: set[str] | None = None) -> None:
        new_dsns = (dsns or set(coordinator.data.keys())) - tracked_dsns
        if not new_dsns:
            return
        tracked_dsns.update(new_dsns)
        entities: list[SelectEntity] = []
        for dsn in new_dsns:
            data = coordinator.data[dsn]
            if data.device.has_session_feature:
                entities.append(AeraSessionSelect(coordinator, dsn))
        if entities:
            async_add_entities(entities)
        _sync_schedule_entities()

    @callback
    def _sync_schedule_entities() -> None:
        new_entities: list[SelectEntity] = []
        for dsn, data in coordinator.data.items():
            for idx, slot in enumerate(data.schedules):
                if slot.schedule_key not in tracked_schedule_keys:
                    tracked_schedule_keys.add(slot.schedule_key)
                    new_entities.append(AeraScheduleDays(coordinator, dsn, idx))
        if new_entities:
            async_add_entities(new_entities)

    _add_device_entities()
    coordinator.register_new_device_callback(_add_device_entities)
    coordinator.register_schedule_change_callback(_sync_schedule_entities)


class AeraScheduleDays(CoordinatorEntity[AeraCoordinator], SelectEntity):
    """Select entity for schedule days of week."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-week"
    _attr_options = DAYS_OPTIONS
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: AeraCoordinator, dsn: str, slot_idx: int) -> None:
        super().__init__(coordinator)
        self._dsn = dsn
        self._schedule_key = coordinator.data[dsn].schedules[slot_idx].schedule_key
        self._attr_unique_id = f"{dsn}_schedule_{self._schedule_key}_days"
        self._attr_name = f"Schedule {slot_idx + 1} days"

    @property
    def _device(self) -> AeraDevice:
        return self.coordinator.data[self._dsn].device

    @property
    def _slot(self) -> AeraScheduleSlot | None:
        for slot in self.coordinator.data[self._dsn].schedules:
            if slot.schedule_key == self._schedule_key:
                return slot
        return None

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
        return super().available and self._slot is not None

    @property
    def current_option(self) -> str | None:
        slot = self._slot
        if not slot:
            return None
        return _days_to_option(slot.days_of_week)

    async def async_select_option(self, option: str) -> None:
        days = _option_to_days(option)
        await self.coordinator.api.update_schedule(
            self._dsn, self._schedule_key, {"days_of_week": days}
        )
        slot = self._slot
        if slot:
            slot.days_of_week = days
        self.async_write_ha_state()
        self.coordinator.force_schedule_refresh()
        await self.coordinator.async_request_refresh()


class AeraSessionSelect(CoordinatorEntity[AeraCoordinator], SelectEntity):
    """Select entity to start/stop a fragrance session."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:timer-outline"
    _attr_options = SESSION_OPTIONS
    _attr_name = "Session"

    def __init__(self, coordinator: AeraCoordinator, dsn: str) -> None:
        super().__init__(coordinator)
        self._dsn = dsn
        self._attr_unique_id = f"{dsn}_session"

    @property
    def _device(self) -> AeraDevice:
        return self.coordinator.data[self._dsn].device

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
        return super().available and self._device.is_online

    @property
    def current_option(self) -> str | None:
        if self._device.session_active:
            return _minutes_to_option(self._device.session_time_remaining)
        return "Off"

    async def async_select_option(self, option: str) -> None:
        duration = SESSION_DURATIONS[option]
        if duration == 0:
            await self.coordinator.api.set_power(self._dsn, False)
            self._device.update_properties({"power_state": 0, "session_state": 0, "session_time_left": 0})
        else:
            await self.coordinator.api.start_session(self._dsn, duration)
            self._device.update_properties({"power_state": 1, "session_state": 1, "session_time_left": duration})
        self.async_write_ha_state()
