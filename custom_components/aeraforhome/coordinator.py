"""Data update coordinator for Aera for Home."""

from __future__ import annotations

import logging
from datetime import timedelta

from aera import AeraApi, AeraDevice
from aera.api import AeraAuthError, AeraApiError

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class AeraCoordinator(DataUpdateCoordinator[dict[str, AeraDevice]]):
    """Coordinator to poll Aera device state."""

    def __init__(self, hass: HomeAssistant, api: AeraApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.api = api
        self.known_dsns: set[str] = set()
        self.new_device_callbacks: list[callback] = []

    def register_new_device_callback(self, cb: callback) -> None:
        """Register a callback to be called when new devices are discovered."""
        self.new_device_callbacks.append(cb)

    async def _async_update_data(self) -> dict[str, AeraDevice]:
        try:
            devices = await self.api.get_devices()
            for device in devices:
                await self.api.get_device_properties(device)
            result = {device.dsn: device for device in devices}

            new_dsns = set(result.keys()) - self.known_dsns
            if self.known_dsns and new_dsns:
                _LOGGER.debug("New Aera devices discovered: %s", new_dsns)
                for cb in self.new_device_callbacks:
                    cb(new_dsns)
            self.known_dsns = set(result.keys())

            return result
        except AeraAuthError as err:
            raise ConfigEntryAuthFailed from err
        except AeraApiError as err:
            raise UpdateFailed(f"Error communicating with Aera API: {err}") from err
