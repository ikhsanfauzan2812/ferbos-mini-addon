# Testing Ferbos Mini Addon with Postman

This guide shows you how to test all the external API endpoints of your Ferbos Mini Addon using Postman.

## Prerequisites

1. **Ferbos Mini Addon running** on your Home Assistant instance
2. **Postman installed** (download from [postman.com](https://www.postman.com/downloads/))
3. **Addon configuration** with external access enabled

## Configuration Setup

### 1. Configure the Addon

In Home Assistant, go to **Supervisor** → **Add-on Store** → **Ferbos Mini Addon** → **Configuration**:

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

### 2. Get Your Home Assistant IP

Find your Home Assistant IP address. The addon will be accessible at:
```
http://YOUR_HA_IP:8080
```

## Postman Collection Setup

### 1. Create a New Collection

1. Open Postman
2. Click **New** → **Collection**
3. Name it "Ferbos Mini Addon API"
4. Add description: "Test collection for Ferbos Mini Addon external API"

### 2. Set Collection Variables

1. Click on your collection → **Variables** tab
2. Add these variables:

| Variable | Initial Value | Current Value | Description |
|----------|---------------|---------------|-------------|
| `base_url` | `http://YOUR_HA_IP:8080` | `http://YOUR_HA_IP:8080` | Base URL of your addon |
| `api_key` | `your-secure-api-key-here` | `your-secure-api-key-here` | Your configured API key |

## API Endpoints Testing

### 1. Basic Connection Test (No Auth Required)

#### GET - Ping Test
- **Method**: `GET`
- **URL**: `{{base_url}}/ping`
- **Headers**: None required
- **Expected Response**:
```json
{
  "status": "pong",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "addon": "Ferbos Mini Addon",
  "version": "1.0.0",
  "database_connected": true
}
```

#### GET - API Info
- **Method**: `GET`
- **URL**: `{{base_url}}/api`
- **Headers**: None required
- **Expected Response**:
```json
{
  "message": "Ferbos Mini Addon is running!",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "1.0.0",
  "database_connected": true,
  "external_access_enabled": true,
  "websocket_enabled": true,
  "endpoints": [...]
}
```

#### GET - Health Check
- **Method**: `GET`
- **URL**: `{{base_url}}/health`
- **Headers**: None required
- **Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "database_path": "/config/home-assistant_v2.db",
  "database_status": "connected",
  "addon_version": "1.0.0",
  "external_access_enabled": true,
  "websocket_enabled": true
}
```

### 2. External API Endpoints (Authentication Required)

#### GET - External Status
- **Method**: `GET`
- **URL**: `{{base_url}}/external/status`
- **Headers**:
  ```
  Authorization: Bearer {{api_key}}
  Content-Type: application/json
  ```
- **Expected Response**:
```json
{
  "addon": "Ferbos Mini Addon",
  "version": "1.0.0",
  "status": "running",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "database_connected": true,
  "database_path": "/config/home-assistant_v2.db",
  "external_access": true,
  "websocket_enabled": true
}
```

#### POST - External Query
- **Method**: `POST`
- **URL**: `{{base_url}}/external/query`
- **Headers**:
  ```
  Authorization: Bearer {{api_key}}
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{
  "query": "SELECT name FROM sqlite_master WHERE type='table' LIMIT 5",
  "params": []
}
```
- **Expected Response**:
```json
{
  "query": "SELECT name FROM sqlite_master WHERE type='table' LIMIT 5",
  "params": [],
  "results": [
    {"name": "states"},
    {"name": "events"},
    {"name": "statistics_meta"}
  ],
  "count": 3,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### GET - External Entities
- **Method**: `GET`
- **URL**: `{{base_url}}/external/entities`
- **Headers**:
  ```
  Authorization: Bearer {{api_key}}
  Content-Type: application/json
  ```
- **Expected Response**:
```json
{
  "entities": [
    "sensor.temperature",
    "light.living_room",
    "sensor.humidity"
  ],
  "count": 3,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### GET - External States
- **Method**: `GET`
- **URL**: `{{base_url}}/external/states?limit=10&entity_id=sensor.temperature`
- **Headers**:
  ```
  Authorization: Bearer {{api_key}}
  Content-Type: application/json
  ```
- **Query Parameters**:
  - `limit`: Number of results (default: 100)
  - `entity_id`: Filter by specific entity (optional)
- **Expected Response**:
```json
{
  "states": [
    {
      "state_id": 1,
      "entity_id": "sensor.temperature",
      "state": "22.5",
      "last_updated": "2024-01-15T10:30:00.000Z"
    }
  ],
  "count": 1,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 3. Internal Endpoints (No Auth Required)

#### GET - Tables
- **Method**: `GET`
- **URL**: `{{base_url}}/tables`
- **Headers**: None required
- **Expected Response**:
```json
{
  "tables": ["states", "events", "statistics_meta"],
  "count": 3
}
```

#### GET - Entities
- **Method**: `GET`
- **URL**: `{{base_url}}/entities`
- **Headers**: None required

#### POST - Query (Internal)
- **Method**: `POST`
- **URL**: `{{base_url}}/query`
- **Headers**:
  ```
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{
  "query": "SELECT entity_id, state FROM states WHERE entity_id LIKE 'sensor.%' LIMIT 5",
  "params": []
}
```

## Postman Collection JSON

Here's a complete Postman collection you can import:

```json
{
  "info": {
    "name": "Ferbos Mini Addon API",
    "description": "Test collection for Ferbos Mini Addon external API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://YOUR_HA_IP:8080",
      "type": "string"
    },
    {
      "key": "api_key",
      "value": "your-secure-api-key-here",
      "type": "string"
    }
  ],
  "item": [
    {
      "name": "Basic Tests",
      "item": [
        {
          "name": "Ping Test",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/ping",
              "host": ["{{base_url}}"],
              "path": ["ping"]
            }
          }
        },
        {
          "name": "API Info",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/api",
              "host": ["{{base_url}}"],
              "path": ["api"]
            }
          }
        },
        {
          "name": "Health Check",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/health",
              "host": ["{{base_url}}"],
              "path": ["health"]
            }
          }
        }
      ]
    },
    {
      "name": "External API (Auth Required)",
      "item": [
        {
          "name": "External Status",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{api_key}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{base_url}}/external/status",
              "host": ["{{base_url}}"],
              "path": ["external", "status"]
            }
          }
        },
        {
          "name": "External Query - Show Tables",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{api_key}}",
                "type": "text"
              },
              {
                "key": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"query\": \"SELECT name FROM sqlite_master WHERE type='table' LIMIT 5\",\n  \"params\": []\n}"
            },
            "url": {
              "raw": "{{base_url}}/external/query",
              "host": ["{{base_url}}"],
              "path": ["external", "query"]
            }
          }
        },
        {
          "name": "External Query - Get States",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{api_key}}",
                "type": "text"
              },
              {
                "key": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"query\": \"SELECT entity_id, state, last_updated FROM states ORDER BY last_updated DESC LIMIT 10\",\n  \"params\": []\n}"
            },
            "url": {
              "raw": "{{base_url}}/external/query",
              "host": ["{{base_url}}"],
              "path": ["external", "query"]
            }
          }
        },
        {
          "name": "External Entities",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{api_key}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{base_url}}/external/entities",
              "host": ["{{base_url}}"],
              "path": ["external", "entities"]
            }
          }
        },
        {
          "name": "External States",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{api_key}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{base_url}}/external/states?limit=10",
              "host": ["{{base_url}}"],
              "path": ["external", "states"],
              "query": [
                {
                  "key": "limit",
                  "value": "10"
                }
              ]
            }
          }
        }
      ]
    },
    {
      "name": "Internal API (No Auth)",
      "item": [
        {
          "name": "Get Tables",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/tables",
              "host": ["{{base_url}}"],
              "path": ["tables"]
            }
          }
        },
        {
          "name": "Get Entities",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/entities",
              "host": ["{{base_url}}"],
              "path": ["entities"]
            }
          }
        },
        {
          "name": "Internal Query",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"query\": \"SELECT entity_id, state FROM states WHERE entity_id LIKE 'sensor.%' LIMIT 5\",\n  \"params\": []\n}"
            },
            "url": {
              "raw": "{{base_url}}/query",
              "host": ["{{base_url}}"],
              "path": ["query"]
            }
          }
        }
      ]
    }
  ]
}
```

## Testing Steps

### 1. Import the Collection
1. Copy the JSON above
2. In Postman, click **Import**
3. Paste the JSON and import

### 2. Update Variables
1. Go to your collection → **Variables**
2. Update `base_url` with your Home Assistant IP
3. Update `api_key` with your configured API key

### 3. Test Basic Connection
1. Run **Ping Test** - should return 200 OK
2. Run **API Info** - should show addon information
3. Run **Health Check** - should show database status

### 4. Test External API
1. Run **External Status** - should return 200 OK with auth
2. Run **External Query - Show Tables** - should return table list
3. Run **External Entities** - should return entity list

### 5. Test Error Cases
1. Try external endpoints without API key - should return 401
2. Try invalid API key - should return 401
3. Try invalid SQL query - should return 400

## Common Issues & Solutions

### 1. Connection Refused
- **Problem**: Cannot connect to addon
- **Solution**: 
  - Check if addon is running
  - Verify IP address and port
  - Check firewall settings

### 2. 401 Unauthorized
- **Problem**: Authentication failed
- **Solution**:
  - Verify API key is correct
  - Check Authorization header format
  - Ensure external access is enabled

### 3. 429 Rate Limited
- **Problem**: Too many requests
- **Solution**:
  - Wait a minute before retrying
  - Increase rate limit in addon config
  - Reduce request frequency

### 4. 500 Internal Server Error
- **Problem**: Server error
- **Solution**:
  - Check addon logs
  - Verify database path
  - Check SQL query syntax

## Advanced Testing

### 1. Test Rate Limiting
1. Send multiple requests quickly to external endpoints
2. Should get 429 after exceeding limit
3. Wait and retry - should work again

### 2. Test SQL Injection Protection
1. Try malicious queries like `DROP TABLE`
2. Should be rejected (only SELECT allowed)
3. Test with parameterized queries

### 3. Test Large Queries
1. Query with large result sets
2. Test with different LIMIT values
3. Monitor response times

## WebSocket Testing

For WebSocket testing, you can use:
1. **Postman WebSocket** (if available in your version)
2. **Browser Developer Tools**
3. **WebSocket testing tools** like wscat

WebSocket URL: `ws://YOUR_HA_IP:8080/ws`

## Tips for Success

1. **Start Simple**: Begin with basic endpoints before testing complex queries
2. **Check Logs**: Monitor addon logs for debugging
3. **Use Variables**: Leverage Postman variables for easy configuration
4. **Test Incrementally**: Test one feature at a time
5. **Save Examples**: Save successful requests as examples for future reference

This comprehensive testing approach will help you verify that your Ferbos Mini Addon's external API is working correctly and securely!
