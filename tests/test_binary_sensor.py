"""Tests for the Aera binary sensor platform."""

from __future__ import annotations

import pytest

from custom_components.aeraforhome.binary_sensor import (
    AeraConnectivitySensor,
    AeraCartridgePresentSensor,
    AeraDeviceProblemSensor,
    AeraSessionActiveSensor,
)

from .conftest import DEVICE_DATA, make_device_data


class TestConnectivitySensor:

    def test_unique_id(self, mock_coordinator):
        sensor = AeraConnectivitySensor(mock_coordinator, "AC000W123456789")
        assert sensor._attr_unique_id == "AC000W123456789_connectivity"

    def test_is_on_online(self, mock_coordinator):
        sensor = AeraConnectivitySensor(mock_coordinator, "AC000W123456789")
        assert sensor.is_on is True

    def test_is_on_offline(self, mock_coordinator):
        mock_coordinator.data["AC000W123456789"].device._data["connection_status"] = "Offline"
        sensor = AeraConnectivitySensor(mock_coordinator, "AC000W123456789")
        assert sensor.is_on is False


class TestCartridgePresentSensor:

    def test_unique_id(self, mock_coordinator):
        sensor = AeraCartridgePresentSensor(mock_coordinator, "AC000W123456789")
        assert sensor._attr_unique_id == "AC000W123456789_cartridge_present"

    def test_is_on_present(self, mock_coordinator):
        sensor = AeraCartridgePresentSensor(mock_coordinator, "AC000W123456789")
        assert sensor.is_on is True

    def test_is_on_absent(self, mock_coordinator):
        mock_coordinator.data["AC000W123456789"].device.update_properties({"cartridge_present": 0})
        sensor = AeraCartridgePresentSensor(mock_coordinator, "AC000W123456789")
        assert sensor.is_on is False


class TestDeviceProblemSensor:

    def test_unique_id(self, mock_coordinator):
        sensor = AeraDeviceProblemSensor(mock_coordinator, "AC000W123456789")
        assert sensor._attr_unique_id == "AC000W123456789_problem"

    def test_no_error(self, mock_coordinator):
        sensor = AeraDeviceProblemSensor(mock_coordinator, "AC000W123456789")
        assert sensor.is_on is False
        assert sensor.extra_state_attributes is None

    def test_with_error(self, mock_coordinator):
        mock_coordinator.data["AC000W123456789"].device.update_properties({"error_condition": 3})
        sensor = AeraDeviceProblemSensor(mock_coordinator, "AC000W123456789")
        assert sensor.is_on is True
        assert sensor.extra_state_attributes == {"error_code": 3}


class TestSessionActiveSensor:

    def test_unique_id(self, mock_coordinator):
        sensor = AeraSessionActiveSensor(mock_coordinator, "AC000W123456789")
        assert sensor._attr_unique_id == "AC000W123456789_session_active"

    def test_inactive(self, mock_coordinator):
        sensor = AeraSessionActiveSensor(mock_coordinator, "AC000W123456789")
        assert sensor.is_on is False

    def test_active(self, mock_coordinator):
        mock_coordinator.data["AC000W123456789"].device.update_properties({"session_state": 1})
        sensor = AeraSessionActiveSensor(mock_coordinator, "AC000W123456789")
        assert sensor.is_on is True
