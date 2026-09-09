"""Shared fixtures for Aera for Home HA integration tests."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Patch ConfigFlowResult if not present in this HA version
from homeassistant import config_entries as _ce
if not hasattr(_ce, "ConfigFlowResult"):
    from homeassistant.data_entry_flow import FlowResult
    _ce.ConfigFlowResult = FlowResult

# Patch FanEntityFeature.TURN_ON/TURN_OFF if not present in this HA version
from homeassistant.components.fan import FanEntityFeature as _FEF
if not hasattr(_FEF, "TURN_ON"):
    _FEF._value2member_map_[8] = _FEF.SET_SPEED
    _FEF.TURN_ON = _FEF(8)
    _FEF.TURN_OFF = _FEF(16)

from aera.device import AeraDevice, DeviceType
from aera.contentful import FragranceInfo

from homeassistant.core import HomeAssistant

from custom_components.aeraforhome.const import DOMAIN
from custom_components.aeraforhome.coordinator import AeraCoordinator, AeraDeviceData, AeraScheduleSlot


MOCK_EMAIL = "test@example.com"
MOCK_PASSWORD = "password123"

DEVICE_DATA: dict[str, Any] = {
    "dsn": "AC000W123456789",
    "key": 12345,
    "product_name": "Aera 3.0",
    "device_name": "Living Room",
    "oem_model": "aera3",
    "model": "AY001MUS1",
    "sw_version": "2.5.0",
    "mac": "00:11:22:33:44:55",
    "lan_ip": "192.168.1.100",
    "connected_at": "2024-01-01T00:00:00Z",
    "connection_status": "Online",
}

MINI_DEVICE_DATA: dict[str, Any] = {
    "dsn": "AC000W999888777",
    "key": 99999,
    "product_name": "Aera Mini",
    "device_name": "Bedroom",
    "oem_model": "aeraMini",
    "model": "AY001MINI",
    "sw_version": "1.0.0",
    "mac": "AA:BB:CC:DD:EE:FF",
    "lan_ip": "192.168.1.101",
    "connected_at": "2024-06-01T00:00:00Z",
    "connection_status": "Online",
}

SAMPLE_PROPERTIES: dict[str, Any] = {
    "power_state": 1,
    "intensity_state": 5,
    "cartridge_usage": 30,
    "cartridge_present": 1,
    "fragrance_name": "Ocean Mist",
    "error_condition": 0,
    "session_state": 0,
    "session_time_left": 0,
    "set_fragrance_identifier": "Ocean Mist",
    "device_fw_version": "2.5.0",
}

SAMPLE_FRAGRANCE = FragranceInfo(
    fragrance_id="OM001",
    fragrance_qr="QR-OM001",
    fragrance_name="Ocean Mist",
    firmware_name="ocean_mist",
    color="#3A7BD5",
    mini_fill=8.0,
    mini_output=0.05,
)

SAMPLE_SCHEDULE_SLOT = AeraScheduleSlot(
    schedule_key=100,
    slot_name="Morning",
    active=True,
    start_time="08:00:00",
    end_time="12:00:00",
    days_of_week=[2, 3, 4, 5, 6, 7, 1],
    intensity=5,
    action_key=200,
)


def make_device(data: dict[str, Any] | None = None, properties: dict[str, Any] | None = None) -> AeraDevice:
    """Create an AeraDevice with optional properties."""
    dev = AeraDevice(
        dict(data or DEVICE_DATA),
        properties=dict(properties or SAMPLE_PROPERTIES),
    )
    dev.fragrance_info = SAMPLE_FRAGRANCE
    return dev


def make_device_data(
    data: dict[str, Any] = DEVICE_DATA,
    properties: dict[str, Any] | None = None,
    schedules: list[AeraScheduleSlot] | None = None,
) -> AeraDeviceData:
    """Create an AeraDeviceData with defaults."""
    return AeraDeviceData(
        device=make_device(data, properties),
        schedules=schedules if schedules is not None else [SAMPLE_SCHEDULE_SLOT],
    )


@pytest.fixture
def mock_api() -> AsyncMock:
    """Create a mock AeraApi."""
    api = AsyncMock()
    api.login = AsyncMock(return_value=True)
    api.get_devices = AsyncMock(return_value=[make_device()])
    api.get_device_properties = AsyncMock(return_value=SAMPLE_PROPERTIES)
    api.set_power = AsyncMock(return_value=True)
    api.set_intensity = AsyncMock(return_value=True)
    api.start_session = AsyncMock(return_value=True)
    api.stop_session = AsyncMock(return_value=True)
    api.set_property = AsyncMock(return_value=True)
    api.get_schedules = AsyncMock(return_value=[])
    api.get_schedule_actions = AsyncMock(return_value=[])
    api.update_schedule = AsyncMock(return_value={})
    api.create_schedule_action = AsyncMock(return_value={})
    api.update_schedule_action = AsyncMock(return_value={})
    api.delete_schedule_action = AsyncMock(return_value=True)
    api.close = AsyncMock()
    return api


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MagicMock:
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "email": MOCK_EMAIL,
        "password": MOCK_PASSWORD,
    }
    return entry


@pytest.fixture
def coordinator_data() -> dict[str, AeraDeviceData]:
    """Default coordinator data with one full-size device."""
    return {"AC000W123456789": make_device_data()}


@pytest.fixture
def coordinator_data_with_mini() -> dict[str, AeraDeviceData]:
    """Coordinator data with both full-size and mini devices."""
    return {
        "AC000W123456789": make_device_data(),
        "AC000W999888777": make_device_data(
            data=MINI_DEVICE_DATA,
            schedules=[],
        ),
    }


@pytest.fixture
def mock_coordinator(hass: HomeAssistant, mock_api, coordinator_data) -> AeraCoordinator:
    """Create a mock coordinator with data pre-populated."""
    coordinator = AeraCoordinator(hass, mock_api)
    coordinator.data = coordinator_data
    coordinator.config_entry_id = "test_entry_id"
    coordinator.known_dsns = set(coordinator_data.keys())
    return coordinator
