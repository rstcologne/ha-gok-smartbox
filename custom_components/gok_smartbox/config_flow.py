"""Config flow for GOK SmartBox."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import GokApiError, GokDeviceNotFound, GokSmartboxApi
from .const import (
    CONF_DEVICE_ID,
    CONF_INTERVAL,
    DEFAULT_INTERVAL,
    DOMAIN,
    INTERVALS,
    parse_device_id,
)


class GokSmartboxConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            device_id = parse_device_id(user_input[CONF_DEVICE_ID])
            if device_id is None:
                errors[CONF_DEVICE_ID] = "invalid_device_id"
            else:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()
                try:
                    await GokSmartboxApi(
                        async_get_clientsession(self.hass), device_id
                    ).async_get_data()
                except GokDeviceNotFound:
                    errors[CONF_DEVICE_ID] = "device_not_found"
                except GokApiError:
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title=f"SmartBox {device_id}",
                        data={
                            CONF_DEVICE_ID: device_id,
                            CONF_INTERVAL: user_input[CONF_INTERVAL],
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID): str,
                vol.Required(CONF_INTERVAL, default=DEFAULT_INTERVAL): SelectSelector(
                    SelectSelectorConfig(
                        options=list(INTERVALS),
                        translation_key=CONF_INTERVAL,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )
