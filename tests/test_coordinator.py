"""Tests for the AeraCoordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from aera.api import AeraAuthError, AeraApiError

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.aeraforhome.coordinator import (
    AeraCoordinator,
    AeraDeviceData,
    AeraScheduleSlot,
)

from .conftest import DEVICE_DATA, SAMPLE_PROPERTIES, make_device


class TestCoordinatorUpdate:

    async def test_successful_update(self, hass: HomeAssistant, mock_api):
        coordinator = AeraCoordinator(hass, mock_api)
        mock_api.get_schedules.return_value = []
        data = await coordinator._async_update_data()
        assert "AC000W123456789" in data
        mock_api.get_devices.assert_called_once()
        mock_api.get_device_properties.assert_called_once()

    async def test_auth_error_raises_config_entry_auth_failed(self, hass, mock_api):
        coordinator = AeraCoordinator(hass, mock_api)
        mock_api.get_devices.side_effect = AeraAuthError("expired")
        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    async def test_api_error_raises_update_failed(self, hass, mock_api):
        coordinator = AeraCoordinator(hass, mock_api)
        mock_api.get_devices.side_effect = AeraApiError("timeout")
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


class TestCoordinatorSchedules:

    async def test_fetch_schedules_active_only(self, hass, mock_api):
        mock_api.get_schedules.return_value = [
            {"key": 1, "active": True, "display_name": "Morning", "start_time_each_day": "08:00:00", "end_time_each_day": "12:00:00", "days_of_week": [2, 3, 4, 5, 6]},
            {"key": 2, "active": False, "display_name": "Night"},
        ]
        mock_api.get_schedule_actions.return_value = [
            {"name": "set_intensity_sched", "active": True, "value": "7", "key": 10},
        ]
        coordinator = AeraCoordinator(hass, mock_api)
        device = make_device()
        slots = await coordinator._fetch_schedules(device)
        assert len(slots) == 1
        assert slots[0].schedule_key == 1
        assert slots[0].intensity == 7
        assert slots[0].action_key == 10

    async def test_fetch_schedules_api_error_returns_empty(self, hass, mock_api):
        mock_api.get_schedules.side_effect = AeraApiError("fail")
        coordinator = AeraCoordinator(hass, mock_api)
        device = make_device()
        slots = await coordinator._fetch_schedules(device)
        assert slots == []


class TestCoordinatorForceRefresh:

    def test_force_schedule_refresh(self, hass, mock_api):
        coordinator = AeraCoordinator(hass, mock_api)
        coordinator._last_schedule_fetch = 99999.0
        coordinator.force_schedule_refresh()
        assert coordinator._last_schedule_fetch == 0.0


class TestCoordinatorCallbacks:

    def test_register_new_device_callback(self, hass, mock_api):
        coordinator = AeraCoordinator(hass, mock_api)
        cb = lambda dsns: None
        coordinator.register_new_device_callback(cb)
        assert cb in coordinator.new_device_callbacks

    def test_register_schedule_change_callback(self, hass, mock_api):
        coordinator = AeraCoordinator(hass, mock_api)
        cb = lambda: None
        coordinator.register_schedule_change_callback(cb)
        assert cb in coordinator.schedule_change_callbacks
