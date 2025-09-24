from __future__ import annotations
from homeassistant.core import HomeAssistant
from homeassistant.components import websocket_api
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
import os
import asyncio
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

    # WebSocket: ferbos/addons/install → add custom repository and install add-on via Supervisor API
    @websocket_api.websocket_command({
        "type": "ferbos/addons/install",
        "id": int,
        vol.Required("args"): dict,
    })
    @websocket_api.async_response
    async def ws_ferbos_addons_install(hass, connection, msg):
        args = msg.get("args") or {}
        repository = args.get("repository") or args.get("repo")
        addon_slug = args.get("addon_slug") or args.get("slug")
        wait = bool(args.get("wait", True))

        if not repository or not addon_slug:
            connection.send_result(msg["id"], {"error": "repository and addon_slug are required", "status_code": 400})
            return

        sup_token = os.getenv("SUPERVISOR_TOKEN", "")
        if not sup_token:
            connection.send_result(msg["id"], {"error": "Supervisor token not available (requires HA OS/Supervised).", "status_code": 400})
            return

        headers = {"Authorization": f"Bearer {sup_token}", "X-Supervisor-Token": sup_token}
        async with aiohttp.ClientSession() as session:
            # 1) Add repo
            try:
                r = await session.post("http://supervisor/store/repositories", headers=headers, json={"repository": repository})
                body = await r.text()
                if r.status not in (200, 201):
                    connection.send_result(msg["id"], {"error": "Failed to add repository", "status": r.status, "body": body})
                    return
            except Exception as e:
                connection.send_result(msg["id"], {"error": f"Repo add error: {e}"})
                return

            # 2) Install addon
            try:
                r2 = await session.post(f"http://supervisor/addons/{addon_slug}/install", headers=headers)
                body2 = await r2.text()
                if r2.status not in (200, 201):
                    connection.send_result(msg["id"], {"error": "Failed to start install", "status": r2.status, "body": body2})
                    return
            except Exception as e:
                connection.send_result(msg["id"], {"error": f"Install error: {e}"})
                return

            result = {"ok": True, "repository_added": repository, "addon_install_started": addon_slug}
            if wait:
                # poll until installed/started or timeout
                try:
                    deadline = hass.loop.time() + 300
                    info_url = f"http://supervisor/addons/{addon_slug}/info"
                    while hass.loop.time() < deadline:
                        gi = await session.get(info_url, headers=headers)
                        payload = await gi.json(content_type=None)
                        state = payload.get("data", {}).get("state") or payload.get("state")
                        if state in ("installed", "started", "running"):
                            result["state"] = state
                            break
                        await asyncio.sleep(2)
                except Exception:
                    pass

            connection.send_result(msg["id"], result)

    websocket_api.async_register_command(hass, ws_ferbos_addons_install)

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

    # WebSocket: ferbos/addons/install (config entry)
    @websocket_api.websocket_command({
        "type": "ferbos/addons/install",
        "id": int,
        vol.Required("args"): dict,
    })
    @websocket_api.async_response
    async def ws_ferbos_addons_install(hass, connection, msg):
        args = msg.get("args") or {}
        repository = args.get("repository") or args.get("repo")
        addon_slug = args.get("addon_slug") or args.get("slug")
        wait = bool(args.get("wait", True))

        sup_token = os.getenv("SUPERVISOR_TOKEN", "")
        if not repository or not addon_slug:
            connection.send_result(msg["id"], {"error": "repository and addon_slug are required", "status_code": 400})
            return
        if not sup_token:
            connection.send_result(msg["id"], {"error": "Supervisor token not available (requires HA OS/Supervised).", "status_code": 400})
            return

        headers = {"Authorization": f"Bearer {sup_token}", "X-Supervisor-Token": sup_token}
        async with aiohttp.ClientSession() as session:
            try:
                r = await session.post("http://supervisor/store/repositories", headers=headers, json={"repository": repository})
                _ = await r.text()
                if r.status not in (200, 201):
                    connection.send_result(msg["id"], {"error": "Failed to add repository", "status": r.status})
                    return
            except Exception as e:
                connection.send_result(msg["id"], {"error": f"Repo add error: {e}"})
                return

            try:
                r2 = await session.post(f"http://supervisor/addons/{addon_slug}/install", headers=headers)
                _ = await r2.text()
                if r2.status not in (200, 201):
                    connection.send_result(msg["id"], {"error": "Failed to start install", "status": r2.status})
                    return
            except Exception as e:
                connection.send_result(msg["id"], {"error": f"Install error: {e}"})
                return

            result = {"ok": True, "repository_added": repository, "addon_install_started": addon_slug}
            if wait:
                try:
                    deadline = hass.loop.time() + 300
                    info_url = f"http://supervisor/addons/{addon_slug}/info"
                    while hass.loop.time() < deadline:
                        gi = await session.get(info_url, headers=headers)
                        pj = await gi.json(content_type=None)
                        state = pj.get("data", {}).get("state") or pj.get("state")
                        if state in ("installed", "started", "running"):
                            result["state"] = state
                            break
                        await asyncio.sleep(2)
                except Exception:
                    pass
            connection.send_result(msg["id"], result)

    websocket_api.async_register_command(hass, ws_ferbos_addons_install)
    return True


