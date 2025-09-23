from __future__ import annotations
from homeassistant.core import HomeAssistant
from homeassistant.components import websocket_api
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
import aiohttp

from .const import DOMAIN, CONF_ADDON_BASE_URL, CONF_API_KEY, DEFAULT_ADDON_BASE_URL
from .api import FerbosAddonClient


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    conf = config.get(DOMAIN, {})
    addon_base_url = conf.get(CONF_ADDON_BASE_URL, DEFAULT_ADDON_BASE_URL)
    api_key = conf.get(CONF_API_KEY, "")

    client = FerbosAddonClient(addon_base_url, api_key)

    # Accept both legacy (top-level query/params) and new (args={}) formats
    @websocket_api.websocket_command(
        vol.Schema(
            {
                vol.Required("type"): "ferbos/query",
                vol.Required("id"): int,
                vol.Optional("args"): dict,
                vol.Optional("query"): cv.string,
                vol.Optional("params"): list,
            },
            extra=vol.ALLOW_EXTRA,
        )
    )
    @websocket_api.async_response
    async def ws_ferbos_query(hass, connection, msg):
        # Normalize payload
        args = msg.get("args")
        if args is None:
            args = {
                "query": msg.get("query"),
                "params": msg.get("params") or [],
            }
        async with aiohttp.ClientSession() as session:
            result = await client.proxy_query(session, args)
        connection.send_result(msg["id"], result)

    websocket_api.async_register_command(hass, ws_ferbos_query)
    return True


