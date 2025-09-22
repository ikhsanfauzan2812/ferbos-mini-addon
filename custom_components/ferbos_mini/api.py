from __future__ import annotations
import aiohttp

class FerbosAddonClient:
    def __init__(self, addon_base_url: str, api_key: str | None = None):
        self._base = addon_base_url.rstrip("/")
        self._api_key = api_key or ""

    async def proxy_query(self, session: aiohttp.ClientSession, args: dict) -> dict:
        payload = {
            "method": "ferbos/query",
            "args": args or {},
        }
        if self._api_key:
            payload["token"] = self._api_key
        url = f"{self._base}/ws_bridge"
        async with session.post(url, json=payload) as resp:
            return await resp.json(content_type=None)


