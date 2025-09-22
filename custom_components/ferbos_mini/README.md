# Ferbos Mini - Custom Integration

Registers a Home Assistant WebSocket command so your existing bridge can call your addon without changes.

## Install
1. Copy `custom_components/ferbos_mini/` into your Home Assistant `/config/custom_components/`.
2. Add to `configuration.yaml`:
```yaml
ferbos_mini:
  addon_base_url: "http://<HA_IP>:8080"   # or your Cloudflare hostname
  api_key: ""                              # if set in addon
```
3. Restart Home Assistant.

## Usage
Send to HA WebSocket (unchanged bridge payload):
```json
{ "id": 1, "type": "ferbos/query", "args": { "query": "SELECT 1", "params": [] } }
```
The integration proxies to the addon `/ws_bridge` and returns the JSON result.


