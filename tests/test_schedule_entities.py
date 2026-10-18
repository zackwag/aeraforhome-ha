"""Tests for schedule entity tracking shared by the schedule platforms."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.aeraforhome import button, number, select, time
from custom_components.aeraforhome.const import DOMAIN

from .conftest import DEVICE_DATA, SAMPLE_SCHEDULE_SLOT

DSN = DEVICE_DATA["dsn"]


@pytest.mark.parametrize("platform", [button, number, select, time])
async def test_schedule_entities_recreated_when_slot_reused(
    hass: HomeAssistant, mock_coordinator, mock_config_entry, platform
):
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    added = []
    await platform.async_setup_entry(hass, mock_config_entry, added.extend)

    def schedule_entities() -> list:
        return [entity for entity in added if "_schedule_" in entity.unique_id]

    per_slot = len(schedule_entities())
    assert per_slot > 0

    sync = mock_coordinator.schedule_change_callbacks[0]
    mock_coordinator.data[DSN].schedules = []
    sync()
    mock_coordinator.data[DSN].schedules = [SAMPLE_SCHEDULE_SLOT]
    sync()

    assert len(schedule_entities()) == per_slot * 2
