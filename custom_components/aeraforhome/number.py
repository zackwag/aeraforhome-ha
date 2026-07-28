"""Number platform for Aera for Home schedules."""

from __future__ import annotations

from typing import Any

from aera import AeraDevice

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AeraCoordinator, AeraScheduleSlot


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aera schedule number entities."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracked_keys: set[int] = set()

    @callback
    def _sync_entities() -> None:
        new_entities: list[NumberEntity] = []
        for dsn, data in coordinator.data.items():
            for idx, slot in enumerate(data.schedules):
                if slot.schedule_key not in tracked_keys:
                    tracked_keys.add(slot.schedule_key)
                    new_entities.append(AeraScheduleIntensity(coordinator, dsn, idx))
        if new_entities:
            async_add_entities(new_entities)

    _sync_entities()
    coordinator.register_new_device_callback(lambda _: _sync_entities())
    coordinator.register_schedule_change_callback(_sync_entities)


class AeraScheduleIntensity(CoordinatorEntity[AeraCoordinator], NumberEntity):
    """Number entity for schedule fragrance intensity."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:scent"
    _attr_native_min_value = 1
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: AeraCoordinator, dsn: str, slot_idx: int) -> None:
        super().__init__(coordinator)
        self._dsn = dsn
        self._slot_idx = slot_idx
        slot = self._slot
        self._attr_unique_id = f"{dsn}_schedule_{slot.schedule_key}_intensity"
        self._attr_name = f"Schedule {slot_idx + 1} intensity"

    @property
    def _device(self) -> AeraDevice:
        return self.coordinator.data[self._dsn].device

    @property
    def _slot(self) -> AeraScheduleSlot:
        return self.coordinator.data[self._dsn].schedules[self._slot_idx]

    @property
    def native_max_value(self) -> float:
        return float(self._device.max_intensity)

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

    @property
    def native_value(self) -> float | None:
        return float(self._slot.intensity)

    async def async_set_native_value(self, value: float) -> None:
        slot = self._slot
        int_value = int(value)
        if slot.action_key:
            await self.coordinator.api.update_schedule_action(
                slot.action_key, {"value": int_value}
            )
        else:
            await self.coordinator.api.create_schedule_action(
                slot.schedule_key,
                {
                    "name": "set_intensity_sched",
                    "value": str(int_value),
                    "base_type": "integer",
                    "active": True,
                    "at_start": True,
                    "at_end": False,
                    "in_range": False,
                },
            )
        self.coordinator.force_schedule_refresh()
        await self.coordinator.async_request_refresh()
