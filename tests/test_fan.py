"""Tests for the Aera fan platform."""

from __future__ import annotations

import math

import pytest

from custom_components.aeraforhome.fan import AeraFanEntity
from custom_components.aeraforhome.coordinator import AeraCoordinator

from .conftest import DEVICE_DATA, SAMPLE_PROPERTIES, make_device


class TestFanEntity:

    def test_unique_id(self, mock_coordinator):
        fan = AeraFanEntity(mock_coordinator, "AC000W123456789")
        assert fan._attr_unique_id == "AC000W123456789"

    def test_is_on(self, mock_coordinator):
        fan = AeraFanEntity(mock_coordinator, "AC000W123456789")
        assert fan.is_on is True

    def test_is_off(self, mock_coordinator):
        mock_coordinator.data["AC000W123456789"].device.update_properties({"power_state": 0})
        fan = AeraFanEntity(mock_coordinator, "AC000W123456789")
        assert fan.is_on is False

    def test_percentage(self, mock_coordinator):
        fan = AeraFanEntity(mock_coordinator, "AC000W123456789")
        expected = math.ceil(5 * 100 / 10)
        assert fan.percentage == expected

    def test_percentage_none(self, mock_coordinator):
        mock_coordinator.data["AC000W123456789"].device._properties.pop("intensity_state", None)
        fan = AeraFanEntity(mock_coordinator, "AC000W123456789")
        assert fan.percentage is None

    def test_speed_count(self, mock_coordinator):
        fan = AeraFanEntity(mock_coordinator, "AC000W123456789")
        assert fan.speed_count == 10

    def test_device_info(self, mock_coordinator):
        fan = AeraFanEntity(mock_coordinator, "AC000W123456789")
        info = fan.device_info
        assert ("aeraforhome", "AC000W123456789") in info["identifiers"]
        assert info["manufacturer"] == "Aera"

    async def test_turn_on(self, mock_coordinator):
        fan = AeraFanEntity(mock_coordinator, "AC000W123456789")
        fan.hass = mock_coordinator.hass
        fan.async_write_ha_state = lambda: None
        await fan.async_turn_on()
        mock_coordinator.api.set_power.assert_called_once_with("AC000W123456789", True)

    async def test_turn_on_with_percentage(self, mock_coordinator):
        fan = AeraFanEntity(mock_coordinator, "AC000W123456789")
        fan.hass = mock_coordinator.hass
        fan.async_write_ha_state = lambda: None
        await fan.async_turn_on(percentage=70)
        mock_coordinator.api.set_power.assert_called_once()
        mock_coordinator.api.set_intensity.assert_called_once()

    async def test_turn_off(self, mock_coordinator):
        fan = AeraFanEntity(mock_coordinator, "AC000W123456789")
        fan.hass = mock_coordinator.hass
        fan.async_write_ha_state = lambda: None
        await fan.async_turn_off()
        mock_coordinator.api.set_power.assert_called_once_with("AC000W123456789", False)

    async def test_set_percentage_zero_turns_off(self, mock_coordinator):
        fan = AeraFanEntity(mock_coordinator, "AC000W123456789")
        fan.hass = mock_coordinator.hass
        fan.async_write_ha_state = lambda: None
        await fan.async_set_percentage(0)
        mock_coordinator.api.set_power.assert_called_once_with("AC000W123456789", False)

    async def test_set_percentage_nonzero(self, mock_coordinator):
        fan = AeraFanEntity(mock_coordinator, "AC000W123456789")
        fan.hass = mock_coordinator.hass
        fan.async_write_ha_state = lambda: None
        await fan.async_set_percentage(50)
        mock_coordinator.api.set_intensity.assert_called_once()
        args = mock_coordinator.api.set_intensity.call_args
        level = args[0][1]
        assert 1 <= level <= 10
