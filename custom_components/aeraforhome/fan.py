"""Fan platform for Aera for Home."""

from __future__ import annotations

import math
from typing import Any

from aera import AeraDevice

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AeraCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aera fan entities."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AeraFanEntity(coordinator, dsn) for dsn in coordinator.data
    )


class AeraFanEntity(CoordinatorEntity[AeraCoordinator], FanEntity):
    """Representation of an Aera diffuser as a fan."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF

    def __init__(self, coordinator: AeraCoordinator, dsn: str) -> None:
        super().__init__(coordinator)
        self._dsn = dsn
        self._attr_unique_id = dsn

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

    @property
    def is_on(self) -> bool | None:
        return self._device.is_power_on

    @property
    def percentage(self) -> int | None:
        intensity = self._device.intensity
        if intensity is None:
            return None
        max_intensity = self._device.max_intensity
        return math.ceil(intensity * 100 / max_intensity)

    @property
    def speed_count(self) -> int:
        return self._device.max_intensity

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        await self.coordinator.api.set_power(self._dsn, True)
        if percentage is not None:
            await self._async_set_percentage(percentage)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_power(self._dsn, False)
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        await self._async_set_percentage(percentage)
        await self.coordinator.async_request_refresh()

    async def _async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.coordinator.api.set_power(self._dsn, False)
            return
        max_intensity = self._device.max_intensity
        level = math.ceil(percentage * max_intensity / 100)
        level = max(1, min(level, max_intensity))
        await self.coordinator.api.set_intensity(self._dsn, level)
