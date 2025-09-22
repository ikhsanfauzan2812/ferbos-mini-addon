from __future__ import annotations
from homeassistant.core import HomeAssistant
from homeassistant.components import websocket_api
from homeassistant.helpers.typing import ConfigType
import aiohttp

from .const import DOMAIN, CONF_ADDON_BASE_URL, CONF_API_KEY, DEFAULT_ADDON_BASE_URL
from .api import FerbosAddonClient


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    conf = config.get(DOMAIN, {})
    addon_base_url = conf.get(CONF_ADDON_BASE_URL, DEFAULT_ADDON_BASE_URL)
    api_key = conf.get(CONF_API_KEY, "")

    client = FerbosAddonClient(addon_base_url, api_key)

    @websocket_api.websocket_command({
        "type": "ferbos/query",
        "id": int,
        "args": dict,
    })
    @websocket_api.async_response
    async def ws_ferbos_query(hass, connection, msg):
        async with aiohttp.ClientSession() as session:
            result = await client.proxy_query(session, msg.get("args", {}))
        connection.send_result(msg["id"], result)

    websocket_api.async_register_command(ws_ferbos_query)
    return True


