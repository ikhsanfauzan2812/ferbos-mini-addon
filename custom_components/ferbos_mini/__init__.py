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
    # Legacy YAML still supported but optional
    conf = config.get(DOMAIN, {})
    addon_base_url = conf.get(CONF_ADDON_BASE_URL, DEFAULT_ADDON_BASE_URL)
    api_key = conf.get(CONF_API_KEY, "")

    client = FerbosAddonClient(addon_base_url, api_key)

    # Accept both legacy (top-level query/params) and new (args={}) formats
    @websocket_api.websocket_command({
        "type": "ferbos/query",
        "id": int,
        vol.Optional("args"): dict,
        vol.Optional("query"): cv.string,
        vol.Optional("params"): list,
    })
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

    # WebSocket: ferbos/config/add → append lines to configuration.yaml via addon /ha_config/append_lines
    @websocket_api.websocket_command({
        "type": "ferbos/config/add",
        "id": int,
        vol.Optional("args"): dict,
        vol.Optional("lines"): list,
        vol.Optional("validate"): bool,
        vol.Optional("reload_core"): bool,
        vol.Optional("backup"): bool,
    })
    @websocket_api.async_response
    async def ws_ferbos_config_add(hass, connection, msg):
        args = msg.get("args") or {}
        # Support flattened payload from old bridge
        if not args and ("lines" in msg or "validate" in msg or "reload_core" in msg or "backup" in msg):
            args = {
                "lines": msg.get("lines"),
                "validate": msg.get("validate", True),
                "reload_core": msg.get("reload_core", True),
                "backup": msg.get("backup", True),
            }
        payload = {
            "lines": args.get("lines") or [],
            "validate": args.get("validate", True),
            "reload_core": args.get("reload_core", True),
            "backup": args.get("backup", True),
        }
        # POST to addon /ha_config/append_lines
        async with aiohttp.ClientSession() as session:
            url = f"{addon_base_url.rstrip('/')}/ha_config/append_lines"
            async with session.post(url, json=payload) as resp:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    data = {"status": resp.status, "text": await resp.text()}
        connection.send_result(msg["id"], data)

    websocket_api.async_register_command(hass, ws_ferbos_config_add)

    # WebSocket: ferbos/ui/add → proxy to addon ws_bridge with method ferbos/ui/add
    @websocket_api.websocket_command({
        "type": "ferbos/ui/add",
        "id": int,
        vol.Optional("args"): dict,
        vol.Optional("template"): cv.string,
        vol.Optional("lines"): list,
        vol.Optional("path"): cv.string,
        vol.Optional("backup"): bool,
        vol.Optional("overwrite"): bool,
    })
    @websocket_api.async_response
    async def ws_ferbos_ui_add(hass, connection, msg):
        args = msg.get("args") or {}
        # Accept flattened fields for convenience
        for key in ("template", "lines", "path", "backup", "overwrite"):
            if key in msg and key not in args:
                args[key] = msg[key]
        payload = {"method": "ferbos/ui/add", "args": args}
        if api_key:
            payload["token"] = api_key
        async with aiohttp.ClientSession() as session:
            url = f"{addon_base_url.rstrip('/')}/ws_bridge"
            async with session.post(url, json=payload) as resp:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    data = {"status": resp.status, "text": await resp.text()}
        connection.send_result(msg["id"], data)

    websocket_api.async_register_command(hass, ws_ferbos_ui_add)

    @websocket_api.websocket_command({
        "type": "ferbos/ui/add",
        "id": int,
        vol.Optional("args"): dict,
        vol.Optional("template"): cv.string,
        vol.Optional("lines"): list,
        vol.Optional("path"): cv.string,
        vol.Optional("backup"): bool,
        vol.Optional("overwrite"): bool,
    })
    @websocket_api.async_response
    async def ws_ferbos_ui_add(hass, connection, msg):
        args = msg.get("args") or {}
        for key in ("template", "lines", "path", "backup", "overwrite"):
            if key in msg and key not in args:
                args[key] = msg[key]
        payload = {"method": "ferbos/ui/add", "args": args}
        if api_key:
            payload["token"] = api_key
        async with aiohttp.ClientSession() as session:
            url = f"{addon_base_url.rstrip('/')}/ws_bridge"
            async with session.post(url, json=payload) as resp:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    data = {"status": resp.status, "text": await resp.text()}
        connection.send_result(msg["id"], data)

    websocket_api.async_register_command(hass, ws_ferbos_ui_add)
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    data = entry.data or {}
    addon_base_url = data.get(CONF_ADDON_BASE_URL, DEFAULT_ADDON_BASE_URL)
    api_key = data.get(CONF_API_KEY, "")

    client = FerbosAddonClient(addon_base_url, api_key)

    @websocket_api.websocket_command({
        "type": "ferbos/query",
        "id": int,
        vol.Optional("args"): dict,
        vol.Optional("query"): cv.string,
        vol.Optional("params"): list,
    })
    @websocket_api.async_response
    async def ws_ferbos_query(hass, connection, msg):
        args = msg.get("args") or {"query": msg.get("query"), "params": msg.get("params") or []}
        async with aiohttp.ClientSession() as session:
            result = await client.proxy_query(session, args)
        connection.send_result(msg["id"], result)

    websocket_api.async_register_command(hass, ws_ferbos_query)

    @websocket_api.websocket_command({
        "type": "ferbos/config/add",
        "id": int,
        vol.Optional("args"): dict,
        vol.Optional("lines"): list,
        vol.Optional("validate"): bool,
        vol.Optional("reload_core"): bool,
        vol.Optional("backup"): bool,
    })
    @websocket_api.async_response
    async def ws_ferbos_config_add(hass, connection, msg):
        args = msg.get("args") or {}
        if not args and ("lines" in msg or "validate" in msg or "reload_core" in msg or "backup" in msg):
            args = {
                "lines": msg.get("lines"),
                "validate": msg.get("validate", True),
                "reload_core": msg.get("reload_core", True),
                "backup": msg.get("backup", True),
            }
        payload = {
            "lines": args.get("lines") or [],
            "validate": args.get("validate", True),
            "reload_core": args.get("reload_core", True),
            "backup": args.get("backup", True),
        }
        async with aiohttp.ClientSession() as session:
            url = f"{addon_base_url.rstrip('/')}/ha_config/append_lines"
            async with session.post(url, json=payload) as resp:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    data = {"status": resp.status, "text": await resp.text()}
        connection.send_result(msg["id"], data)

    websocket_api.async_register_command(hass, ws_ferbos_config_add)
    return True


