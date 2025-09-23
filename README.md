# Hestia Info - NTN Network Monitoring System

A comprehensive Python-based web application for monitoring and managing Hestia NTN (Non-Terrestrial Network) devices with real-time data visualization, automatic transmission queuing, and bi-directional message handling.

## 🚀 Features

### Real-Time Monitoring
- **NTN Status Components** - Live LED indicators for module status (NIDD/UDP modes)
- **Network Details** - IMSI, RSRP, SINR, GPS coordinates with auto-refresh
- **LoRa Device Information** - Device status and communication data
- **Dual Message Display** - Side-by-side uplink queue and downlink message logs

### LoRa Configuration & Management
- **LoRa Dongle Configuration** - Set frequency, spreading factor (SF), channel plan
- **Device Management** - Add, delete, and configure up to 16 LoRa devices
- **Real-time Setup Progress** - Monitor LoRa configuration with live progress updates
- **Device Validation** - Input validation for device IDs and keys
- **Bulk Operations** - Setup multiple devices simultaneously

### Data Management
- **NetworkInfo Data Capture** - Manual capture of network measurements
- **Automatic Queue Processing** - Background transmission with retry logic
- **Smart Triggering** - Auto-capture on specific downlink message keys
- **File-Based Queue** - Persistent data storage with file locking

### Communication Features
- **Bi-directional Messaging** - Both uplink transmission and downlink reception
- **Status-Aware Transmission** - Checks module readiness before sending
- **Message History** - Last 3 messages for both uplink and downlink
- **Queue Visibility** - Real-time view of pending transmissions

### Configuration & Management
- **Serial Interface Configuration** - Dynamic port configuration
- **Service Control** - Start/stop NTN monitoring services
- **Message Management** - Clear individual message types
- **Multi-Platform Support** - Mac OS, Linux, and Windows compatibility

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface (Flask)                    │
├─────────────────────────────────────────────────────────────┤
│ Hestia Info Page        │        LoRa Setup Page           │
│ ┌─────────────────────┐ │ ┌─────────────────────────────────┐ │
│ │ NTN Status │Network │ │ │ LoRa Config │ Device Mgmt     │ │
│ │ LED Status │Details │ │ │ Frequency   │ Add/Delete      │ │
│ │ Uplink Q   │Downlink│ │ │ Spread Fact │ Setup Progress  │ │
│ └─────────────────────┘ │ └─────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│              Background Services                            │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ Data Collection │  │ Upload Worker   │                  │
│  │ Thread          │  │ Thread          │                  │
│  └─────────────────┘  └─────────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│                Hardware Interface                          │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ NTN Dongle      │  │ LoRa Module     │                  │
│  │ (Modbus RTU)    │  │ (AT Commands)   │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Requirements

- **Python 3.8+**
- **Hardware**: NTN dongle with Modbus RTU interface
- **Connectivity**: USB serial connection
- **Platform**: Mac OS, Linux, or Windows

## 🚀 Quick Start

1. **Clone the repository:**
```bash
git clone <repository-url>
cd hestia-info
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
python run.py
```

4. **Access the web interface:**
```
# Hestia Info (NTN Monitoring)
http://localhost:5001/hestia_info

# LoRa Setup (Device Configuration)
http://localhost:5001/lora
```

## 📖 Detailed Setup

For complete deployment instructions including service setup, troubleshooting, and platform-specific configurations, see [DEPLOYMENT.md](DEPLOYMENT.md).

## 🎛️ Usage Guide

### Initial Configuration
1. **Configure Serial Interface**
   - Set the correct serial port for your system
   - Common ports: `/dev/ttyUSB0` (Linux), `COM3` (Windows), `/dev/tty.usbserial-*` (Mac)

2. **Configure LoRa Devices** (http://localhost:5001/lora)
   - Set frequency, spreading factor, and channel plan
   - Add up to 16 LoRa devices with validation
   - Run "LoRa Config Setup" and "LoRa Devices Setup"

3. **Start Hestia Info Service** (http://localhost:5001/hestia_info)
   - Click "Start Hestia Info" to begin monitoring
   - Watch LED indicators for connection status

### Monitoring Features

#### NTN Status Components
- **Real-time LED indicators** showing module readiness
- **Service Mode Detection** - Automatically switches between NIDD/UDP indicators
- **Status Categories**:
  - Module AT Ready
  - IP Ready / Downlink Ready (mode-dependent)
  - SIM Ready
  - Network Registered
  - Socket Ready (UDP mode only)
  - All Ready

#### Network Information
- **Live Data**: IMSI, RSRP, SINR, GPS coordinates
- **Manual Capture**: Click "Capture NetworkInfo Data" to queue current measurements
- **Auto-refresh**: Updates every 5 seconds

### Message Management

#### Uplink Messages (Pending Queue)
- **Queue Visibility**: Shows next 3 items waiting for transmission
- **Status Tracking**: PENDING with queue position
- **Smart Transmission**: Only sends when module is ready
- **Queue Management**: Clear entire queue if needed

#### Downlink Messages
- **Automatic Logging**: All received messages with timestamps
- **Decoded Content**: Shows both hex and readable JSON data
- **Auto-Triggering**: Messages with `timeperiods` or `gpstype` keys trigger data capture
- **Message History**: Last 3 received messages

### Data Capture Modes

#### Manual Capture
```json
// Captured at 2025-09-19 15:23:45
{"m": [latitude, longitude, rsrp, sinr]}
```

#### Auto-Capture (Downlink Triggered)
```json
// Auto-captured from downlink at 2025-09-19 15:24:12
{"D": [{"data": {"timeperiods": 300}}]}
```

## 🔧 LoRa Configuration

### LoRa Setup Page Features
Access the LoRa configuration at `http://localhost:5001/lora`

#### Dongle Configuration
- **Serial Interface**: Configure communication port
- **Frequency**: Set operating frequency (9 digits)
- **Spreading Factor**: Choose SF 7-12
- **Channel Plan**: Select region (AS923, US915, AU915, EU868, KR920, IN865, RU864)

#### Device Management
- **Add Devices**: Configure up to 16 LoRa devices
  - Device Index: 0-15
  - Device ID: 8 characters
  - Network Session Key: 32 characters
  - Application Session Key: 32 characters
  - Transmit Interval: Configurable timing

#### Setup Operations
- **LoRa Config Setup**: Initialize dongle with frequency and settings
- **LoRa Devices Setup**: Deploy all configured devices to dongle
- **Real-time Progress**: Monitor setup progress with live updates
- **Error Handling**: View setup status and failed device reports

#### Device Operations
- **Bulk Selection**: Select multiple devices for deletion
- **Validation**: Automatic input validation for all fields
- **Status Tracking**: Monitor device deployment success/failure

## 🔧 Configuration Files

- **`hestia_info.ini`** - Main configuration and cached data
- **`temp_data_queue.json`** - Transmission queue (auto-managed)
- **`requirements.txt`** - Python dependencies

## 🛠️ Development

### Project Structure
```
hestia-info/
├── app/
│   ├── models/          # Data models and managers
│   ├── routes/          # Flask route handlers
│   └── utils/           # Utility functions
├── templates/           # HTML templates
├── static/             # CSS and static assets
├── run.py              # Application entry point
└── requirements.txt    # Dependencies
```

### Key Components
- **HestiaInfoManager** - Configuration and data management
- **Upload Worker Thread** - Background transmission processing
- **Real-time Updates** - JavaScript auto-refresh system
- **File Locking** - Thread-safe queue operations

## 🐛 Troubleshooting

### Common Issues

**Serial Port Access Denied:**
```bash
# Linux/Mac
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB0

# Windows: Run as Administrator or check Device Manager
```

**Module Not Ready:**
- Check LED indicators in NTN Status Components
- Ensure all components show green (ready) status
- Verify SIM card and antenna connections

**Queue Not Processing:**
- Check "Upload worker thread started" in logs
- Verify `all_ready` status is true
- Ensure `is_upload_available()` returns true

**Web Interface Not Loading:**
- Check if port 5001 is available
- Verify Python dependencies are installed
- Check console output for error messages

## 📊 Monitoring & Logging

### Log Levels
- **INFO**: Normal operation, status updates
- **WARNING**: Transmission failures, retries
- **ERROR**: System errors, connection issues
- **DEBUG**: Detailed operation traces

### Key Metrics
- **Queue Length**: Number of pending transmissions
- **Success Rate**: Transmission success/failure ratio
- **Response Time**: Network measurement intervals
- **Connection Status**: Module readiness indicators

## 🔒 Security Considerations

- **Network Access**: Restrict web interface access
- **Serial Permissions**: Ensure proper user group membership
- **Data Privacy**: Network measurements may contain sensitive location data
- **Service Security**: Run with minimal required privileges

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup
- **Issues**: Check troubleshooting section above
- **Hardware**: Verify NTN dongle compatibility and drivers

---

## 🎯 Quick Reference

### Default Settings
- **Hestia Info Interface**: http://localhost:5001/hestia_info
- **LoRa Setup Interface**: http://localhost:5001/lora
- **Update Interval**: 5 seconds (Hestia Info)
- **Queue Size**: 3 pending messages displayed
- **Message History**: 3 messages per type
- **Max LoRa Devices**: 16 devices per dongle

### Service Commands

#### Hestia Info Operations
```bash
# Start NTN monitoring
Click "Start Hestia Info" button

# Capture current data
Click "Capture NetworkInfo Data" button

# Clear message queues
Click "Clear Queue" or "Clear Downlink" buttons
```

#### LoRa Setup Operations
```bash
# Configure LoRa dongle
Click "LoRa Config Setup" button

# Deploy devices to dongle
Click "LoRa Devices Setup" button

# Add new device
Fill form and click "Add Device"

# Remove devices
Select devices and click "Delete Selected"
```

