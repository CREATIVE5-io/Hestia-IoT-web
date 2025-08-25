# 🚀 Hestia-Setup

A Flask web application for LoRa device configuration and management, extracted from the SMG-Web project. Provides a clean web interface for configuring LoRa dongles, managing devices, and communicating with NTN (Non-Terrestrial Network) dongles.

## Features

- **LoRa Dongle Configuration**: Set frequency, spreading factor (SF), channel plan, and serial interface
- **Device Management**: Add, delete, and configure up to 16 LoRa devices with validation
  - Device ID: 8 characters
  - Network Session Key: 32 characters
  - Application Session Key: 32 characters
- **Real-time Progress Tracking**: Monitor setup processes with live progress updates
- **NTN Dongle Communication**: REST API for NTN dongle status, device info, and data transmission
- **Background Processing**: Asynchronous task handling with Celery and Redis
- **Serial Communication**: Hardware integration using pyserial and modbus-tk
- **Clean Apple-style UI**: Modern, responsive web interface
- **Comprehensive Logging**: Detailed logging configuration for debugging and monitoring

## Quick Start

### Prerequisites

- Python 3.8+
- Redis server (for Celery task queue)

### Installation

#### Option 1: Automatic Installation (Recommended)

```bash
# Make the install script executable and run it
chmod +x install.sh
./install.sh
```

#### Option 2: Manual Installation

1. Clone or download this project
2. Install Python dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

3. Install and start Redis:
   ```bash
   # On Ubuntu/Debian:
   sudo apt-get install redis-server
   sudo systemctl start redis-server

   # On macOS with Homebrew:
   brew install redis
   brew services start redis
   ```

4. Create configuration directories:
   ```bash
   mkdir -p ~/.smginfo ~/run
   ```

### Running the Application

1. Start the application:
   ```bash
   python3 run.py
   ```

2. Open your browser and navigate to `http://localhost:5001`

### Testing

Run the test script to verify installation:

```bash
python3 test_app.py
```

## Configuration

You can customize the application by setting environment variables:

- `SECRET_KEY`: Flask secret key for sessions
- `CELERY_BROKER_URL`: Redis URL for Celery (default: redis://localhost:6379/0)
- `FLASK_ENV`: Application environment (development/production/testing)

## API Documentation

### NTN Dongle Endpoints

#### Get NTN Status
```
GET /api/ntn/status?type=NIDD
```
Returns the current status of the NTN dongle.

#### Get Device Information
```
GET /api/ntn/device
```
Returns NTN device information and configuration.

#### Send Data
```
POST /api/ntn/send
Content-Type: application/json

{
  "data": "your_data_here"
}
```
Sends data through the NTN dongle.

## Project Structure

```
hestia-setup/
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
│   └── apple_style.css          # Apple-style CSS
├── templates/
│   └── lora.html                # Main LoRa configuration page
├── logs/
│   └── lora-setup.log           # Application logs
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
├── test_app.py                  # Test script
├── install.sh                   # Installation script
├── QUICKSTART.md                # Detailed quick start guide
└── README.md                    # This file
```

## Usage

1. **Configure LoRa Dongle**: Set frequency, spreading factor, and channel plan
2. **Add Devices**: Configure LoRa devices with their IDs and keys (up to 16 devices)
3. **Setup LoRa Config**: Initialize LoRa dongle configuration
4. **Setup LoRa Devices**: Deploy device configurations to the dongle
5. **Monitor Progress**: Track setup progress in real-time
6. **NTN API**: Use REST API endpoints for NTN dongle communication

## Troubleshooting

### Common Issues

1. **Redis Connection Error:**
   - Make sure Redis is installed and running
   - Check if Redis is listening on the default port (6379)
   - Verify Redis service status: `redis-cli ping` (should return "PONG")

2. **Permission Errors:**
   - Ensure the application can create directories in `~/.smginfo` and `~/run`
   - Check file permissions for the project directory

3. **Port Already in Use:**
   - Change the port in `run.py` if 5001 is already in use
   - Find available ports: `netstat -tlnp | grep :5001`

4. **Import Errors:**
   - Make sure all dependencies are installed: `pip3 install -r requirements.txt`
   - Verify Python version is 3.8 or higher

5. **Serial Communication Issues:**
   - Check that LoRa/NTN dongles are properly connected
   - Verify serial interface paths (default: `/dev/ttyUSB0`)
   - Ensure proper permissions for serial device access

### Getting Help

If you encounter issues:
1. Run the test script: `python3 test_app.py`
2. Check the console output for error messages
3. Review application logs in the `logs/` directory
4. Verify Redis is running: `redis-cli ping`
5. Check system resources and port availability

## License

This project is derived from SMG-Web and maintains the same licensing terms.

**Last Updated**: September 2025
