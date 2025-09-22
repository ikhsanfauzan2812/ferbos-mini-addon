from fastapi import FastAPI, Request
import websockets
import asyncio
import json
import uvicorn
import httpx

app = FastAPI()

# Configuration - Update these for your local setup
ADDON_BASE_URL = "http://192.168.68.102:8080"  # Your Home Assistant IP
ADDON_API_KEY = "your-secure-api-key-here"  # Your addon API key from config

@app.post("/ws_bridge")
async def websocket_bridge(request: Request):
    data = await request.json()
    ws_url = data.get("ws_url")
    token = data.get("token")
    method = data.get("method")
    args = data.get("args", {})

    if not all([ws_url, token, method]):
        return {"error": "Missing one of: ws_url, token, method"}

    # Check if this is an addon method
    if method.startswith("ferbos/"):
        return await handle_addon_method(method, args, token)
    
    # Otherwise, handle as Home Assistant WebSocket command
    return await handle_ha_websocket(ws_url, token, method, args)

async def handle_addon_method(method: str, args: dict, token: str):
    """Handle addon methods by calling the addon directly"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ADDON_BASE_URL}/ws_bridge",
                json={
                    "method": method,
                    "args": args,
                    "token": token
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Addon request failed with status {response.status_code}",
                    "details": response.text
                }
                
    except Exception as e:
        return {"error": f"Failed to call addon: {str(e)}"}

async def handle_ha_websocket(ws_url: str, token: str, method: str, args: dict):
    """Handle Home Assistant WebSocket commands"""
    try:
        async with websockets.connect(ws_url) as ws:
            await ws.recv()  # hello

            await ws.send(json.dumps({
                "type": "auth",
                "access_token": token
            }))
            await ws.recv()  # auth_ok

            # Send method & args to websocket
            command = {
                "id": 1,
                "type": method,
                **args
            }

            await ws.send(json.dumps(command))

            while True:
                message = await ws.recv()
                parsed = json.loads(message)

                # Filter response selain event/ping
                if parsed.get("type") not in ("event", "ping"):
                    return parsed

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
