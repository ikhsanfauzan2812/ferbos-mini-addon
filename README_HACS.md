# Ferbos Mini - Home Assistant Integration

A Home Assistant integration that provides seamless communication with the Ferbos Mini add-on for database querying and configuration management.

## Features

- 🔍 **Database Querying**: Execute custom SQL queries on your Home Assistant database
- ⚙️ **Configuration Management**: Add lines to configuration.yaml via WebSocket API
- 🛡️ **Security**: Secure API communication with optional API key authentication
- 🔄 **Real-time**: WebSocket-based communication for instant responses
- 📊 **Flexible**: Support for both legacy and modern API formats

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to **Integrations**
3. Click the three dots menu (⋮) in the top right
4. Select **Custom repositories**
5. Add this repository: `https://github.com/ikhsanfauzan2812/ferbos-mini-addon`
6. Select **Integration** as the category
7. Click **Add**
8. Search for "Ferbos Mini" and install it
9. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy the `ferbos_mini` folder to your `custom_components` directory
3. Restart Home Assistant
4. Add the integration via **Settings** → **Devices & Services** → **Add Integration**

## Prerequisites

- **Ferbos Mini Add-on**: This integration requires the Ferbos Mini add-on to be installed and running
- **Home Assistant**: Version 2023.1.0 or higher
- **HACS**: Optional but recommended for easy installation

## Configuration

### Step 1: Install the Ferbos Mini Add-on

First, you need to install the Ferbos Mini add-on:

1. Copy the add-on files to your Home Assistant add-ons directory
2. In Home Assistant, go to **Supervisor** → **Add-on Store** → **Local Add-ons**
3. Find "Ferbos Mini Addon" and install it
4. Configure the add-on with your desired settings
5. Start the add-on

### Step 2: Configure the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Ferbos Mini"
4. Enter the add-on URL (default: `http://localhost:8080`)
5. Optionally, enter an API key if you've configured one in the add-on
6. Click **Submit**

## Usage

### WebSocket API

The integration provides WebSocket commands that can be used from the Home Assistant frontend or external applications:

#### Database Query
```javascript
// Query the database
{
  "type": "ferbos/query",
  "id": 1,
  "args": {
    "query": "SELECT * FROM states WHERE entity_id = 'sensor.temperature' LIMIT 10",
    "params": []
  }
}
```

#### Configuration Management
```javascript
// Add lines to configuration.yaml
{
  "type": "ferbos/config/add",
  "id": 2,
  "args": {
    "lines": [
      "automation:",
      "  - alias: 'Test Automation'",
      "    trigger:",
      "      platform: state",
      "      entity_id: sensor.temperature"
    ],
    "validate": true,
    "reload_core": true,
    "backup": true
  }
}
```

### Frontend Usage

You can use these WebSocket commands in your custom Lovelace cards or external applications by connecting to Home Assistant's WebSocket API.

## API Endpoints (Add-on)

The Ferbos Mini add-on provides these HTTP endpoints:

- `GET /health` - Health check
- `GET /tables` - List all database tables
- `GET /schema/{table_name}` - Get table schema
- `POST /query` - Execute custom SQL queries
- `GET /states` - Get recent states
- `GET /events` - Get recent events
- `GET /entities` - Get all entity IDs

## Security

- Only SELECT queries are allowed for security
- Optional API key authentication
- All queries are logged for monitoring
- Database access is read-only

## Troubleshooting

1. **Integration not found**: Ensure the add-on is installed and running
2. **Connection failed**: Check the add-on URL and ensure it's accessible
3. **Permission denied**: Verify the add-on has proper database access
4. **WebSocket errors**: Check Home Assistant logs for detailed error messages

## Development

For development and testing:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the add-on locally
python run.py
```

## Support

- **Documentation**: [GitHub Repository](https://github.com/ikhsanfauzan2812/ferbos-mini-addon)
- **Issues**: [GitHub Issues](https://github.com/ikhsanfauzan2812/ferbos-mini-addon/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ikhsanfauzan2812/ferbos-mini-addon/discussions)

## License

This project is provided as-is for educational and personal use.
