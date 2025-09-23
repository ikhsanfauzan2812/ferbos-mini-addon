from __future__ import annotations
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, CONF_ADDON_BASE_URL, CONF_API_KEY, DEFAULT_ADDON_BASE_URL
import voluptuous as vol
import aiohttp


class FerbosConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            # Basic ping check to addon if provided
            base = user_input.get(CONF_ADDON_BASE_URL, DEFAULT_ADDON_BASE_URL).rstrip("/")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{base}/ping", timeout=10) as resp:
                        if resp.status != 200:
                            errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(title="Ferbos Mini", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(CONF_ADDON_BASE_URL, default=DEFAULT_ADDON_BASE_URL): str,
                vol.Optional(CONF_API_KEY, default=""): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


