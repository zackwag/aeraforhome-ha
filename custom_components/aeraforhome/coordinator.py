"""Data update coordinator for Aera for Home."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from aera import AeraApi, AeraDevice
from aera.api import AeraAuthError, AeraApiError

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL_SECONDS, SCHEDULE_POLL_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


@dataclass
class AeraScheduleSlot:
    """Represents a single schedule slot with its action."""

    schedule_key: int
    slot_name: str
    active: bool = False
    start_time: str = "00:00:00"
    end_time: str = "00:00:00"
    days_of_week: list[int] = field(default_factory=list)
    intensity: int = 5
    action_key: int | None = None


@dataclass
class AeraDeviceData:
    """All data for one Aera device."""

    device: AeraDevice
    schedules: list[AeraScheduleSlot] = field(default_factory=list)


class AeraCoordinator(DataUpdateCoordinator[dict[str, AeraDeviceData]]):
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
        self._known_schedule_keys: set[int] = set()
        self._last_schedule_fetch: float = 0.0
        self._cached_schedules: dict[str, list[AeraScheduleSlot]] = {}
        self.new_device_callbacks: list[callback] = []
        self.schedule_change_callbacks: list[callback] = []
        self.config_entry_id: str | None = None

    def register_new_device_callback(self, cb: callback) -> None:
        """Register a callback to be called when new devices are discovered."""
        self.new_device_callbacks.append(cb)

    def register_schedule_change_callback(self, cb: callback) -> None:
        """Register a callback for when schedules are added or removed."""
        self.schedule_change_callbacks.append(cb)

    def force_schedule_refresh(self) -> None:
        """Force schedules to be re-fetched on next poll."""
        self._last_schedule_fetch = 0.0

    async def _async_update_data(self) -> dict[str, AeraDeviceData]:
        try:
            devices = await self.api.get_devices()
            for device in devices:
                await self.api.get_device_properties(device)

            now = time.monotonic()
            should_fetch_schedules = (
                now - self._last_schedule_fetch >= SCHEDULE_POLL_INTERVAL_SECONDS
            )

            result: dict[str, AeraDeviceData] = {}
            for device in devices:
                if should_fetch_schedules:
                    schedules = await self._fetch_schedules(device)
                    self._cached_schedules[device.dsn] = schedules
                else:
                    schedules = self._cached_schedules.get(device.dsn, [])
                result[device.dsn] = AeraDeviceData(device=device, schedules=schedules)

            if should_fetch_schedules:
                self._last_schedule_fetch = now

            new_dsns = set(result.keys()) - self.known_dsns
            if self.known_dsns and new_dsns:
                _LOGGER.debug("New Aera devices discovered: %s", new_dsns)
                for cb in self.new_device_callbacks:
                    cb(new_dsns)
            self.known_dsns = set(result.keys())

            current_schedule_keys = {
                slot.schedule_key
                for data in result.values()
                for slot in data.schedules
            }
            if should_fetch_schedules:
                self._cleanup_orphaned_schedule_entities(current_schedule_keys)
            if self._known_schedule_keys and current_schedule_keys != self._known_schedule_keys:
                for cb in self.schedule_change_callbacks:
                    cb()
            self._known_schedule_keys = current_schedule_keys

            return result
        except AeraAuthError as err:
            raise ConfigEntryAuthFailed from err
        except AeraApiError as err:
            raise UpdateFailed(f"Error communicating with Aera API: {err}") from err

    def _cleanup_orphaned_schedule_entities(self, current_keys: set[int]) -> None:
        """Remove schedule entities that have no matching schedule."""
        if not self.config_entry_id:
            return
        ent_reg = er.async_get(self.hass)
        entries = er.async_entries_for_config_entry(ent_reg, self.config_entry_id)
        for entry in entries:
            if "_schedule_" not in entry.unique_id:
                continue
            if not any(f"_schedule_{key}" in entry.unique_id for key in current_keys):
                _LOGGER.debug("Removing orphaned schedule entity %s", entry.entity_id)
                ent_reg.async_remove(entry.entity_id)

    async def _fetch_schedules(self, device: AeraDevice) -> list[AeraScheduleSlot]:
        """Fetch configured schedules and their actions for a device."""
        slots: list[AeraScheduleSlot] = []
        try:
            raw_schedules = await self.api.get_schedules(device)
        except AeraApiError:
            _LOGGER.debug("Failed to fetch schedules for %s", device.dsn)
            return slots

        for sched in raw_schedules:
            actions = []
            try:
                actions = await self.api.get_schedule_actions(sched["key"])
            except AeraApiError:
                pass

            is_active = sched.get("active", False)
            has_actions = any(
                a.get("name") == "set_intensity_sched" and a.get("active", False)
                for a in actions
            )
            if not is_active and not has_actions:
                continue

            slot = AeraScheduleSlot(
                schedule_key=sched["key"],
                slot_name=sched.get("display_name") or sched.get("name", ""),
                active=is_active,
                start_time=sched.get("start_time_each_day", "00:00:00"),
                end_time=sched.get("end_time_each_day", "00:00:00"),
                days_of_week=sched.get("days_of_week", []),
            )
            for action in actions:
                if action.get("name") == "set_intensity_sched" and action.get("active"):
                    slot.intensity = int(action.get("value", 5))
                    slot.action_key = action.get("key")
                    break
            slots.append(slot)
        return slots

    async def async_create_schedule(
        self,
        dsn: str,
        start_time: str,
        end_time: str,
        days_of_week: list[int],
        intensity: int,
    ) -> None:
        """Create a schedule by activating the next available slot."""
        device = self.data[dsn].device
        all_schedules = await self.api.get_schedules(device)
        inactive = [s for s in all_schedules if not s.get("active")]
        if not inactive:
            raise AeraApiError("No available schedule slots (all 20 are active)")

        slot = inactive[0]
        schedule_key = slot["key"]

        await self.api.update_schedule(dsn, schedule_key, {
            "active": True,
            "start_time_each_day": start_time,
            "end_time_each_day": end_time,
            "days_of_week": days_of_week,
        })
        await self.api.create_schedule_action(schedule_key, {
            "name": "set_intensity_sched",
            "value": str(intensity),
            "base_type": "integer",
            "active": True,
            "at_start": True,
            "at_end": False,
            "in_range": False,
        })
        self.force_schedule_refresh()
        await self.async_request_refresh()

    async def async_delete_schedule(self, dsn: str, schedule_key: int) -> None:
        """Delete a schedule by deactivating it."""
        await self.api.update_schedule(dsn, schedule_key, {"active": False})
        self.force_schedule_refresh()
        await self.async_request_refresh()
