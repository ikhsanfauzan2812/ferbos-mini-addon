#!/usr/bin/env python3
"""
Startup script for the bridge API
"""

import uvicorn
import sys
import os

def main():
    print("🚀 Starting Bridge API...")
    print("📍 Bridge will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "bridge_api_fixed:app",
            host="0.0.0.0",
            port=8000,
            reload=True,  # Auto-reload on code changes
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Bridge API stopped")
    except Exception as e:
        print(f"❌ Error starting bridge API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
