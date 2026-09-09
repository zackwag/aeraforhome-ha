"""Tests for the Aera for Home config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.aeraforhome.const import DOMAIN

from .conftest import MOCK_EMAIL, MOCK_PASSWORD

PATCH_TARGET = "custom_components.aeraforhome.config_flow.AeraApi"

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_user_flow_success(hass: HomeAssistant) -> None:
    """Test successful user config flow."""
    mock_api = AsyncMock()
    mock_api.login = AsyncMock(return_value=True)
    with patch(PATCH_TARGET, return_value=mock_api):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"email": MOCK_EMAIL, "password": MOCK_PASSWORD},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == MOCK_EMAIL
        assert result["data"] == {"email": MOCK_EMAIL, "password": MOCK_PASSWORD}


async def test_user_flow_invalid_auth(hass: HomeAssistant) -> None:
    """Test config flow with bad credentials."""
    from aera.api import AeraAuthError

    mock_api = AsyncMock()
    mock_api.login = AsyncMock(side_effect=AeraAuthError("bad"))
    with patch(PATCH_TARGET, return_value=mock_api):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"email": MOCK_EMAIL, "password": MOCK_PASSWORD},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_unknown_error(hass: HomeAssistant) -> None:
    """Test config flow with unexpected exception."""
    mock_api = AsyncMock()
    mock_api.login = AsyncMock(side_effect=RuntimeError("boom"))
    with patch(PATCH_TARGET, return_value=mock_api):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"email": MOCK_EMAIL, "password": MOCK_PASSWORD},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}
