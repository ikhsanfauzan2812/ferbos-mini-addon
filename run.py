#!/usr/bin/env python3
"""
Home Assistant Database Query Addon
Provides HTTP API endpoints to query the Home Assistant database
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class HomeAssistantDB:
    """Handle Home Assistant database operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """Ensure the database file exists and is accessible"""
        if not os.path.exists(self.db_path):
            logger.warning(f"Database file not found at {self.db_path}")
            # Create a minimal database structure for testing
            self.create_test_db()
    
    def create_test_db(self):
        """Create a minimal test database structure"""
        try:
            conn = sqlite3.connect(self.db_path)
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
            
            conn.commit()
            conn.close()
            logger.info("Created test database structure")
        except Exception as e:
            logger.error(f"Error creating test database: {e}")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as list of dictionaries"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to list of dictionaries
            results = []
            for row in rows:
                results.append(dict(row))
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise
    
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
db_path = os.getenv('DATABASE_PATH', '/config/home_assistant_v2.db')
ha_db = HomeAssistantDB(db_path)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database_path': db_path,
        'database_exists': os.path.exists(db_path)
    })

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
        
        # Basic security check - only allow SELECT queries
        if not query.strip().upper().startswith('SELECT'):
            return jsonify({'error': 'Only SELECT queries are allowed'}), 400
        
        results = ha_db.execute_query(query, tuple(params))
        
        return jsonify({
            'query': query,
            'params': params,
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting Home Assistant Database Query Addon on port {port}")
    logger.info(f"Database path: {db_path}")
    
    # Run with uvicorn for better performance
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
