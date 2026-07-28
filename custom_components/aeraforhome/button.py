"""Button platform for Aera for Home."""

from __future__ import annotations

from typing import Any

from aera import AeraDevice

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AeraCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aera button entities."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracked: set[str] = set()

    @callback
    def _add_entities(dsns: set[str] | None = None) -> None:
        new_dsns = (dsns or set(coordinator.data.keys())) - tracked
        if not new_dsns:
            return
        tracked.update(new_dsns)
        entities: list[ButtonEntity] = []
        for dsn in new_dsns:
            device = coordinator.data[dsn].device
            if device.device_type.is_full_size:
                entities.append(AeraEjectButton(coordinator, dsn))
        async_add_entities(entities)

    _add_entities()
    coordinator.register_new_device_callback(_add_entities)


class AeraEjectButton(CoordinatorEntity[AeraCoordinator], ButtonEntity):
    """Button to eject the fragrance cartridge."""

    _attr_has_entity_name = True
    _attr_name = "Eject cartridge"
    _attr_icon = "mdi:eject"

    def __init__(self, coordinator: AeraCoordinator, dsn: str) -> None:
        super().__init__(coordinator)
        self._dsn = dsn
        self._attr_unique_id = f"{dsn}_eject"

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
        return (
            super().available
            and self._device.is_online
            and self._device.is_cartridge_present is True
        )

    async def async_press(self) -> None:
        await self.coordinator.api.eject_cartridge(self._dsn)
        await self.coordinator.async_request_refresh()
