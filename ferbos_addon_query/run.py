#!/usr/bin/env python3
"""
Home Assistant Database Query Addon
Provides HTTP API endpoints and WebSocket support to query the Home Assistant database
Supports external access with authentication and real-time updates
"""

import os
import json
import sqlite3
import logging
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from functools import wraps
from collections import defaultdict, deque

from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import eventlet
import requests
import pathlib
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ferbos-addon-secret-key')

# Initialize SocketIO with CORS support
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize CORS
CORS(app, resources={
    r"/api/*": {"origins": "*"},
    r"/external/*": {"origins": "*"},
    r"/ws/*": {"origins": "*"}
})

# Rate limiting storage
rate_limit_storage = defaultdict(lambda: deque())

class Config:
    """Configuration management"""
    def __init__(self):
        self.port = int(os.getenv('PORT', 8080))
        self.database_path = os.getenv('DATABASE_PATH', '/config/home-assistant_v2.db')
        self.enable_external_access = os.getenv('ENABLE_EXTERNAL_ACCESS', 'true').lower() == 'true'
        self.api_key = os.getenv('API_KEY', '')
        self.enable_websocket = os.getenv('ENABLE_WEBSOCKET', 'true').lower() == 'true'
        self.rate_limit = int(os.getenv('RATE_LIMIT', 100))
        self.allow_all_queries = os.getenv('ALLOW_ALL_QUERIES', 'true').lower() == 'true'
        self.allowed_tables = os.getenv('ALLOWED_TABLES', '').split(',') if os.getenv('ALLOWED_TABLES') else []
        
        # Load from options.json if available
        self.load_options()
    
    def load_options(self):
        """Load configuration from options.json"""
        try:
            options_path = '/data/options.json'
            if os.path.exists(options_path):
                with open(options_path, 'r') as f:
                    options = json.load(f)
                    self.port = options.get('port', self.port)
                    self.database_path = options.get('database_path', self.database_path)
                    self.enable_external_access = options.get('enable_external_access', self.enable_external_access)
                    self.api_key = options.get('api_key', self.api_key)
                    self.enable_websocket = options.get('enable_websocket', self.enable_websocket)
                    self.rate_limit = options.get('rate_limit', self.rate_limit)
                    self.allow_all_queries = options.get('allow_all_queries', self.allow_all_queries)
                    self.allowed_tables = options.get('allowed_tables', self.allowed_tables)
                logger.info("Loaded configuration from options.json")
        except Exception as e:
            logger.warning(f"Could not load options.json: {e}")

config = Config()

def rate_limit(max_requests=100, window=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            now = time.time()
            
            # Clean old requests
            while rate_limit_storage[client_ip] and rate_limit_storage[client_ip][0] <= now - window:
                rate_limit_storage[client_ip].popleft()
            
            # Check rate limit
            if len(rate_limit_storage[client_ip]) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Add current request
            rate_limit_storage[client_ip].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_auth(f):
    """Authentication decorator for external endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not config.enable_external_access:
            return jsonify({'error': 'External access is disabled'}), 403
        
        # Check API key if configured
        if config.api_key:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'API key required'}), 401
            
            provided_key = auth_header.split(' ')[1]
            if provided_key != config.api_key:
                return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

class HomeAssistantDB:
    """Handle Home Assistant database operations with real-time monitoring"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.last_modified = 0
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """Ensure the database file exists and is accessible"""
        if not os.path.exists(self.db_path):
            logger.warning(f"Database file not found at {self.db_path}")
            self.create_test_db()
    
    def create_test_db(self):
        """Create a minimal test database structure"""
        try:
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_db_path = os.path.join(temp_dir, "home_assistant_test.db")
            
            logger.info(f"Creating test database at: {temp_db_path}")
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            # Create basic tables that might exist in HA
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS states (
                    state_id INTEGER PRIMARY KEY,
                    entity_id TEXT,
                    state TEXT,
                    attributes TEXT,
                    event_id INTEGER,
                    last_changed TEXT,
                    last_updated TEXT,
                    context_id TEXT,
                    context_user_id TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY,
                    event_type TEXT,
                    event_data TEXT,
                    origin TEXT,
                    time_fired TEXT,
                    context_id TEXT,
                    context_user_id TEXT
                )
            ''')
            
            # Insert some sample data
            cursor.execute('''
                INSERT OR IGNORE INTO states (entity_id, state, last_updated) VALUES
                ('sensor.temperature', '22.5', datetime('now')),
                ('light.living_room', 'on', datetime('now')),
                ('sensor.humidity', '45', datetime('now')),
                ('switch.garage', 'off', datetime('now')),
                ('sensor.motion', 'clear', datetime('now'))
            ''')
            
            conn.commit()
            conn.close()
            
            self.db_path = temp_db_path
            logger.info(f"Created test database with sample data at: {temp_db_path}")
        except Exception as e:
            logger.error(f"Error creating test database: {e}")
            self.db_path = ":memory:"
            logger.info("Using in-memory database as fallback")
    
    def check_for_changes(self):
        """Check if database has been modified and emit updates via websocket"""
        try:
            if os.path.exists(self.db_path):
                current_modified = os.path.getmtime(self.db_path)
                if current_modified > self.last_modified:
                    self.last_modified = current_modified
                    # Emit database change event
                    socketio.emit('database_updated', {
                        'timestamp': datetime.now().isoformat(),
                        'message': 'Database has been updated'
                    }, namespace='/ws')
                    return True
        except Exception as e:
            logger.error(f"Error checking database changes: {e}")
        return False
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as list of dictionaries"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                row_dict = {}
                for key in row.keys():
                    value = row[key]
                    if isinstance(value, bytes):
                        value = value.decode('utf-8', errors='ignore')
                    row_dict[key] = value
                results.append(row_dict)
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []
    
    def get_tables(self) -> List[str]:
        """Get list of all tables in the database"""
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        results = self.execute_query(query)
        return [row['name'] for row in results]
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific table"""
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)

# Initialize database connection
def find_home_assistant_db():
    """Find the Home Assistant database file"""
    possible_paths = [
        '/config/home-assistant_v2.db',
        '/config/home_assistant_v2.db',
        '/config/home-assistant.db',
        config.database_path
    ]
    
    env_path = os.getenv('DATABASE_PATH')
    if env_path:
        possible_paths.insert(0, env_path)
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found Home Assistant database at: {path}")
            return path
    
    logger.warning("No Home Assistant database found, will create test database")
    return None

db_path = find_home_assistant_db() or config.database_path
logger.info(f"Initializing database connection with path: {db_path}")

try:
    ha_db = HomeAssistantDB(db_path)
    logger.info("Database connection initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database connection: {e}")
    class DummyDB:
        def __init__(self):
            self.db_path = "dummy"
        def get_tables(self):
            return []
        def execute_query(self, query, params=()):
            return []
        def get_table_schema(self, table_name):
            return []
        def check_for_changes(self):
            return False
    ha_db = DummyDB()

# WebSocket Events
@socketio.on('connect', namespace='/ws')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {
        'message': 'Connected to Ferbos Addon WebSocket',
        'timestamp': datetime.now().isoformat(),
        'database_connected': ha_db.db_path != "dummy"
    })

@socketio.on('disconnect', namespace='/ws')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_room', namespace='/ws')
def handle_join_room(data):
    """Handle joining a room for specific updates"""
    room = data.get('room', 'general')
    join_room(room)
    emit('joined_room', {'room': room})

@socketio.on('subscribe_entity', namespace='/ws')
def handle_subscribe_entity(data):
    """Subscribe to updates for a specific entity"""
    entity_id = data.get('entity_id')
    if entity_id:
        join_room(f'entity_{entity_id}')
        emit('subscribed', {'entity_id': entity_id})

@socketio.on('query_database', namespace='/ws')
def handle_query_database(data):
    """Handle database queries via WebSocket"""
    query = data.get('query', '')
    if not query:
        emit('query_error', {'error': 'Query is required'})
        return
    
    # Validate query safety
    validation = validate_query_safety(query)
    if not validation['allowed']:
        emit('query_error', {'error': validation['reason']})
        return
    
    try:
        results = ha_db.execute_query(query)
        emit('query_result', {
            'query': query,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        emit('query_error', {'error': str(e)})

# HTTP Routes
@app.route('/', methods=['GET'])
def root():
    """Root endpoint - serve web interface"""
    return render_template('index.html')

@app.route('/api', methods=['GET'])
def api_info():
    """API info endpoint"""
    return jsonify({
        'message': 'Ferbos Mini Addon is running!',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'database_connected': ha_db.db_path != "dummy",
        'database_path': ha_db.db_path,
        'external_access_enabled': config.enable_external_access,
        'websocket_enabled': config.enable_websocket,
        'endpoints': [
            '/ping',
            '/health', 
            '/debug',
            '/tables',
            '/entities',
            '/states',
            '/events',
            '/query',
            '/external/status',
            '/external/query',
            '/ws_bridge',  # WebSocket bridge endpoint
            '/ws'  # WebSocket endpoint
        ]
    })

@app.route('/status', methods=['GET'])
def status():
    """Standalone status page"""
    return jsonify({
        'addon': 'Ferbos Mini Addon',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'database_connected': ha_db.db_path != "dummy",
        'database_path': ha_db.db_path,
        'external_access_enabled': config.enable_external_access,
        'websocket_enabled': config.enable_websocket,
        'access_methods': {
            'web_interface': '/',
            'api_info': '/api',
            'health_check': '/ping',
            'database_query': '/query',
            'external_api': '/external/status',
            'websocket': '/ws'
        }
    })

# WebSocket Bridge endpoint for HTTPS access
@app.route('/ws_bridge', methods=['POST'])
def ws_bridge():
    """WebSocket bridge endpoint for external HTTPS access"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON payload'}), 400
        
        # Extract bridge parameters
        method = data.get('method', '')
        args = data.get('args', {})
        token = data.get('token', '')
        
        # Debug logging
        logger.info(f"Bridge request - Method: {method}, Args: {args}, Token: {token[:20]}..." if token else "No token")
        
        # Validate required fields
        if not method:
            return jsonify({'error': 'Method is required'}), 400
        
        # Handle authentication if token provided
        if token and config.api_key:
            if token != config.api_key:
                return jsonify({'error': 'Invalid token'}), 401
        
        # Route to appropriate addon method
        result = route_bridge_method(method, args)
        
        if result.get('error'):
            return jsonify(result), result.get('status_code', 400)
        
        return jsonify({
            'success': True,
            'method': method,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"WebSocket bridge error: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def validate_query_safety(query: str) -> dict:
    """Validate query for safety and permissions"""
    query_upper = query.strip().upper()
    
    # Always allow SELECT queries
    if query_upper.startswith('SELECT'):
        return {'allowed': True, 'reason': 'SELECT queries are always allowed'}
    
    # Check if all queries are enabled
    if not config.allow_all_queries:
        return {
            'allowed': False, 
            'reason': 'Only SELECT queries are allowed. Enable allow_all_queries in config to allow other query types.'
        }
    
    # Check for dangerous operations
    dangerous_keywords = ['DROP', 'ALTER', 'CREATE', 'TRUNCATE', 'VACUUM', 'REINDEX']
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return {
                'allowed': False,
                'reason': f'{keyword} operations are not allowed for safety'
            }
    
    # Check table restrictions
    if config.allowed_tables:
        # Extract table names from query (basic parsing)
        import re
        table_matches = re.findall(r'FROM\s+(\w+)', query_upper)
        table_matches.extend(re.findall(r'INTO\s+(\w+)', query_upper))
        table_matches.extend(re.findall(r'UPDATE\s+(\w+)', query_upper))
        
        for table in table_matches:
            if table not in config.allowed_tables:
                return {
                    'allowed': False,
                    'reason': f'Table {table} is not in allowed_tables list'
                }
    
    return {'allowed': True, 'reason': 'Query passed safety checks'}

def route_bridge_method(method: str, args: dict) -> dict:
    """Route bridge method calls to appropriate addon functions"""
    try:
        # Method mapping for addon endpoints
        method_map = {
            # Status and info methods
            'ferbos/status': lambda: get_addon_status(),
            'ferbos/info': lambda: get_addon_info(),
            'ferbos/health': lambda: get_health_status(),
            'ferbos/ping': lambda: get_ping_status(),
            
            # Database methods
            'ferbos/tables': lambda: get_database_tables(),
            'ferbos/entities': lambda: get_entities_list(),
            'ferbos/states': lambda: get_states_data(args),
            'ferbos/events': lambda: get_events_data(args),
            
            # Query methods
            'ferbos/query': lambda: execute_bridge_query(args),
            'ferbos/schema': lambda: get_table_schema_bridge(args),
            
            # WebSocket methods
            'ferbos/ws/connect': lambda: get_websocket_info(),
            'ferbos/ws/status': lambda: get_websocket_status(),
        }
        
        if method not in method_map:
            return {
                'error': f'Unknown method: {method}',
                'available_methods': list(method_map.keys()),
                'status_code': 404
            }
        
        return method_map[method]()
        
    except Exception as e:
        logger.error(f"Method routing error: {e}")
        return {'error': str(e), 'status_code': 500}

# Bridge helper functions
def get_addon_status():
    """Get addon status for bridge"""
    return {
        'addon': 'Ferbos Mini Addon',
        'version': '1.0.0',
        'status': 'running',
        'database_connected': ha_db.db_path != "dummy",
        'external_access_enabled': config.enable_external_access,
        'websocket_enabled': config.enable_websocket
    }

def get_addon_info():
    """Get addon info for bridge"""
    return {
        'message': 'Ferbos Mini Addon is running!',
        'version': '1.0.0',
        'database_connected': ha_db.db_path != "dummy",
        'database_path': ha_db.db_path,
        'external_access_enabled': config.enable_external_access,
        'websocket_enabled': config.enable_websocket,
        'available_methods': [
            'ferbos/status', 'ferbos/info', 'ferbos/health', 'ferbos/ping',
            'ferbos/tables', 'ferbos/entities', 'ferbos/states', 'ferbos/events',
            'ferbos/query', 'ferbos/schema', 'ferbos/ws/connect', 'ferbos/ws/status'
        ]
    }

def get_health_status():
    """Get health status for bridge"""
    try:
        db_status = "unknown"
        try:
            ha_db.get_tables()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        return {
            'status': 'healthy',
            'database_path': ha_db.db_path,
            'database_status': db_status,
            'addon_version': '1.0.0',
            'external_access_enabled': config.enable_external_access,
            'websocket_enabled': config.enable_websocket
        }
    except Exception as e:
        return {'error': str(e), 'status_code': 500}

def get_ping_status():
    """Get ping status for bridge"""
    return {
        'status': 'pong',
        'addon': 'Ferbos Mini Addon',
        'version': '1.0.0',
        'database_connected': ha_db.db_path != "dummy"
    }

def get_database_tables():
    """Get database tables for bridge"""
    try:
        tables = ha_db.get_tables()
        return {
            'tables': tables,
            'count': len(tables)
        }
    except Exception as e:
        return {'error': str(e), 'status_code': 500}

def get_entities_list():
    """Get entities list for bridge"""
    try:
        query = "SELECT DISTINCT entity_id FROM states ORDER BY entity_id"
        results = ha_db.execute_query(query)
        entities = [row['entity_id'] for row in results]
        return {
            'entities': entities,
            'count': len(entities)
        }
    except Exception as e:
        return {'error': str(e), 'status_code': 500}

def get_states_data(args):
    """Get states data for bridge"""
    try:
        limit = args.get('limit', 100)
        entity_id = args.get('entity_id')
        
        if entity_id:
            query = "SELECT * FROM states WHERE entity_id = ? ORDER BY last_updated DESC LIMIT ?"
            params = (entity_id, limit)
        else:
            query = "SELECT * FROM states ORDER BY last_updated DESC LIMIT ?"
            params = (limit,)
        
        results = ha_db.execute_query(query, params)
        return {
            'states': results,
            'count': len(results)
        }
    except Exception as e:
        return {'error': str(e), 'status_code': 500}

def get_events_data(args):
    """Get events data for bridge"""
    try:
        limit = args.get('limit', 100)
        event_type = args.get('event_type')
        
        if event_type:
            query = "SELECT * FROM events WHERE event_type = ? ORDER BY time_fired DESC LIMIT ?"
            params = (event_type, limit)
        else:
            query = "SELECT * FROM events ORDER BY time_fired DESC LIMIT ?"
            params = (limit,)
        
        results = ha_db.execute_query(query, params)
        return {
            'events': results,
            'count': len(results)
        }
    except Exception as e:
        return {'error': str(e), 'status_code': 500}

def execute_bridge_query(args):
    """Execute query for bridge"""
    try:
        query = args.get('query', '')
        params = args.get('params', [])
        
        # Debug logging
        logger.info(f"Bridge query args: {args}")
        logger.info(f"Extracted query: '{query}'")
        logger.info(f"Extracted params: {params}")
        
        if not query:
            return {'error': 'Query is required', 'status_code': 400}
        
        # Validate query safety
        validation = validate_query_safety(query)
        if not validation['allowed']:
            return {'error': validation['reason'], 'status_code': 400}
        
        # Execute query
        results = ha_db.execute_query(query, tuple(params))
        
        # For non-SELECT queries, return affected rows count
        query_upper = query.strip().upper()
        if query_upper.startswith(('INSERT', 'UPDATE', 'DELETE')):
            return {
                'query': query,
                'params': params,
                'affected_rows': len(results) if results else 0,
                'message': f'Query executed successfully. {len(results) if results else 0} rows affected.'
            }
        else:
            return {
                'query': query,
                'params': params,
                'results': results,
                'count': len(results)
            }
    except Exception as e:
        logger.error(f"Bridge query error: {e}")
        return {'error': str(e), 'status_code': 500}

def get_table_schema_bridge(args):
    """Get table schema for bridge"""
    try:
        table_name = args.get('table_name', '')
        if not table_name:
            return {'error': 'table_name is required', 'status_code': 400}
        
        schema = ha_db.get_table_schema(table_name)
        return {
            'table': table_name,
            'schema': schema
        }
    except Exception as e:
        return {'error': str(e), 'status_code': 500}

def get_websocket_info():
    """Get WebSocket info for bridge"""
    return {
        'websocket_enabled': config.enable_websocket,
        'websocket_url': f'ws://{request.host}/ws',
        'events': [
            'connect', 'disconnect', 'query_database', 'subscribe_entity',
            'database_updated', 'query_result', 'query_error'
        ]
    }

def get_websocket_status():
    """Get WebSocket status for bridge"""
    return {
        'websocket_enabled': config.enable_websocket,
        'connected_clients': len(socketio.server.manager.rooms.get('/', {}).get('', set())),
        'status': 'active' if config.enable_websocket else 'disabled'
    }

# External API endpoints (with authentication)
@app.route('/external/status', methods=['GET'])
@require_auth
@rate_limit(max_requests=config.rate_limit)
def external_status():
    """External status endpoint with authentication"""
    return jsonify({
        'addon': 'Ferbos Mini Addon',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'database_connected': ha_db.db_path != "dummy",
        'database_path': ha_db.db_path,
        'external_access': True,
        'websocket_enabled': config.enable_websocket
    })

@app.route('/external/query', methods=['POST'])
@require_auth
@rate_limit(max_requests=config.rate_limit)
def external_query():
    """External query endpoint with authentication"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        params = data.get('params', [])
        
        # Validate query safety
        validation = validate_query_safety(query)
        if not validation['allowed']:
            return jsonify({'error': validation['reason']}), 400
        
        results = ha_db.execute_query(query, tuple(params))
        
        return jsonify({
            'query': query,
            'params': params,
            'results': results,
            'count': len(results),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/external/entities', methods=['GET'])
@require_auth
@rate_limit(max_requests=config.rate_limit)
def external_entities():
    """External entities endpoint with authentication"""
    try:
        query = "SELECT DISTINCT entity_id FROM states ORDER BY entity_id"
        results = ha_db.execute_query(query)
        entities = [row['entity_id'] for row in results]
        
        return jsonify({
            'entities': entities,
            'count': len(entities),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/external/states', methods=['GET'])
@require_auth
@rate_limit(max_requests=config.rate_limit)
def external_states():
    """External states endpoint with authentication"""
    try:
        limit = request.args.get('limit', 100, type=int)
        entity_id = request.args.get('entity_id')
        
        if entity_id:
            query = "SELECT * FROM states WHERE entity_id = ? ORDER BY last_updated DESC LIMIT ?"
            params = (entity_id, limit)
        else:
            query = "SELECT * FROM states ORDER BY last_updated DESC LIMIT ?"
            params = (limit,)
        
        results = ha_db.execute_query(query, params)
        return jsonify({
            'states': results,
            'count': len(results),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Standard endpoints (no authentication required for internal use)
@app.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint"""
    return jsonify({
        'status': 'pong',
        'timestamp': datetime.now().isoformat(),
        'addon': 'Ferbos Mini Addon',
        'version': '1.0.0',
        'database_connected': ha_db.db_path != "dummy"
    })

@app.route('/debug', methods=['GET'])
def debug_info():
    """Debug information endpoint"""
    try:
        import glob
        
        db_files = []
        try:
            db_files = glob.glob('/config/*.db')
        except Exception as e:
            logger.error(f"Error listing db files: {e}")
        
        config_contents = []
        try:
            if os.path.exists('/config'):
                config_contents = os.listdir('/config')
        except Exception as e:
            logger.error(f"Error listing config directory: {e}")
        
        return jsonify({
            'current_database_path': ha_db.db_path,
            'database_exists': os.path.exists(ha_db.db_path),
            'config_directory_contents': config_contents,
            'db_files_in_config': db_files,
            'working_directory': os.getcwd(),
            'external_access_enabled': config.enable_external_access,
            'websocket_enabled': config.enable_websocket,
            'allow_all_queries': config.allow_all_queries,
            'allowed_tables': config.allowed_tables,
            'environment_variables': {
                'DATABASE_PATH': os.getenv('DATABASE_PATH'),
                'HOME': os.getenv('HOME'),
                'USER': os.getenv('USER'),
                'API_KEY': '***' if config.api_key else None
            }
        })
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/ha_config/insert', methods=['POST'])
def ha_config_insert():
    """Safely insert a YAML snippet as a new file under /config using includes.

    Body JSON:
    {
      "relative_dir": "packages/ferbos",   # required, relative under /config
      "filename": "my_feature.yaml",       # required, file name to write
      "yaml": "automation:\n  - alias: Test...",  # required
      "validate": true,                     # optional, default true
      "reload_core": true,                  # optional, default true
      "overwrite": false                    # optional, default false
    }
    """
    try:
        data = request.get_json(force=True, silent=False)
        if not data:
            return jsonify({'error': 'JSON body required'}), 400

        relative_dir = str(data.get('relative_dir', '')).strip()
        filename = str(data.get('filename', '')).strip()
        yaml_text = data.get('yaml', None)
        validate = bool(data.get('validate', True))
        reload_core = bool(data.get('reload_core', True))
        overwrite = bool(data.get('overwrite', False))

        if not relative_dir or not filename or yaml_text is None:
            return jsonify({'error': 'relative_dir, filename and yaml are required'}), 400

        # prevent path traversal and force under /config
        base_config = pathlib.Path('/config').resolve()
        target_dir = (base_config / pathlib.Path(relative_dir)).resolve()
        if not str(target_dir).startswith(str(base_config)):
            return jsonify({'error': 'relative_dir must be under /config'}), 400

        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = (target_dir / filename).resolve()
        if not str(target_path).startswith(str(base_config)):
            return jsonify({'error': 'filename path escapes /config'}), 400

        if target_path.exists() and not overwrite:
            return jsonify({'error': 'file already exists', 'path': str(target_path)}), 409

        # Write temp then move
        temp_path = target_path.with_suffix(target_path.suffix + '.tmp')
        temp_path.write_text(yaml_text, encoding='utf-8')
        temp_path.replace(target_path)

        result = {
            'ok': True,
            'path': str(target_path),
            'validated': False,
            'reloaded': False
        }

        # Validate via Supervisor if requested and available
        if validate:
            sup_token = os.getenv('SUPERVISOR_TOKEN')
            try:
                if sup_token:
                    resp = requests.post(
                        'http://supervisor/core/api/config/core/check',
                        headers={'Authorization': f'Bearer {sup_token}'},
                        timeout=30
                    )
                    if resp.status_code != 200:
                        # revert by removing the new file
                        try:
                            target_path.unlink(missing_ok=True)
                        except Exception:
                            pass
                        return jsonify({'error': 'validation request failed', 'status': resp.status_code, 'body': resp.text}), 400
                    payload = resp.json()
                    result['validated'] = True
                    if not payload.get('result') == 'valid':
                        # revert on invalid
                        try:
                            target_path.unlink(missing_ok=True)
                        except Exception:
                            pass
                        return jsonify({'error': 'configuration invalid', 'details': payload}), 400
                else:
                    # No supervisor token; cannot validate
                    result['validated'] = False
            except Exception as e:
                try:
                    target_path.unlink(missing_ok=True)
                except Exception:
                    pass
                return jsonify({'error': 'validation error', 'details': str(e)}), 400

        # Reload core config if requested and validation passed or skipped
        if reload_core:
            sup_token = os.getenv('SUPERVISOR_TOKEN')
            if sup_token:
                try:
                    resp = requests.post(
                        'http://supervisor/core/api/services/homeassistant/reload_core_config',
                        headers={'Authorization': f'Bearer {sup_token}'},
                        timeout=30
                    )
                    result['reloaded'] = resp.status_code == 200
                except Exception:
                    result['reloaded'] = False
            else:
                result['reloaded'] = False

        return jsonify(result)
    except Exception as e:
        logger.error(f"ha_config_insert error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/ha_config/append_lines', methods=['POST'])
def ha_config_append_lines():
    """Append lines to /config/configuration.yaml with backup, validation and optional reload.

    Body JSON:
    {
      "lines": ["homeassistant:", "  packages: !include_dir_merge_named packages"],
      "validate": true,
      "reload_core": true,
      "backup": true
    }
    """
    try:
        data = request.get_json(force=True, silent=False)
        if not data:
            return jsonify({'error': 'JSON body required'}), 400

        lines = data.get('lines', [])
        validate = bool(data.get('validate', True))
        reload_core = bool(data.get('reload_core', True))
        do_backup = bool(data.get('backup', True))

        if not isinstance(lines, list) or not lines:
            return jsonify({'error': 'lines must be a non-empty array of strings'}), 400

        config_path = pathlib.Path('/config/configuration.yaml').resolve()
        if not config_path.exists():
            return jsonify({'error': 'configuration.yaml not found'}), 404

        backup_path = None
        if do_backup:
            backup_dir = pathlib.Path('/config/.backup')
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            backup_path = backup_dir / f'configuration.yaml.{timestamp}'
            try:
                shutil.copy2(str(config_path), str(backup_path))
            except Exception as e:
                return jsonify({'error': f'backup failed: {e}'}), 500

        try:
            with open(config_path, 'a', encoding='utf-8') as f:
                if not str(lines[-1]).endswith('\n'):
                    # ensure trailing newline on file before appending
                    f.write('\n')
                f.write('\n'.join(str(l) for l in lines))
                f.write('\n')
        except Exception as e:
            return jsonify({'error': f'append failed: {e}'}), 500

        result = {
            'ok': True,
            'path': str(config_path),
            'backup_path': str(backup_path) if backup_path else None,
            'validated': False,
            'reloaded': False
        }

        if validate:
            sup_token = os.getenv('SUPERVISOR_TOKEN')
            try:
                if sup_token:
                    resp = requests.post(
                        'http://supervisor/core/api/config/core/check',
                        headers={'Authorization': f'Bearer {sup_token}'},
                        timeout=30
                    )
                    if resp.status_code != 200:
                        # restore backup if we have it
                        if backup_path:
                            try:
                                shutil.copy2(str(backup_path), str(config_path))
                            except Exception:
                                pass
                        return jsonify({'error': 'validation request failed', 'status': resp.status_code, 'body': resp.text}), 400
                    payload = resp.json()
                    result['validated'] = True
                    if not payload.get('result') == 'valid':
                        if backup_path:
                            try:
                                shutil.copy2(str(backup_path), str(config_path))
                            except Exception:
                                pass
                        return jsonify({'error': 'configuration invalid', 'details': payload}), 400
                else:
                    result['validated'] = False
            except Exception as e:
                if backup_path:
                    try:
                        shutil.copy2(str(backup_path), str(config_path))
                    except Exception:
                        pass
                return jsonify({'error': 'validation error', 'details': str(e)}), 400

        if reload_core:
            sup_token = os.getenv('SUPERVISOR_TOKEN')
            if sup_token:
                try:
                    resp = requests.post(
                        'http://supervisor/core/api/services/homeassistant/reload_core_config',
                        headers={'Authorization': f'Bearer {sup_token}'},
                        timeout=30
                    )
                    result['reloaded'] = resp.status_code == 200
                except Exception:
                    result['reloaded'] = False
            else:
                result['reloaded'] = False

        return jsonify(result)
    except Exception as e:
        logger.error(f"ha_config_append_lines error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db_status = "unknown"
        try:
            ha_db.get_tables()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database_path': ha_db.db_path,
            'database_status': db_status,
            'addon_version': '1.0.0',
            'external_access_enabled': config.enable_external_access,
            'websocket_enabled': config.enable_websocket
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/tables', methods=['GET'])
def get_tables():
    """Get list of all tables in the database"""
    try:
        tables = ha_db.get_tables()
        return jsonify({
            'tables': tables,
            'count': len(tables)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/schema/<table_name>', methods=['GET'])
def get_table_schema(table_name: str):
    """Get schema information for a specific table"""
    try:
        schema = ha_db.get_table_schema(table_name)
        return jsonify({
            'table': table_name,
            'schema': schema
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/query', methods=['POST'])
def execute_query():
    """Execute a custom SQL query"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        params = data.get('params', [])
        
        # Validate query safety
        validation = validate_query_safety(query)
        if not validation['allowed']:
            return jsonify({'error': validation['reason']}), 400
        
        results = ha_db.execute_query(query, tuple(params))
        
        return jsonify({
            'query': query,
            'params': params,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/query', methods=['GET'])
def execute_query_get():
    """Execute a custom SQL query via GET (for simple queries)"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
        
        # Validate query safety
        validation = validate_query_safety(query)
        if not validation['allowed']:
            return jsonify({'error': validation['reason']}), 400
        
        results = ha_db.execute_query(query)
        
        return jsonify({
            'query': query,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/states', methods=['GET'])
def get_states():
    """Get recent states from the states table"""
    try:
        limit = request.args.get('limit', 100, type=int)
        entity_id = request.args.get('entity_id')
        
        if entity_id:
            query = "SELECT * FROM states WHERE entity_id = ? ORDER BY last_updated DESC LIMIT ?"
            params = (entity_id, limit)
        else:
            query = "SELECT * FROM states ORDER BY last_updated DESC LIMIT ?"
            params = (limit,)
        
        results = ha_db.execute_query(query, params)
        return jsonify({
            'states': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/events', methods=['GET'])
def get_events():
    """Get recent events from the events table"""
    try:
        limit = request.args.get('limit', 100, type=int)
        event_type = request.args.get('event_type')
        
        if event_type:
            query = "SELECT * FROM events WHERE event_type = ? ORDER BY time_fired DESC LIMIT ?"
            params = (event_type, limit)
        else:
            query = "SELECT * FROM events ORDER BY time_fired DESC LIMIT ?"
            params = (limit,)
        
        results = ha_db.execute_query(query, params)
        return jsonify({
            'events': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/entities', methods=['GET'])
def get_entities():
    """Get list of unique entities from the states table"""
    try:
        query = "SELECT DISTINCT entity_id FROM states ORDER BY entity_id"
        results = ha_db.execute_query(query)
        entities = [row['entity_id'] for row in results]
        
        return jsonify({
            'entities': entities,
            'count': len(entities)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Background task for monitoring database changes
def monitor_database():
    """Background task to monitor database changes"""
    while True:
        try:
            ha_db.check_for_changes()
            eventlet.sleep(5)  # Check every 5 seconds
        except Exception as e:
            logger.error(f"Error in database monitoring: {e}")
            eventlet.sleep(10)

if __name__ == '__main__':
    logger.info(f"Starting Home Assistant Database Query Addon on port {config.port}")
    logger.info(f"Database path: {db_path}")
    logger.info(f"External access enabled: {config.enable_external_access}")
    logger.info(f"WebSocket enabled: {config.enable_websocket}")
    
    if config.enable_websocket:
        # Start background task for database monitoring
        eventlet.spawn(monitor_database)
    
    # Run with SocketIO for WebSocket support
    socketio.run(
        app,
        host="0.0.0.0",
        port=config.port,
        debug=False,
        use_reloader=False
    )