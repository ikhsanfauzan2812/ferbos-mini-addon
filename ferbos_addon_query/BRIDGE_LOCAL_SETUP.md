# Local Bridge API Setup Guide

This guide helps you run and test the bridge API locally before deployment.

## Prerequisites

1. **Python 3.8+** installed
2. **Your addon running** on localhost:8080
3. **Home Assistant accessible** via WebSocket

## Quick Start

### 1. Install Dependencies

```bash
pip install -r bridge_requirements.txt
```

### 2. Configure the Bridge

Edit `bridge_api_fixed.py` and update these variables:

```python
# Configuration - Update these for your local setup
ADDON_BASE_URL = "http://localhost:8080"  # Your local addon URL
ADDON_API_KEY = "your-secure-api-key-here"  # Your addon API key from config
```

**Important**: Make sure `ADDON_API_KEY` matches the API key you configured in your addon.

### 3. Start the Bridge API

```bash
python start_bridge.py
```

Or directly:

```bash
python bridge_api_fixed.py
```

The bridge will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

### 4. Test the Setup

```bash
python test_bridge_local.py
```

## Configuration Details

### Addon Configuration

Make sure your addon is configured with:

```json
{
  "port": 8080,
  "database_path": "/config/home-assistant_v2.db",
  "enable_external_access": true,
  "api_key": "your-secure-api-key-here",
  "enable_websocket": true,
  "rate_limit": 100
}
```

### Bridge Configuration

The bridge automatically detects method types:

- **Addon methods** (`ferbos/*`) → Routed to your addon
- **HA methods** (everything else) → Routed to Home Assistant WebSocket

## Testing

### Test 1: Direct Addon Access

```bash
curl -X POST http://localhost:8080/ws_bridge \
  -H "Content-Type: application/json" \
  -d '{
    "method": "ferbos/status",
    "args": {},
    "token": "your-secure-api-key-here"
  }'
```

### Test 2: Bridge with Addon Method

```bash
curl -X POST http://localhost:8000/ws_bridge \
  -H "Content-Type: application/json" \
  -d '{
    "ws_url": "wss://your-ha-domain.com/api/websocket",
    "token": "your-ha-token",
    "method": "ferbos/query",
    "args": {
      "query": "SELECT * FROM statistics WHERE metadata_id = 375",
      "params": []
    }
  }'
```

### Test 3: Bridge with HA Method

```bash
curl -X POST http://localhost:8000/ws_bridge \
  -H "Content-Type: application/json" \
  -d '{
    "ws_url": "wss://your-ha-domain.com/api/websocket",
    "token": "your-ha-token",
    "method": "states/get",
    "args": {}
  }'
```

## Postman Testing

1. **Import the collection**: `Ferbos_Mini_Addon_API.postman_collection.json`
2. **Update variables**:
   - `base_url`: `http://localhost:8000` (for bridge) or `http://localhost:8080` (for direct addon)
   - `api_key`: Your configured API key
3. **Use the "🌉 WebSocket Bridge" folder** for bridge testing

## Troubleshooting

### Bridge Not Starting

```bash
# Check if port 8000 is available
netstat -an | grep 8000

# Try a different port
uvicorn bridge_api_fixed:app --host 0.0.0.0 --port 8001
```

### Addon Not Accessible

```bash
# Test addon directly
curl http://localhost:8080/ping

# Check addon logs in Home Assistant
```

### Authentication Issues

1. **Verify API key** matches in both addon config and bridge config
2. **Check addon external access** is enabled
3. **Test with direct addon access** first

### WebSocket Issues

1. **Verify HA WebSocket URL** is correct
2. **Check HA token** is valid
3. **Test HA WebSocket** directly first

## Development Tips

### Auto-reload

The bridge runs with auto-reload enabled, so changes to the code will automatically restart the server.

### Debug Mode

For more detailed logging, modify the uvicorn run command:

```python
uvicorn.run(
    "bridge_api_fixed:app",
    host="0.0.0.0",
    port=8000,
    reload=True,
    log_level="debug"  # More verbose logging
)
```

### Testing Different Scenarios

Use the test script to verify different scenarios:

```bash
# Test all scenarios
python test_bridge_local.py

# Test specific scenarios by modifying the test script
```

## Deployment Preparation

Once local testing is successful:

1. **Update configuration** for production:
   - Change `ADDON_BASE_URL` to your production addon URL
   - Update `ADDON_API_KEY` to production API key
   - Configure proper logging and error handling

2. **Test with production URLs**:
   - Use your actual HA WebSocket URL
   - Test with production addon URL

3. **Deploy to your server**:
   - Copy the bridge files to your server
   - Install dependencies
   - Configure as a service (systemd, docker, etc.)

## File Structure

```
ferbos_addon_query/
├── bridge_api_fixed.py          # Main bridge API
├── bridge_requirements.txt      # Python dependencies
├── start_bridge.py             # Startup script
├── test_bridge_local.py        # Test script
├── BRIDGE_LOCAL_SETUP.md       # This guide
└── run.py                      # Your addon
```

## Next Steps

1. **Run local tests** to verify everything works
2. **Test with your actual HA instance** using production URLs
3. **Deploy to your server** when ready
4. **Monitor logs** for any issues

Happy testing! 🚀
