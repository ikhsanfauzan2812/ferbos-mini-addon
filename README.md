# Home Assistant Database Query Addon

A mini addon for Home Assistant that provides HTTP API endpoints to query the Home Assistant database (`home_assistant_v2.db`) from outside the Home Assistant environment.

## Features

- 🔍 Query Home Assistant database via HTTP API
- 📊 Get states, events, and entity information
- 🛡️ Security-focused (only SELECT queries allowed)
- 🐳 Docker-based deployment
- 📈 Health check endpoint
- 🔧 Custom SQL query support

## Installation

1. Copy this addon to your Home Assistant addons directory:
   ```bash
   cp -r ferbos-addon-query /config/addons/
   ```

2. In Home Assistant, go to **Supervisor** → **Add-on Store** → **Local Add-ons**

3. Find "Database Query Addon" and click **Install**

4. Configure the addon settings:
   - **Port**: Default 8080 (change if needed)
   - **Database Path**: Default `/config/home_assistant_v2.db`

5. Start the addon

## API Endpoints

### Health Check
```http
GET /health
```
Returns the health status of the addon and database connection.

### Get All Tables
```http
GET /tables
```
Returns a list of all tables in the Home Assistant database.

### Get Table Schema
```http
GET /schema/{table_name}
```
Returns the schema information for a specific table.

### Execute Custom Query
```http
POST /query
Content-Type: application/json

{
  "query": "SELECT * FROM states WHERE entity_id = 'sensor.temperature' LIMIT 10",
  "params": []
}
```
Execute custom SQL SELECT queries. Only SELECT queries are allowed for security.

### Get States
```http
GET /states?limit=100&entity_id=sensor.temperature
```
Get recent states from the states table with optional filtering.

### Get Events
```http
GET /events?limit=100&event_type=state_changed
```
Get recent events from the events table with optional filtering.

### Get Entities
```http
GET /entities
```
Get a list of all unique entity IDs from the states table.

## Usage Examples

### Get all entities
```bash
curl http://your-ha-ip:8080/entities
```

### Get recent states for a specific entity
```bash
curl "http://your-ha-ip:8080/states?entity_id=sensor.temperature&limit=50"
```

### Execute custom query
```bash
curl -X POST http://your-ha-ip:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT entity_id, state, last_updated FROM states WHERE state = '\''on'\'' ORDER BY last_updated DESC LIMIT 10",
    "params": []
  }'
```

### Get table schema
```bash
curl http://your-ha-ip:8080/schema/states
```

## Configuration

The addon can be configured through the Home Assistant addon configuration:

```json
{
  "port": 8080,
  "database_path": "/config/home_assistant_v2.db"
}
```

## Security Notes

- Only SELECT queries are allowed for security reasons
- The addon runs with limited privileges
- Database access is read-only
- All queries are logged for monitoring

## Troubleshooting

1. **Database not found**: Ensure the database path is correct and the file exists
2. **Permission denied**: Check that the addon has access to the database file
3. **Port conflicts**: Change the port in the addon configuration if 8080 is already in use

## Development

To run locally for development:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_PATH="/path/to/home_assistant_v2.db"
export PORT=8080

# Run the application
python run.py
```

## License

This addon is provided as-is for educational and personal use.
