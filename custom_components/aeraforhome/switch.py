"""Switch platform for Aera for Home schedules."""

from __future__ import annotations

from typing import Any

from aera import AeraDevice

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AeraCoordinator, AeraScheduleSlot


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aera schedule switch entities."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracked_keys: set[int] = set()

    @callback
    def _sync_entities() -> None:
        current_keys: set[int] = set()
        new_entities: list[SwitchEntity] = []
        for dsn, data in coordinator.data.items():
            for idx, slot in enumerate(data.schedules):
                current_keys.add(slot.schedule_key)
                if slot.schedule_key not in tracked_keys:
                    new_entities.append(AeraScheduleSwitch(coordinator, dsn, idx))
        tracked_keys.update(current_keys)
        if new_entities:
            async_add_entities(new_entities)

    _sync_entities()
    coordinator.register_new_device_callback(lambda _: _sync_entities())
    coordinator.register_schedule_change_callback(_sync_entities)


class AeraScheduleSwitch(CoordinatorEntity[AeraCoordinator], SwitchEntity):
    """Switch to enable/disable a schedule slot."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-clock"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: AeraCoordinator, dsn: str, slot_idx: int) -> None:
        super().__init__(coordinator)
        self._dsn = dsn
        self._schedule_key = coordinator.data[dsn].schedules[slot_idx].schedule_key
        self._attr_unique_id = f"{dsn}_schedule_{self._schedule_key}"
        self._attr_name = f"Schedule {slot_idx + 1}"

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
    def is_on(self) -> bool:
        slot = self._slot
        return slot.active if slot else False

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api.update_schedule(
            self._dsn, self._schedule_key, {"active": True}
        )
        slot = self._slot
        if slot:
            slot.active = True
        self.async_write_ha_state()
        self.coordinator.force_schedule_refresh()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.update_schedule(
            self._dsn, self._schedule_key, {"active": False}
        )
        slot = self._slot
        if slot:
            slot.active = False
        self.async_write_ha_state()
        self.coordinator.force_schedule_refresh()
        await self.coordinator.async_request_refresh()
