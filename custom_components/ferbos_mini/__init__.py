from __future__ import annotations
from homeassistant.core import HomeAssistant
from homeassistant.components import websocket_api
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
import aiohttp
import aiosqlite
import asyncio
from pathlib import Path
from datetime import datetime
import shutil

from .const import DOMAIN, CONF_ADDON_BASE_URL, CONF_API_KEY, DEFAULT_ADDON_BASE_URL
from .api import FerbosAddonClient


async def _run_sqlite_query(hass: HomeAssistant, args: dict) -> dict:
    query: str | None = (args or {}).get("query")
    params = (args or {}).get("params") or []
    if not query:
        return {"success": False, "error": {"code": "invalid", "message": "Missing query"}}

    db_path = Path(hass.config.path("home-assistant_v2.db"))
    if not db_path.exists():
        return {"success": False, "error": {"code": "not_found", "message": f"DB not found: {db_path}"}}

    try:
        async with aiosqlite.connect(db_path.as_posix()) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            is_select = query.strip().lower().startswith("select")
            if is_select:
                rows = await cursor.fetchall()
                await cursor.close()
                result = [dict(r) for r in rows]
                return {"success": True, "data": result}
            else:
                await db.commit()
                rowcount = cursor.rowcount
                lastrowid = cursor.lastrowid
                await cursor.close()
                return {"success": True, "data": {"rowcount": rowcount, "lastrowid": lastrowid}}
    except Exception as exc:
        return {"success": False, "error": {"code": "sqlite_error", "message": str(exc)}}


async def _append_config_lines(hass: HomeAssistant, payload: dict) -> dict:
    lines = payload.get("lines") or []
    validate = payload.get("validate", True)
    reload_core = payload.get("reload_core", True)
    backup = payload.get("backup", True)

    if not isinstance(lines, list):
        return {"success": False, "error": {"code": "invalid", "message": "lines must be a list"}}

    config_path = Path(hass.config.path("configuration.yaml"))
    if not config_path.exists():
        return {"success": False, "error": {"code": "not_found", "message": f"configuration.yaml not found at {config_path}"}}

    try:
        if backup:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = config_path.with_suffix(f".backup.{ts}.yaml")
            shutil.copy2(config_path.as_posix(), backup_path.as_posix())

        content_to_append = "\n".join([str(l) for l in lines])
        # Ensure separation by a newline
        with open(config_path, "a", encoding="utf-8") as f:
            if not content_to_append.endswith("\n"):
                content_to_append += "\n"
            f.write(content_to_append)

        if validate:
            await hass.services.async_call("homeassistant", "check_config", blocking=True)
        if reload_core:
            # Reload core configuration (area registry, customize, packages etc.)
            await hass.services.async_call("homeassistant", "reload_core_config", blocking=True)

        return {"success": True}
    except Exception as exc:
        return {"success": False, "error": {"code": "file_write_error", "message": str(exc)}}


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
        result = await _run_sqlite_query(hass, args)
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
        data = await _append_config_lines(hass, payload)
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
        result = await _run_sqlite_query(hass, args)
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
        data = await _append_config_lines(hass, payload)
        connection.send_result(msg["id"], data)

    websocket_api.async_register_command(hass, ws_ferbos_config_add)
    return True


