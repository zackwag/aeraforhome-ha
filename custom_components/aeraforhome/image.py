"""Image platform for Aera for Home."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

import qrcode

from aera import AeraDevice

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AeraCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aera image entities."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracked: set[str] = set()

    @callback
    def _add_entities(dsns: set[str] | None = None) -> None:
        new_dsns = (dsns or set(coordinator.data.keys())) - tracked
        if not new_dsns:
            return
        tracked.update(new_dsns)
        entities: list[ImageEntity] = []
        for dsn in new_dsns:
            device = coordinator.data[dsn].device
            if device.device_type.is_mini:
                entities.append(AeraFragranceQrImage(coordinator, dsn))
        async_add_entities(entities)

    _add_entities()
    coordinator.register_new_device_callback(_add_entities)


def _generate_qr_png(data: str) -> bytes:
    """Generate a QR code PNG image in memory."""
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


class AeraFragranceQrImage(CoordinatorEntity[AeraCoordinator], ImageEntity):
    """Image entity showing a QR code for the fragrance link."""

    _attr_has_entity_name = True
    _attr_name = "Fragrance QR code"
    _attr_content_type = "image/png"

    def __init__(self, coordinator: AeraCoordinator, dsn: str) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, coordinator.hass)
        self._dsn = dsn
        self._attr_unique_id = f"{dsn}_fragrance_qr"
        self._attr_image_last_updated = datetime.now(tz=timezone.utc)
        self._qr_url: str | None = None
        self._qr_bytes: bytes | None = None

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

    def _get_qr_url(self) -> str | None:
        info = self._device.fragrance_info
        if info and info.fragrance_qr:
            return info.fragrance_qr
        return None

    async def async_image(self) -> bytes | None:
        """Return the QR code image bytes."""
        url = self._get_qr_url()
        if not url:
            return None
        if url != self._qr_url:
            self._qr_url = url
            self._qr_bytes = await self.hass.async_add_executor_job(
                _generate_qr_png, url
            )
            self._attr_image_last_updated = datetime.now(tz=timezone.utc)
        return self._qr_bytes
