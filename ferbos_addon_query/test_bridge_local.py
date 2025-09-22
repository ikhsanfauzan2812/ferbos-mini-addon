#!/usr/bin/env python3
"""
Test script for local bridge API
"""

import requests
import json

# Configuration
BRIDGE_URL = "http://localhost:8000/ws_bridge"
ADDON_URL = "http://localhost:8080"

def test_bridge_connection():
    """Test if bridge is running"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        print("✅ Bridge API is running")
        return True
    except Exception as e:
        print(f"❌ Bridge API not running: {e}")
        return False

def test_addon_connection():
    """Test if addon is running"""
    try:
        response = requests.get(f"{ADDON_URL}/ping", timeout=5)
        if response.status_code == 200:
            print("✅ Addon is running")
            return True
        else:
            print(f"❌ Addon returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Addon not running: {e}")
        return False

def test_bridge_addon_method():
    """Test bridge with addon method"""
    print("\n🧪 Testing bridge with addon method...")
    
    payload = {
        "ws_url": "wss://hijau001.ferbos-dev.com/api/websocket",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIwNmUxMzZjZWYxMDk0YzE1OTc1NzQzMGVkMTFlYzc0YiIsImlhdCI6MTc1ODUxMjI1MywiZXhwIjoyMDczODcyMjUzfQ.id2-OPcSslXiIpqjhPcPUB7h9Ps2bSyEXUjsaxH0HSo",
        "method": "ferbos/status",
        "args": {}
    }
    
    try:
        response = requests.post(BRIDGE_URL, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Bridge addon method test successful")
            return True
        else:
            print("❌ Bridge addon method test failed")
            return False
            
    except Exception as e:
        print(f"❌ Bridge addon method test error: {e}")
        return False

def test_bridge_ha_method():
    """Test bridge with Home Assistant method"""
    print("\n🧪 Testing bridge with HA method...")
    
    payload = {
        "ws_url": "wss://hijau001.ferbos-dev.com/api/websocket",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIwNmUxMzZjZWYxMDk0YzE1OTc1NzQzMGVkMTFlYzc0YiIsImlhdCI6MTc1ODUxMjI1MywiZXhwIjoyMDczODcyMjUzfQ.id2-OPcSslXiIpqjhPcPUB7h9Ps2bSyEXUjsaxH0HSo",
        "method": "states/get",
        "args": {}
    }
    
    try:
        response = requests.post(BRIDGE_URL, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Bridge HA method test successful")
            return True
        else:
            print("❌ Bridge HA method test failed")
            return False
            
    except Exception as e:
        print(f"❌ Bridge HA method test error: {e}")
        return False

def test_direct_addon():
    """Test addon directly"""
    print("\n🧪 Testing addon directly...")
    
    payload = {
        "method": "ferbos/status",
        "args": {},
        "token": "your-secure-api-key-here"
    }
    
    try:
        response = requests.post(f"{ADDON_URL}/ws_bridge", json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Direct addon test successful")
            return True
        else:
            print("❌ Direct addon test failed")
            return False
            
    except Exception as e:
        print(f"❌ Direct addon test error: {e}")
        return False

def main():
    print("🚀 Testing Local Bridge API Setup")
    print("=" * 50)
    
    # Test connections
    bridge_running = test_bridge_connection()
    addon_running = test_addon_connection()
    
    if not bridge_running:
        print("\n💡 To start the bridge API:")
        print("   python bridge_api_fixed.py")
        return
    
    if not addon_running:
        print("\n💡 Make sure your addon is running on localhost:8080")
        return
    
    # Test functionality
    print("\n" + "=" * 50)
    print("🧪 Running Tests...")
    
    # Test direct addon first
    direct_success = test_direct_addon()
    
    # Test bridge with addon method
    bridge_addon_success = test_bridge_addon_method()
    
    # Test bridge with HA method
    bridge_ha_success = test_bridge_ha_method()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Direct Addon: {'✅' if direct_success else '❌'}")
    print(f"   Bridge + Addon: {'✅' if bridge_addon_success else '❌'}")
    print(f"   Bridge + HA: {'✅' if bridge_ha_success else '❌'}")
    
    if all([direct_success, bridge_addon_success, bridge_ha_success]):
        print("\n🎉 All tests passed! Your bridge is ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Check the configuration and try again.")

if __name__ == "__main__":
    main()
