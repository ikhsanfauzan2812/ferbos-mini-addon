#!/usr/bin/env python3
"""
Quick script to find and test your addon
"""

import requests
import sys

def test_addon_url(url):
    """Test if addon is accessible at given URL"""
    try:
        response = requests.get(f"{url}/ping", timeout=5)
        if response.status_code == 200:
            print(f"✅ Addon found at: {url}")
            return True
        else:
            print(f"❌ Addon at {url} returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Addon at {url} not accessible: {e}")
        return False

def main():
    print("🔍 Searching for your addon...")
    print("=" * 50)
    
    # Common IP addresses to test (based on your network 192.168.68.x)
    common_ips = [
        "localhost",
        "127.0.0.1",
        "192.168.68.1",    # Your gateway
        "192.168.68.100",
        "192.168.68.101",
        "192.168.68.102",
        "192.168.68.103",
        "192.168.68.104",
        "192.168.68.105",
        "192.168.68.110",
        "192.168.68.120",
        "192.168.68.130",
        "192.168.68.140",
        "192.168.68.150",
        "192.168.68.160",
        "192.168.68.170",
        "192.168.68.180",
        "192.168.68.190",
        "192.168.68.200"
    ]
    
    # Common ports to test
    common_ports = [8080, 8081, 8082, 3000, 5000]
    
    found_addons = []
    
    for ip in common_ips:
        for port in common_ports:
            url = f"http://{ip}:{port}"
            if test_addon_url(url):
                found_addons.append(url)
    
    print("\n" + "=" * 50)
    if found_addons:
        print("🎉 Found addon(s):")
        for addon_url in found_addons:
            print(f"   {addon_url}")
        
        print(f"\n💡 Update your bridge configuration:")
        print(f"   ADDON_BASE_URL = \"{found_addons[0]}\"")
    else:
        print("❌ No addon found. Make sure:")
        print("   1. Your addon is running in Home Assistant")
        print("   2. External access is enabled")
        print("   3. The port is correct (usually 8080)")
        print("   4. Your Home Assistant is accessible from this machine")

if __name__ == "__main__":
    main()
