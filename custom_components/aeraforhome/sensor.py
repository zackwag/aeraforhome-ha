"""Sensor platform for Aera for Home."""

from __future__ import annotations

from typing import Any

from aera import AeraDevice

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AeraCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aera sensor entities."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    for dsn in coordinator.data:
        entities.append(AeraFragranceNameSensor(coordinator, dsn))
        entities.append(AeraFragranceRemainingSensor(coordinator, dsn))
    async_add_entities(entities)


class AeraBaseSensor(CoordinatorEntity[AeraCoordinator], SensorEntity):
    """Base class for Aera sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AeraCoordinator, dsn: str) -> None:
        super().__init__(coordinator)
        self._dsn = dsn

    @property
    def _device(self) -> AeraDevice:
        return self.coordinator.data[self._dsn]

    @property
    def device_info(self) -> dict[str, Any]:
        device = self._device
        return {
            "identifiers": {(DOMAIN, self._dsn)},
            "name": device.device_name,
            "manufacturer": "Aera",
            "model": device.device_type.name.replace("_", " ").title(),
            "sw_version": device.firmware_version,
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
