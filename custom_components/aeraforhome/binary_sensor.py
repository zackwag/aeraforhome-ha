"""Binary sensor platform for Aera for Home."""

from __future__ import annotations

from typing import Any

from aera import AeraDevice

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AeraCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aera binary sensor entities."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracked: set[str] = set()

    @callback
    def _add_entities(dsns: set[str] | None = None) -> None:
        new_dsns = (dsns or set(coordinator.data.keys())) - tracked
        if not new_dsns:
            return
        tracked.update(new_dsns)
        entities: list[BinarySensorEntity] = []
        for dsn in new_dsns:
            device = coordinator.data[dsn].device
            entities.append(AeraConnectivitySensor(coordinator, dsn))
            entities.append(AeraDeviceProblemSensor(coordinator, dsn))
            if device.device_type.is_full_size:
                entities.append(AeraCartridgePresentSensor(coordinator, dsn))
        async_add_entities(entities)

    _add_entities()
    coordinator.register_new_device_callback(_add_entities)


class AeraConnectivitySensor(CoordinatorEntity[AeraCoordinator], BinarySensorEntity):
    """Binary sensor for device online/offline status."""

    _attr_has_entity_name = True
    _attr_name = "Connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: AeraCoordinator, dsn: str) -> None:
        super().__init__(coordinator)
        self._dsn = dsn
        self._attr_unique_id = f"{dsn}_connectivity"

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
    def is_on(self) -> bool | None:
        return self._device.is_online


class AeraCartridgePresentSensor(CoordinatorEntity[AeraCoordinator], BinarySensorEntity):
    """Binary sensor for cartridge presence (full-size devices)."""

    _attr_has_entity_name = True
    _attr_name = "Cartridge"
    _attr_device_class = BinarySensorDeviceClass.PLUG

    def __init__(self, coordinator: AeraCoordinator, dsn: str) -> None:
        super().__init__(coordinator)
        self._dsn = dsn
        self._attr_unique_id = f"{dsn}_cartridge_present"

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
    def is_on(self) -> bool | None:
        return self._device.is_cartridge_present


class AeraDeviceProblemSensor(CoordinatorEntity[AeraCoordinator], BinarySensorEntity):
    """Binary sensor for device error condition."""

    _attr_has_entity_name = True
    _attr_name = "Problem"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: AeraCoordinator, dsn: str) -> None:
        super().__init__(coordinator)
        self._dsn = dsn
        self._attr_unique_id = f"{dsn}_problem"

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
    def is_on(self) -> bool | None:
        return self._device.has_error

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self._device.has_error:
            return {"error_code": self._device.error_condition}
        return None
