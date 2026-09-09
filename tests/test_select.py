"""Tests for the Aera select platform helpers and entities."""

from __future__ import annotations

import pytest

from custom_components.aeraforhome.select import (
    _days_to_option,
    _option_to_days,
    _minutes_to_option,
    DAYS_EVERY_DAY,
    DAYS_WEEKDAYS,
    DAYS_WEEKENDS,
    SESSION_DURATIONS,
    AeraSessionSelect,
)


class TestDaysHelpers:

    def test_days_to_option_every_day(self):
        assert _days_to_option(DAYS_EVERY_DAY) == "Every day"

    def test_days_to_option_weekdays(self):
        assert _days_to_option(DAYS_WEEKDAYS) == "Weekdays"

    def test_days_to_option_weekends(self):
        assert _days_to_option(DAYS_WEEKENDS) == "Weekends"

    def test_days_to_option_unknown_defaults(self):
        assert _days_to_option([1, 3, 5]) == "Every day"

    def test_days_to_option_unordered(self):
        assert _days_to_option([1, 7, 6, 5, 4, 3, 2]) == "Every day"

    def test_option_to_days_every_day(self):
        assert _option_to_days("Every day") == DAYS_EVERY_DAY

    def test_option_to_days_weekdays(self):
        assert _option_to_days("Weekdays") == DAYS_WEEKDAYS

    def test_option_to_days_weekends(self):
        assert _option_to_days("Weekends") == DAYS_WEEKENDS

    def test_option_to_days_default(self):
        assert _option_to_days("Something else") == DAYS_EVERY_DAY


class TestMinutesToOption:

    def test_zero(self):
        assert _minutes_to_option(0) == "Off"

    def test_none(self):
        assert _minutes_to_option(None) == "Off"

    def test_negative(self):
        assert _minutes_to_option(-5) == "Off"

    def test_2_hours(self):
        assert _minutes_to_option(120) == "2 hours"

    def test_under_2_hours(self):
        assert _minutes_to_option(60) == "2 hours"

    def test_4_hours(self):
        assert _minutes_to_option(240) == "4 hours"

    def test_under_4_hours(self):
        assert _minutes_to_option(180) == "4 hours"

    def test_8_hours(self):
        assert _minutes_to_option(480) == "8 hours"

    def test_over_4_hours(self):
        assert _minutes_to_option(300) == "8 hours"


class TestSessionSelect:

    def test_current_option_off(self, mock_coordinator):
        select = AeraSessionSelect(mock_coordinator, "AC000W123456789")
        assert select.current_option == "Off"

    def test_current_option_active(self, mock_coordinator):
        dev = mock_coordinator.data["AC000W123456789"].device
        dev.update_properties({"session_state": 1, "session_time_left": 120})
        select = AeraSessionSelect(mock_coordinator, "AC000W123456789")
        assert select.current_option == "2 hours"

    async def test_select_off(self, mock_coordinator):
        select = AeraSessionSelect(mock_coordinator, "AC000W123456789")
        select.hass = mock_coordinator.hass
        select.async_write_ha_state = lambda: None
        await select.async_select_option("Off")
        mock_coordinator.api.set_power.assert_called_once_with("AC000W123456789", False)

    async def test_select_duration(self, mock_coordinator):
        select = AeraSessionSelect(mock_coordinator, "AC000W123456789")
        select.hass = mock_coordinator.hass
        select.async_write_ha_state = lambda: None
        await select.async_select_option("4 hours")
        mock_coordinator.api.start_session.assert_called_once_with("AC000W123456789", 240)


class TestSessionDurations:

    def test_all_durations_present(self):
        assert SESSION_DURATIONS["Off"] == 0
        assert SESSION_DURATIONS["2 hours"] == 120
        assert SESSION_DURATIONS["4 hours"] == 240
        assert SESSION_DURATIONS["8 hours"] == 480
