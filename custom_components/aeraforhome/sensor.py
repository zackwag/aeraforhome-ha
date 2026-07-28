"""Sensor platform for Aera for Home."""

from __future__ import annotations

from typing import Any

from aera import AeraDevice

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AeraCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aera sensor entities."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracked: set[str] = set()

    @callback
    def _add_entities(dsns: set[str] | None = None) -> None:
        new_dsns = (dsns or set(coordinator.data.keys())) - tracked
        if not new_dsns:
            return
        tracked.update(new_dsns)
        entities: list[SensorEntity] = []
        for dsn in new_dsns:
            entities.append(AeraFragranceNameSensor(coordinator, dsn))
            entities.append(AeraFragranceRemainingSensor(coordinator, dsn))
            device = coordinator.data[dsn].device
            if device.has_session_feature:
                entities.append(AeraSessionTimeSensor(coordinator, dsn))
            if device.device_type.is_mini:
                entities.append(AeraFragranceCodeSensor(coordinator, dsn))
        async_add_entities(entities)

    _add_entities()
    coordinator.register_new_device_callback(_add_entities)


class AeraBaseSensor(CoordinatorEntity[AeraCoordinator], SensorEntity):
    """Base class for Aera sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AeraCoordinator, dsn: str) -> None:
        super().__init__(coordinator)
        self._dsn = dsn

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


class AeraFragranceNameSensor(AeraBaseSensor):
    """Sensor for the current fragrance name."""

    _attr_name = "Fragrance"
    _attr_icon = "mdi:flower"

    def __init__(self, coordinator: AeraCoordinator, dsn: str) -> None:
        super().__init__(coordinator, dsn)
        self._attr_unique_id = f"{dsn}_fragrance_name"

    @property
    def native_value(self) -> str | None:
        return self._device.fragrance_name


class AeraFragranceRemainingSensor(AeraBaseSensor):
    """Sensor for fragrance remaining percentage."""

    _attr_name = "Fragrance remaining"
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:gauge"

    def __init__(self, coordinator: AeraCoordinator, dsn: str) -> None:
        super().__init__(coordinator, dsn)
        self._attr_unique_id = f"{dsn}_fragrance_remaining"

    @property
    def native_value(self) -> int | None:
        return self._device.fragrance_remaining


class AeraSessionTimeSensor(AeraBaseSensor):
    """Sensor for session time remaining."""

    _attr_name = "Session time remaining"
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator: AeraCoordinator, dsn: str) -> None:
        super().__init__(coordinator, dsn)
        self._attr_unique_id = f"{dsn}_session_time_remaining"

    @property
    def native_value(self) -> int | None:
        if not self._device.session_active:
            return None
        return self._device.session_time_remaining


class AeraFragranceCodeSensor(AeraBaseSensor):
    """Sensor for the fragrance code (Mini devices)."""

    _attr_name = "Fragrance code"
    _attr_icon = "mdi:numeric"

    def __init__(self, coordinator: AeraCoordinator, dsn: str) -> None:
        super().__init__(coordinator, dsn)
        self._attr_unique_id = f"{dsn}_fragrance_code"

    @property
    def native_value(self) -> str | None:
        info = self._device.fragrance_info
        if info and info.fragrance_id:
            return info.fragrance_id
        return None
