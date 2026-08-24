"""Button platform for Aera for Home schedule deletion."""

from __future__ import annotations

from typing import Any

from aera import AeraDevice

from homeassistant.components.button import ButtonEntity
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
    """Set up Aera schedule delete button entities."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracked_keys: set[int] = set()

    @callback
    def _sync_entities() -> None:
        new_entities: list[ButtonEntity] = []
        for dsn, data in coordinator.data.items():
            for idx, slot in enumerate(data.schedules):
                if slot.schedule_key not in tracked_keys:
                    tracked_keys.add(slot.schedule_key)
                    new_entities.append(AeraScheduleDeleteButton(coordinator, dsn, idx))
        if new_entities:
            async_add_entities(new_entities)

    _sync_entities()
    coordinator.register_new_device_callback(lambda _: _sync_entities())
    coordinator.register_schedule_change_callback(_sync_entities)


class AeraScheduleDeleteButton(CoordinatorEntity[AeraCoordinator], ButtonEntity):
    """Button to delete a schedule."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-remove"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: AeraCoordinator, dsn: str, slot_idx: int) -> None:
        super().__init__(coordinator)
        self._dsn = dsn
        self._schedule_key = coordinator.data[dsn].schedules[slot_idx].schedule_key
        self._attr_unique_id = f"{dsn}_schedule_{self._schedule_key}_delete"
        self._attr_name = f"Schedule {slot_idx + 1} delete"

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

    async def async_press(self) -> None:
        await self.coordinator.async_delete_schedule(self._dsn, self._schedule_key)
