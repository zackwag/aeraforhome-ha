"""Tests for the Aera time platform."""

from __future__ import annotations

from datetime import time as dt_time

from unittest.mock import AsyncMock

import pytest

from custom_components.aeraforhome.time import (
    _parse_time,
    AeraScheduleStartTime,
    AeraScheduleEndTime,
)


class TestParseTime:

    def test_hms(self):
        assert _parse_time("08:30:00") == dt_time(8, 30, 0)

    def test_hm_only(self):
        assert _parse_time("14:15") == dt_time(14, 15, 0)

    def test_midnight(self):
        assert _parse_time("00:00:00") == dt_time(0, 0, 0)


class TestScheduleStartTime:

    def test_unique_id(self, mock_coordinator):
        entity = AeraScheduleStartTime(mock_coordinator, "AC000W123456789", 0)
        assert entity._attr_unique_id == "AC000W123456789_schedule_100_start"

    def test_native_value(self, mock_coordinator):
        entity = AeraScheduleStartTime(mock_coordinator, "AC000W123456789", 0)
        assert entity.native_value == dt_time(8, 0, 0)

    async def test_set_value(self, mock_coordinator):
        entity = AeraScheduleStartTime(mock_coordinator, "AC000W123456789", 0)
        entity.hass = mock_coordinator.hass
        entity.async_write_ha_state = lambda: None
        mock_coordinator.async_request_refresh = AsyncMock()
        await entity.async_set_value(dt_time(9, 30, 0))
        mock_coordinator.api.update_schedule.assert_called_once_with(
            "AC000W123456789", 100, {"start_time_each_day": "09:30:00"}
        )


class TestScheduleEndTime:

    def test_unique_id(self, mock_coordinator):
        entity = AeraScheduleEndTime(mock_coordinator, "AC000W123456789", 0)
        assert entity._attr_unique_id == "AC000W123456789_schedule_100_end"

    def test_native_value(self, mock_coordinator):
        entity = AeraScheduleEndTime(mock_coordinator, "AC000W123456789", 0)
        assert entity.native_value == dt_time(12, 0, 0)

    async def test_set_value(self, mock_coordinator):
        entity = AeraScheduleEndTime(mock_coordinator, "AC000W123456789", 0)
        entity.hass = mock_coordinator.hass
        entity.async_write_ha_state = lambda: None
        mock_coordinator.async_request_refresh = AsyncMock()
        await entity.async_set_value(dt_time(18, 0, 0))
        mock_coordinator.api.update_schedule.assert_called_once_with(
            "AC000W123456789", 100, {"end_time_each_day": "18:00:00"}
        )
