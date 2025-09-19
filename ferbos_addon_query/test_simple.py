#!/usr/bin/env python3
"""
Simple test version of the addon to verify basic functionality
"""

from flask import Flask, jsonify
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'Ferbos Mini Addon is running!',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'status': 'working'
    })

@app.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint"""
    return jsonify({
        'status': 'pong',
        'timestamp': datetime.now().isoformat(),
        'addon': 'Ferbos Mini Addon'
    })

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'test': 'success',
        'working_directory': os.getcwd(),
        'files_in_current_dir': os.listdir('.') if os.path.exists('.') else []
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    print(f"Starting simple test server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
