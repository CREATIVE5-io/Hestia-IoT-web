# 🚀 LoRa Setup - Quick Start Guide

## What is this?

This is a standalone LoRa device configuration application extracted from the SMG-Web project. It provides a clean web interface for:

- Configuring LoRa dongle settings (frequency, spreading factor, channel plan)
- Managing LoRa devices (add, delete, configure up to 16 devices)
- Real-time setup progress tracking
- NTN (Non-Terrestrial Network) dongle communication via REST API

## Quick Installation & Setup

### Option 1: Automatic Installation (Recommended)

```bash
# Make the install script executable and run it
chmod +x install.sh
./install.sh
```

### Option 2: Manual Installation

1. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Install and start Redis:**
   ```bash
   # On Ubuntu/Debian:
   sudo apt-get install redis-server
   sudo systemctl start redis-server
   
   # On macOS with Homebrew:
   brew install redis
   brew services start redis
   ```

3. **Create configuration directories:**
   ```bash
   mkdir -p ~/.smginfo ~/run
   ```

## Running the Application

1. **Start the application:**
   ```bash
   python3 run.py
   ```

2. **Open your browser and go to:**
   ```
   http://localhost:5001
   ```

## Testing the Installation

Run the test script to verify everything is working:

```bash
python3 test_app.py
```

## Configuration

You can customize the application using environment variables:

```bash
export SECRET_KEY="your-secret-key-here"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export FLASK_ENV="development"  # or "production" or "testing"
```

## Project Structure

```
lora-setup/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config/
│   │   └── settings.py          # Configuration settings
│   ├── models/
│   │   ├── config_manager.py    # Base configuration manager
│   │   ├── lora_manager.py      # LoRa-specific configuration
│   │   └── ntn_manager.py       # NTN dongle management
│   ├── routes/
│   │   ├── lora.py              # LoRa management routes
│   │   ├── lora_progress.py     # Progress tracking routes
│   │   └── ntn.py               # NTN API routes
│   └── utils/
│       ├── auth.py              # Authentication utilities (unused)
│       ├── celery_config.py     # Celery configuration
│       ├── logging_config.py    # Logging configuration
│       └── lora_setup.py        # LoRa setup utilities
├── static/
│   └── apple_style.css          # Stylesheet
├── templates/
│   └── lora.html                # Main LoRa configuration page
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
├── test_app.py                  # Test script
└── install.sh                   # Installation script
```

## Features Overview

### LoRa Dongle Configuration
- Set frequency, spreading factor (SF), and channel plan
- Real-time validation and saving

### Device Management
- Add up to 16 LoRa devices
- Configure device ID, type, keys, and transmission intervals
- Bulk delete and clear all devices
- Input validation for device IDs and keys

### Setup Progress
- Real-time progress tracking during device setup
- Error handling and timeout detection
- Visual progress indicators

### NTN API
- REST API endpoints for NTN dongle communication
- Device status monitoring
- Data transmission capabilities

## Troubleshooting

### Common Issues

1. **Redis Connection Error:**
   - Make sure Redis is installed and running
   - Check if Redis is listening on the default port (6379)

2. **Permission Errors:**
   - Ensure the application can create directories in `~/.smginfo` and `~/run`

3. **Port Already in Use:**
   - Change the port in `run.py` if 5001 is already in use

4. **Import Errors:**
   - Make sure all dependencies are installed: `pip3 install -r requirements.txt`

### Getting Help

If you encounter issues:
1. Run the test script: `python3 test_app.py`
2. Check the console output for error messages
3. Verify Redis is running: `redis-cli ping` (should return "PONG")

## What's Different from SMG-Web?

This project contains the LoRa and NTN functionality from SMG-Web:
- Removed APN, peripherals, and other modules
- No authentication system (direct access to functionality)
- Focused UI with LoRa configuration and NTN API
- Standalone operation (no dependencies on other SMG components)

Enjoy configuring your LoRa devices! 🚀