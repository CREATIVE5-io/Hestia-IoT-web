#!/usr/bin/env python3
"""
LoRa Setup Application Entry Point
"""
 
import os
from app import create_app
from app.config.settings import config

# Get configuration from environment
config_name = os.environ.get('FLASK_ENV', 'default')
app = create_app(config[config_name])

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=5001, debug=True)