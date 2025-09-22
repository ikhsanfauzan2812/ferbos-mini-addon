# Ferbos Mini Addon - External API Documentation

## Overview

The Ferbos Mini Addon now supports external access with authentication, WebSocket connections, and real-time database monitoring. This allows external applications to interact with your Home Assistant database directly, similar to how HACS handles websocket connections.

## Features

- ✅ **External API Access** - Direct HTTP endpoints for external applications
- ✅ **WebSocket Support** - Real-time database monitoring and query execution
- ✅ **Authentication** - API key-based authentication for external endpoints
- ✅ **Rate Limiting** - Configurable rate limiting to prevent abuse
- ✅ **CORS Support** - Cross-origin requests enabled for web applications
- ✅ **Real-time Updates** - WebSocket notifications when database changes

## Configuration

### Addon Options

Configure the addon through Home Assistant's addon options:

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

### Environment Variables

You can also configure via environment variables:

- `PORT` - Port number (default: 8080)
- `DATABASE_PATH` - Path to Home Assistant database
- `ENABLE_EXTERNAL_ACCESS` - Enable external access (default: true)
- `API_KEY` - API key for authentication (optional)
- `ENABLE_WEBSOCKET` - Enable WebSocket support (default: true)
- `RATE_LIMIT` - Rate limit per minute (default: 100)

## API Endpoints

### Internal Endpoints (No Authentication)

These endpoints are available for internal Home Assistant use:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api` | API information and available endpoints |
| GET | `/status` | Addon status and configuration |
| GET | `/ping` | Simple health check |
| GET | `/health` | Detailed health check with database status |
| GET | `/tables` | List all database tables |
| GET | `/entities` | List all entities |
| GET | `/states` | Get recent states |
| GET | `/events` | Get recent events |
| POST | `/query` | Execute SQL query |
| GET | `/query?q=SELECT...` | Execute SQL query via GET |

### External Endpoints (Authentication Required)

These endpoints require authentication for external access:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/external/status` | External status endpoint |
| POST | `/external/query` | Execute SQL query externally |
| GET | `/external/entities` | Get entities externally |
| GET | `/external/states` | Get states externally |

### WebSocket Endpoint

| Endpoint | Description |
|----------|-------------|
| `/ws` | WebSocket connection for real-time updates |

## Authentication

External endpoints require authentication via API key in the Authorization header:

```http
Authorization: Bearer YOUR_API_KEY
```

### Example with curl:

```bash
curl -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -X POST http://your-ha-ip:8080/external/query \
     -d '{"query": "SELECT * FROM states LIMIT 10"}'
```

## WebSocket API

### Connection

Connect to the WebSocket endpoint:

```javascript
const socket = io('http://your-ha-ip:8080/ws');

socket.on('connect', () => {
    console.log('Connected to WebSocket');
});

socket.on('disconnect', () => {
    console.log('Disconnected from WebSocket');
});
```

### Events

#### Client to Server Events

| Event | Data | Description |
|-------|------|-------------|
| `query_database` | `{query: "SELECT ..."}` | Execute SQL query |
| `subscribe_entity` | `{entity_id: "sensor.temperature"}` | Subscribe to entity updates |
| `join_room` | `{room: "room_name"}` | Join a specific room |

#### Server to Client Events

| Event | Data | Description |
|-------|------|-------------|
| `connected` | `{message: "...", timestamp: "..."}` | Connection confirmation |
| `query_result` | `{query: "...", results: [...], count: 10}` | Query execution result |
| `query_error` | `{error: "error message"}` | Query execution error |
| `database_updated` | `{timestamp: "...", message: "..."}` | Database change notification |
| `joined_room` | `{room: "room_name"}` | Room join confirmation |

### Example WebSocket Usage

```javascript
const socket = io('http://your-ha-ip:8080/ws');

// Execute a query
socket.emit('query_database', {
    query: 'SELECT entity_id, state FROM states ORDER BY last_updated DESC LIMIT 10'
});

// Listen for results
socket.on('query_result', (data) => {
    console.log('Query result:', data.results);
});

// Subscribe to entity updates
socket.emit('subscribe_entity', {
    entity_id: 'sensor.temperature'
});

// Listen for database updates
socket.on('database_updated', (data) => {
    console.log('Database updated:', data.message);
});
```

## Rate Limiting

External endpoints are rate limited to prevent abuse. The default limit is 100 requests per minute per IP address. This can be configured in the addon options.

When the rate limit is exceeded, the API returns:

```json
{
    "error": "Rate limit exceeded"
}
```

With HTTP status code 429.

## CORS Support

CORS is enabled for the following origins:
- `/api/*` - API endpoints
- `/external/*` - External endpoints  
- `/ws/*` - WebSocket endpoints

All origins (`*`) are allowed by default for development. For production, consider restricting this to specific domains.

## Example Usage

### Python Example

```python
import requests
import json

# API key authentication
headers = {
    'Authorization': 'Bearer your-api-key',
    'Content-Type': 'application/json'
}

# Execute a query
response = requests.post(
    'http://your-ha-ip:8080/external/query',
    headers=headers,
    json={
        'query': 'SELECT entity_id, state FROM states WHERE entity_id LIKE "sensor.%" LIMIT 10'
    }
)

data = response.json()
print(f"Found {data['count']} results")
for result in data['results']:
    print(f"{result['entity_id']}: {result['state']}")
```

### JavaScript Example

```javascript
// HTTP API
async function queryDatabase(query) {
    const response = await fetch('http://your-ha-ip:8080/external/query', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer your-api-key',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
    });
    
    return await response.json();
}

// WebSocket API
const socket = io('http://your-ha-ip:8080/ws');

socket.on('connect', async () => {
    // Execute query via WebSocket
    socket.emit('query_database', {
        query: 'SELECT * FROM states ORDER BY last_updated DESC LIMIT 5'
    });
});

socket.on('query_result', (data) => {
    console.log('Results:', data.results);
});
```

## Security Considerations

1. **API Key**: Use a strong, unique API key for authentication
2. **Rate Limiting**: Configure appropriate rate limits for your use case
3. **Network Access**: Consider firewall rules to restrict access
4. **HTTPS**: Use HTTPS in production environments
5. **Database Access**: Only SELECT queries are allowed for security

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check if the addon is running and the port is correct
2. **Authentication Failed**: Verify the API key is correct
3. **Rate Limited**: Reduce request frequency or increase rate limit
4. **WebSocket Connection Failed**: Check if WebSocket is enabled in options

### Debug Endpoint

Use the `/debug` endpoint to get detailed information about the addon configuration:

```bash
curl http://your-ha-ip:8080/debug
```

This will show:
- Database path and status
- Configuration directory contents
- Environment variables
- Available database files

## Integration Examples

### Home Assistant Custom Component

```python
# custom_components/ferbos_addon/sensor.py
import requests
import logging

_LOGGER = logging.getLogger(__name__)

class FerbosAddonSensor(Entity):
    def __init__(self, hass, api_key):
        self.hass = hass
        self.api_key = api_key
        self._state = None
        
    def update(self):
        try:
            response = requests.get(
                'http://localhost:8080/external/status',
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            if response.status_code == 200:
                self._state = 'connected'
            else:
                self._state = 'error'
        except Exception as e:
            _LOGGER.error(f"Error connecting to Ferbos Addon: {e}")
            self._state = 'error'
```

### Node-RED Integration

```javascript
// Node-RED function node
const query = msg.payload.query || "SELECT * FROM states LIMIT 10";

const requestOptions = {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer your-api-key',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query })
};

fetch('http://your-ha-ip:8080/external/query', requestOptions)
    .then(response => response.json())
    .then(data => {
        msg.payload = data;
        return msg;
    })
    .catch(error => {
        msg.payload = { error: error.message };
        return msg;
    });
```

## Changelog

### Version 1.0.0
- Initial release with external API support
- WebSocket integration for real-time updates
- Authentication and rate limiting
- CORS support for web applications
- Comprehensive documentation and examples
