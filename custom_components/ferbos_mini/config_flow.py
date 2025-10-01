from __future__ import annotations
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, CONF_ADDON_BASE_URL, CONF_API_KEY, DEFAULT_ADDON_BASE_URL
import voluptuous as vol


class FerbosConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            # Do not enforce connectivity; allow setup even if no bridge is running.
            # The URL/token are still stored for optional features (e.g., UI add),
            # but core query/config features now run locally in the integration.
            return self.async_create_entry(title="Ferbos Mini", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(CONF_ADDON_BASE_URL, default=DEFAULT_ADDON_BASE_URL): str,
                vol.Optional(CONF_API_KEY, default=""): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


