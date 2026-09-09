"""Tests for the Aera sensor platform."""

from __future__ import annotations

import pytest

from custom_components.aeraforhome.sensor import (
    AeraFragranceNameSensor,
    AeraFragranceRemainingSensor,
    AeraIntensitySensor,
    AeraSessionTimeSensor,
    AeraFragranceCodeSensor,
)

from .conftest import MINI_DEVICE_DATA, make_device_data


class TestFragranceNameSensor:

    def test_unique_id(self, mock_coordinator):
        sensor = AeraFragranceNameSensor(mock_coordinator, "AC000W123456789")
        assert sensor._attr_unique_id == "AC000W123456789_fragrance_name"

    def test_native_value(self, mock_coordinator):
        sensor = AeraFragranceNameSensor(mock_coordinator, "AC000W123456789")
        assert sensor.native_value == "Ocean Mist"


class TestFragranceRemainingSensor:

    def test_unique_id(self, mock_coordinator):
        sensor = AeraFragranceRemainingSensor(mock_coordinator, "AC000W123456789")
        assert sensor._attr_unique_id == "AC000W123456789_fragrance_remaining"

    def test_native_value(self, mock_coordinator):
        sensor = AeraFragranceRemainingSensor(mock_coordinator, "AC000W123456789")
        assert sensor.native_value == 70

    def test_unit(self, mock_coordinator):
        sensor = AeraFragranceRemainingSensor(mock_coordinator, "AC000W123456789")
        assert sensor._attr_native_unit_of_measurement == "%"


class TestIntensitySensor:

    def test_unique_id(self, mock_coordinator):
        sensor = AeraIntensitySensor(mock_coordinator, "AC000W123456789")
        assert sensor._attr_unique_id == "AC000W123456789_intensity"

    def test_native_value(self, mock_coordinator):
        sensor = AeraIntensitySensor(mock_coordinator, "AC000W123456789")
        assert sensor.native_value == 5

    def test_extra_state_attributes(self, mock_coordinator):
        sensor = AeraIntensitySensor(mock_coordinator, "AC000W123456789")
        attrs = sensor.extra_state_attributes
        assert attrs == {"max_intensity": 10}


class TestSessionTimeSensor:

    def test_unique_id(self, mock_coordinator):
        sensor = AeraSessionTimeSensor(mock_coordinator, "AC000W123456789")
        assert sensor._attr_unique_id == "AC000W123456789_session_time_remaining"

    def test_native_value_inactive(self, mock_coordinator):
        sensor = AeraSessionTimeSensor(mock_coordinator, "AC000W123456789")
        assert sensor.native_value is None

    def test_native_value_active(self, mock_coordinator):
        dev = mock_coordinator.data["AC000W123456789"].device
        dev.update_properties({"session_state": 1, "session_time_left": 25})
        sensor = AeraSessionTimeSensor(mock_coordinator, "AC000W123456789")
        assert sensor.native_value == 25


class TestFragranceCodeSensor:

    def test_native_value_with_info(self, mock_coordinator):
        mock_coordinator.data["AC000W999888777"] = make_device_data(
            data=MINI_DEVICE_DATA, schedules=[]
        )
        sensor = AeraFragranceCodeSensor(mock_coordinator, "AC000W999888777")
        assert sensor.native_value == "OM001"

    def test_native_value_no_info(self, mock_coordinator):
        mock_coordinator.data["AC000W999888777"] = make_device_data(
            data=MINI_DEVICE_DATA, schedules=[]
        )
        mock_coordinator.data["AC000W999888777"].device.fragrance_info = None
        sensor = AeraFragranceCodeSensor(mock_coordinator, "AC000W999888777")
        assert sensor.native_value is None
