# WebSocket Bridge Integration for Ferbos Mini Addon

This document explains how to use the WebSocket bridge endpoint to access your Ferbos Mini Addon via HTTPS through your existing bridge API.

## Overview

The WebSocket bridge endpoint (`/ws_bridge`) allows you to access your addon's functionality through your existing HTTPS bridge API, similar to how you access Home Assistant's WebSocket API. This provides a unified interface for external applications.

## Bridge Endpoint

**URL**: `POST http://YOUR_HA_IP:8080/ws_bridge`

## Request Format

```json
{
  "ws_url": "wss://your-bridge-domain.com/api/websocket",
  "token": "your-api-key-here",
  "method": "ferbos/METHOD_NAME",
  "args": {
    "parameter1": "value1",
    "parameter2": "value2"
  }
}
```

## Available Methods

### Status and Info Methods

#### `ferbos/status`
Get addon status information.

**Request**:
```json
{
  "method": "ferbos/status",
  "args": {}
}
```

**Response**:
```json
{
  "success": true,
  "method": "ferbos/status",
  "result": {
    "addon": "Ferbos Mini Addon",
    "version": "1.0.0",
    "status": "running",
    "database_connected": true,
    "external_access_enabled": true,
    "websocket_enabled": true
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### `ferbos/info`
Get detailed addon information and available methods.

**Request**:
```json
{
  "method": "ferbos/info",
  "args": {}
}
```

#### `ferbos/health`
Get health check information.

**Request**:
```json
{
  "method": "ferbos/health",
  "args": {}
}
```

#### `ferbos/ping`
Simple ping test.

**Request**:
```json
{
  "method": "ferbos/ping",
  "args": {}
}
```

### Database Methods

#### `ferbos/tables`
Get list of database tables.

**Request**:
```json
{
  "method": "ferbos/tables",
  "args": {}
}
```

**Response**:
```json
{
  "success": true,
  "method": "ferbos/tables",
  "result": {
    "tables": ["states", "events", "statistics_meta"],
    "count": 3
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### `ferbos/entities`
Get list of entities.

**Request**:
```json
{
  "method": "ferbos/entities",
  "args": {}
}
```

#### `ferbos/states`
Get states data with optional filtering.

**Request**:
```json
{
  "method": "ferbos/states",
  "args": {
    "limit": 10,
    "entity_id": "sensor.temperature"
  }
}
```

#### `ferbos/events`
Get events data with optional filtering.

**Request**:
```json
{
  "method": "ferbos/events",
  "args": {
    "limit": 10,
    "event_type": "state_changed"
  }
}
```

### Query Methods

#### `ferbos/query`
Execute custom SQL queries.

**Request**:
```json
{
  "method": "ferbos/query",
  "args": {
    "query": "SELECT * FROM statistics WHERE metadata_id = 375",
    "params": []
  }
}
```

**Response**:
```json
{
  "success": true,
  "method": "ferbos/query",
  "result": {
    "query": "SELECT * FROM statistics WHERE metadata_id = 375",
    "params": [],
    "results": [
      {
        "id": 1,
        "metadata_id": 375,
        "start": "2024-01-15T00:00:00.000Z",
        "mean": 22.5,
        "min": 20.0,
        "max": 25.0
      }
    ],
    "count": 1
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### `ferbos/schema`
Get table schema information.

**Request**:
```json
{
  "method": "ferbos/schema",
  "args": {
    "table_name": "states"
  }
}
```

### WebSocket Methods

#### `ferbos/ws/connect`
Get WebSocket connection information.

**Request**:
```json
{
  "method": "ferbos/ws/connect",
  "args": {}
}
```

#### `ferbos/ws/status`
Get WebSocket status.

**Request**:
```json
{
  "method": "ferbos/ws/status",
  "args": {}
}
```

## Postman Examples

### 1. Test Addon Status
```json
{
  "ws_url": "wss://your-bridge-domain.com/api/websocket",
  "token": "your-api-key-here",
  "method": "ferbos/status",
  "args": {}
}
```

### 2. Get Database Tables
```json
{
  "ws_url": "wss://your-bridge-domain.com/api/websocket",
  "token": "your-api-key-here",
  "method": "ferbos/tables",
  "args": {}
}
```

### 3. Execute Custom Query
```json
{
  "ws_url": "wss://your-bridge-domain.com/api/websocket",
  "token": "your-api-key-here",
  "method": "ferbos/query",
  "args": {
    "query": "SELECT * FROM statistics WHERE metadata_id = 375",
    "params": []
  }
}
```

### 4. Get States with Filter
```json
{
  "ws_url": "wss://your-bridge-domain.com/api/websocket",
  "token": "your-api-key-here",
  "method": "ferbos/states",
  "args": {
    "limit": 5,
    "entity_id": "sensor.temperature"
  }
}
```

### 5. Get Table Schema
```json
{
  "ws_url": "wss://your-bridge-domain.com/api/websocket",
  "token": "your-api-key-here",
  "method": "ferbos/schema",
  "args": {
    "table_name": "states"
  }
}
```

## Error Handling

### Invalid Method
```json
{
  "error": "Unknown method: ferbos/invalid",
  "available_methods": [
    "ferbos/status", "ferbos/info", "ferbos/health", "ferbos/ping",
    "ferbos/tables", "ferbos/entities", "ferbos/states", "ferbos/events",
    "ferbos/query", "ferbos/schema", "ferbos/ws/connect", "ferbos/ws/status"
  ],
  "status_code": 404
}
```

### Authentication Error
```json
{
  "error": "Invalid token",
  "status_code": 401
}
```

### Query Error
```json
{
  "error": "Only SELECT queries are allowed",
  "status_code": 400
}
```

## Integration with Your Bridge API

To integrate with your existing bridge API, you can:

1. **Use the same endpoint structure** as your Home Assistant bridge
2. **Replace the method** with `ferbos/METHOD_NAME`
3. **Keep the same authentication** using your token
4. **Use the same args structure** for parameters

### Example Bridge Configuration

```json
{
  "ws_url": "wss://solaristic003.ferbos-dev.com/api/websocket",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "method": "ferbos/query",
  "args": {
    "query": "SELECT * FROM statistics WHERE metadata_id = 375",
    "params": []
  }
}
```

## Security Features

- **Token Authentication**: Uses your existing API key for authentication
- **SQL Injection Protection**: Only SELECT queries are allowed
- **Rate Limiting**: Inherits rate limiting from external endpoints
- **Error Handling**: Comprehensive error responses

## Benefits

1. **Unified Interface**: Same API structure as your Home Assistant bridge
2. **HTTPS Access**: Secure access through your existing bridge
3. **Easy Integration**: Drop-in replacement for Home Assistant methods
4. **Consistent Authentication**: Uses your existing token system
5. **Comprehensive Coverage**: All addon functionality available

## Usage Tips

1. **Start Simple**: Begin with `ferbos/status` to test connectivity
2. **Use Method Names**: Always prefix methods with `ferbos/`
3. **Check Available Methods**: Use `ferbos/info` to see all available methods
4. **Handle Errors**: Check for error responses and status codes
5. **Use Parameters**: Leverage the `args` object for method parameters

## Troubleshooting

### Connection Issues
- Verify the addon is running
- Check the IP address and port
- Ensure external access is enabled

### Authentication Issues
- Verify your API key is correct
- Check if the token matches your configured API key
- Ensure the token is included in the request

### Method Issues
- Use the correct method name with `ferbos/` prefix
- Check available methods with `ferbos/info`
- Verify method parameters in the `args` object

This bridge integration provides a seamless way to access your Ferbos Mini Addon through your existing HTTPS bridge API, making it easy to integrate with external applications and services.
