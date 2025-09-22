#!/usr/bin/env python3
"""
Test script for Ferbos Mini Addon External API
Demonstrates how to use the external API endpoints with authentication
"""

import requests
import json
import time
import socketio
from typing import Dict, Any

class FerbosAddonClient:
    """Client for interacting with Ferbos Mini Addon External API"""
    
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json'
        }
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
    
    def test_connection(self) -> Dict[str, Any]:
        """Test basic connection to the addon"""
        try:
            response = requests.get(f'{self.base_url}/ping', timeout=5)
            return {
                'status': 'success',
                'status_code': response.status_code,
                'data': response.json()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_external_status(self) -> Dict[str, Any]:
        """Get external status (requires authentication)"""
        try:
            response = requests.get(
                f'{self.base_url}/external/status',
                headers=self.headers,
                timeout=10
            )
            return {
                'status': 'success',
                'status_code': response.status_code,
                'data': response.json()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def execute_query(self, query: str, params: list = None) -> Dict[str, Any]:
        """Execute a SQL query via external API"""
        try:
            payload = {
                'query': query,
                'params': params or []
            }
            response = requests.post(
                f'{self.base_url}/external/query',
                headers=self.headers,
                json=payload,
                timeout=30
            )
            return {
                'status': 'success',
                'status_code': response.status_code,
                'data': response.json()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_entities(self) -> Dict[str, Any]:
        """Get list of entities via external API"""
        try:
            response = requests.get(
                f'{self.base_url}/external/entities',
                headers=self.headers,
                timeout=10
            )
            return {
                'status': 'success',
                'status_code': response.status_code,
                'data': response.json()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_states(self, limit: int = 10, entity_id: str = None) -> Dict[str, Any]:
        """Get states via external API"""
        try:
            params = {'limit': limit}
            if entity_id:
                params['entity_id'] = entity_id
            
            response = requests.get(
                f'{self.base_url}/external/states',
                headers=self.headers,
                params=params,
                timeout=10
            )
            return {
                'status': 'success',
                'status_code': response.status_code,
                'data': response.json()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

class FerbosWebSocketClient:
    """WebSocket client for real-time database monitoring"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.replace('http://', '').replace('https://', '')
        self.sio = socketio.Client()
        self.connected = False
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.sio.event
        def connect():
            print("✅ Connected to WebSocket")
            self.connected = True
        
        @self.sio.event
        def disconnect():
            print("❌ Disconnected from WebSocket")
            self.connected = False
        
        @self.sio.event
        def connected(data):
            print(f"📡 Server: {data['message']}")
        
        @self.sio.event
        def query_result(data):
            print(f"📊 Query result: {data['count']} rows")
            if data['count'] > 0:
                print("Sample result:", data['results'][0] if data['results'] else "No data")
        
        @self.sio.event
        def query_error(data):
            print(f"❌ Query error: {data['error']}")
        
        @self.sio.event
        def database_updated(data):
            print(f"🔄 Database updated: {data['message']}")
    
    def connect(self):
        """Connect to WebSocket"""
        try:
            self.sio.connect(f'http://{self.base_url}/ws')
            return True
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from WebSocket"""
        if self.connected:
            self.sio.disconnect()
    
    def execute_query(self, query: str):
        """Execute query via WebSocket"""
        if self.connected:
            self.sio.emit('query_database', {'query': query})
            print(f"📤 Sent query: {query}")
        else:
            print("❌ WebSocket not connected")
    
    def subscribe_entity(self, entity_id: str):
        """Subscribe to entity updates"""
        if self.connected:
            self.sio.emit('subscribe_entity', {'entity_id': entity_id})
            print(f"📡 Subscribed to entity: {entity_id}")
        else:
            print("❌ WebSocket not connected")

def run_tests():
    """Run comprehensive tests of the external API"""
    
    # Configuration
    BASE_URL = "http://localhost:8080"  # Change this to your Home Assistant IP
    API_KEY = "your-api-key-here"  # Set this to your configured API key
    
    print("🚀 Ferbos Mini Addon External API Test")
    print("=" * 50)
    
    # Initialize client
    client = FerbosAddonClient(BASE_URL, API_KEY)
    
    # Test 1: Basic connection
    print("\n1️⃣ Testing basic connection...")
    result = client.test_connection()
    if result['status'] == 'success':
        print(f"✅ Connection successful: {result['data']['status']}")
    else:
        print(f"❌ Connection failed: {result['error']}")
        return
    
    # Test 2: External status (requires authentication)
    print("\n2️⃣ Testing external status...")
    result = client.get_external_status()
    if result['status'] == 'success':
        print(f"✅ External status: {result['data']['status']}")
        print(f"   Database connected: {result['data']['database_connected']}")
        print(f"   WebSocket enabled: {result['data']['websocket_enabled']}")
    else:
        print(f"❌ External status failed: {result['error']}")
        if result.get('status_code') == 401:
            print("   💡 This might be due to missing or incorrect API key")
    
    # Test 3: Get entities
    print("\n3️⃣ Testing get entities...")
    result = client.get_entities()
    if result['status'] == 'success':
        entities = result['data']['entities']
        print(f"✅ Found {len(entities)} entities")
        if entities:
            print(f"   Sample entities: {entities[:5]}")
    else:
        print(f"❌ Get entities failed: {result['error']}")
    
    # Test 4: Get states
    print("\n4️⃣ Testing get states...")
    result = client.get_states(limit=5)
    if result['status'] == 'success':
        states = result['data']['states']
        print(f"✅ Found {len(states)} states")
        if states:
            print("   Sample states:")
            for state in states[:3]:
                print(f"     {state.get('entity_id', 'N/A')}: {state.get('state', 'N/A')}")
    else:
        print(f"❌ Get states failed: {result['error']}")
    
    # Test 5: Execute custom query
    print("\n5️⃣ Testing custom query...")
    query = "SELECT name FROM sqlite_master WHERE type='table' LIMIT 5"
    result = client.execute_query(query)
    if result['status'] == 'success':
        tables = result['data']['results']
        print(f"✅ Query executed successfully")
        print(f"   Found {len(tables)} tables")
        if tables:
            table_names = [table['name'] for table in tables]
            print(f"   Tables: {table_names}")
    else:
        print(f"❌ Custom query failed: {result['error']}")
    
    # Test 6: WebSocket connection
    print("\n6️⃣ Testing WebSocket connection...")
    ws_client = FerbosWebSocketClient(BASE_URL)
    if ws_client.connect():
        time.sleep(2)  # Wait for connection
        
        # Test WebSocket query
        print("   Testing WebSocket query...")
        ws_client.execute_query("SELECT COUNT(*) as table_count FROM sqlite_master WHERE type='table'")
        time.sleep(2)  # Wait for result
        
        # Test entity subscription
        print("   Testing entity subscription...")
        ws_client.subscribe_entity("sensor.temperature")
        time.sleep(1)
        
        # Disconnect
        ws_client.disconnect()
    else:
        print("❌ WebSocket connection failed")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    print("\n💡 Tips:")
    print("   - Make sure the addon is running and accessible")
    print("   - Configure API key in addon options if using authentication")
    print("   - Check firewall settings if connection fails")
    print("   - Use the web interface at http://your-ha-ip:8080 for interactive testing")

if __name__ == "__main__":
    run_tests()
