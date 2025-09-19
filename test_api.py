#!/usr/bin/env python3
"""
Test script for Ferbos Mini Addon API
Tests all available endpoints and provides examples
"""

import requests
import json
import sys
from datetime import datetime

class FerbosAddonTester:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def test_endpoint(self, method, endpoint, data=None, params=None):
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=10)
            else:
                print(f"❌ Unsupported method: {method}")
                return None
            
            print(f"🔍 {method} {endpoint}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   ✅ Success: {len(str(result))} characters")
                    return result
                except json.JSONDecodeError:
                    print(f"   ✅ Success: {response.text[:100]}...")
                    return response.text
            else:
                print(f"   ❌ Error: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection Error: {e}")
            return None
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Testing Ferbos Mini Addon API")
        print("=" * 50)
        
        # Test 1: Health Check
        print("\n1️⃣ Health Check")
        health = self.test_endpoint('GET', '/health')
        
        if not health:
            print("❌ Health check failed. Is the addon running?")
            return False
        
        # Test 2: Get Tables
        print("\n2️⃣ Get Database Tables")
        tables = self.test_endpoint('GET', '/tables')
        
        # Test 3: Get Entities
        print("\n3️⃣ Get Entities")
        entities = self.test_endpoint('GET', '/entities')
        
        # Test 4: Get Recent States
        print("\n4️⃣ Get Recent States")
        states = self.test_endpoint('GET', '/states', params={'limit': 5})
        
        # Test 5: Get Recent Events
        print("\n5️⃣ Get Recent Events")
        events = self.test_endpoint('GET', '/events', params={'limit': 5})
        
        # Test 6: Get Table Schema (if tables exist)
        if tables and 'tables' in tables and tables['tables']:
            table_name = tables['tables'][0]
            print(f"\n6️⃣ Get Schema for Table: {table_name}")
            schema = self.test_endpoint('GET', f'/schema/{table_name}')
        
        # Test 7: Custom Query - Get all entities
        print("\n7️⃣ Custom Query - Get All Entities")
        custom_query = {
            "query": "SELECT DISTINCT entity_id FROM states ORDER BY entity_id LIMIT 10",
            "params": []
        }
        custom_result = self.test_endpoint('POST', '/query', data=custom_query)
        
        # Test 8: Custom Query - Get states with 'on' value
        print("\n8️⃣ Custom Query - Get 'On' States")
        on_query = {
            "query": "SELECT entity_id, state, last_updated FROM states WHERE state = ? ORDER BY last_updated DESC LIMIT 5",
            "params": ["on"]
        }
        on_result = self.test_endpoint('POST', '/query', data=on_query)
        
        # Test 9: Custom Query - Get sensor entities
        print("\n9️⃣ Custom Query - Get Sensor Entities")
        sensor_query = {
            "query": "SELECT entity_id, state FROM states WHERE entity_id LIKE ? ORDER BY entity_id LIMIT 10",
            "params": ["sensor.%"]
        }
        sensor_result = self.test_endpoint('POST', '/query', data=sensor_query)
        
        # Test 10: Get States for Specific Entity (if entities exist)
        if entities and 'entities' in entities and entities['entities']:
            entity_id = entities['entities'][0]
            print(f"\n🔟 Get States for Entity: {entity_id}")
            entity_states = self.test_endpoint('GET', '/states', params={'entity_id': entity_id, 'limit': 3})
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        return True
    
    def interactive_mode(self):
        """Interactive mode for custom queries"""
        print("\n🎯 Interactive Mode")
        print("Enter custom SQL queries (type 'quit' to exit)")
        print("Example: SELECT * FROM states WHERE entity_id = 'sensor.temperature' LIMIT 5")
        
        while True:
            try:
                query = input("\nSQL Query: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    continue
                
                # Basic validation
                if not query.upper().startswith('SELECT'):
                    print("❌ Only SELECT queries are allowed")
                    continue
                
                data = {"query": query, "params": []}
                result = self.test_endpoint('POST', '/query', data=data)
                
                if result and 'results' in result:
                    print(f"\n📊 Results ({result['count']} rows):")
                    for i, row in enumerate(result['results'][:5]):  # Show first 5 rows
                        print(f"   {i+1}: {row}")
                    
                    if result['count'] > 5:
                        print(f"   ... and {result['count'] - 5} more rows")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n👋 Interactive mode ended")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = input("Enter Home Assistant IP and port (e.g., http://192.168.1.100:8080): ").strip()
        if not base_url:
            base_url = "http://localhost:8080"
    
    if not base_url.startswith('http'):
        base_url = f"http://{base_url}"
    
    tester = FerbosAddonTester(base_url)
    
    print(f"🎯 Testing Ferbos Mini Addon at: {base_url}")
    
    # Run all tests
    if tester.run_all_tests():
        # Ask if user wants interactive mode
        try:
            interactive = input("\n🤔 Enter interactive mode? (y/n): ").strip().lower()
            if interactive in ['y', 'yes']:
                tester.interactive_mode()
        except KeyboardInterrupt:
            pass
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    main()
