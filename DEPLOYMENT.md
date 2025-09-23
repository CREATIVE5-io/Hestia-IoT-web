# Hestia Info Deployment Guide

This guide provides step-by-step instructions for deploying the Hestia Info application on Mac OS, Linux, and Windows.

## Prerequisites

Before deploying, ensure you have:
- Python 3.8 or higher
- NTN dongle hardware
- USB serial connection
- Network connectivity

## Quick Start

1. Clone or download the application
2. Install dependencies
3. Configure serial interface
4. Run the application

---

## Mac OS Deployment

### Step 1: Install Python
```bash
# Check if Python 3 is installed
python3 --version

# If not installed, install using Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python3
```

### Step 2: Install Dependencies
```bash
# Navigate to project directory
cd /path/to/hestia-info

# Install required packages
pip3 install -r requirements.txt

# If you encounter permission issues, use:
pip3 install --user -r requirements.txt
```

### Step 3: Configure Serial Interface
```bash
# Check connected USB devices
ls /dev/tty.*

# Common serial interfaces on Mac:
# /dev/tty.usbserial-*
# /dev/tty.usbmodem*

# Make the install script executable
chmod +x install.sh

# Run the installation script (optional)
./install.sh
```

### Step 4: Run the Application
```bash
# Start the application
python3 run.py

# Or make it executable and run directly
chmod +x run.py
./run.py
```

### Step 5: Access the Web Interface
Open your web browser and navigate to:
```
http://localhost:5001/hestia_info
```

---

## Linux Deployment

### Step 1: Install Python and Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL/Fedora
sudo yum install python3 python3-pip
# or
sudo dnf install python3 python3-pip

# Arch Linux
sudo pacman -S python python-pip
```

### Step 2: Install System Dependencies
```bash
# Install required system packages
sudo apt install python3-dev build-essential

# For serial communication
sudo apt install python3-serial

# Add user to dialout group (for serial access)
sudo usermod -a -G dialout $USER

# Log out and log back in, or run:
newgrp dialout
```

### Step 3: Set Up Virtual Environment (Recommended)
```bash
# Create virtual environment
python3 -m venv hestia-env

# Activate virtual environment
source hestia-env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure Serial Interface
```bash
# Check connected USB devices
lsusb

# Check serial interfaces
ls /dev/ttyUSB* /dev/ttyACM*

# Common serial interfaces on Linux:
# /dev/ttyUSB0
# /dev/ttyACM0

# Set permissions (if needed)
sudo chmod 666 /dev/ttyUSB0

# Run installation script
chmod +x install.sh
./install.sh
```

### Step 5: Run the Application
```bash
# With virtual environment activated
python run.py

# Or directly
python3 run.py

# Run in background
nohup python3 run.py > hestia.log 2>&1 &
```

### Step 6: Create Systemd Service (Optional)
```bash
# Create service file
sudo nano /etc/systemd/system/hestia-info.service
```

Add the following content:
```ini
[Unit]
Description=Hestia Info Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/hestia-info
Environment=PATH=/path/to/hestia-info/hestia-env/bin
ExecStart=/path/to/hestia-info/hestia-env/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable hestia-info
sudo systemctl start hestia-info

# Check status
sudo systemctl status hestia-info
```

---

## Windows Deployment

### Step 1: Install Python
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
```cmd
python --version
pip --version
```

### Step 2: Install Dependencies
```cmd
# Open Command Prompt or PowerShell
cd C:\path\to\hestia-info

# Install requirements
pip install -r requirements.txt

# If you encounter permission issues:
pip install --user -r requirements.txt
```

### Step 3: Configure Serial Interface
```cmd
# Check Device Manager for COM ports
# Look for "Ports (COM & LPT)" section
# Common interfaces: COM1, COM3, COM4, etc.

# You can also use PowerShell:
Get-WmiObject -Class Win32_SerialPort | Select-Object Name, DeviceID
```

### Step 4: Run the Application
```cmd
# Navigate to project directory
cd C:\path\to\hestia-info

# Run the application
python run.py

# Or double-click run.py if Python is associated with .py files
```

### Step 5: Create Windows Service (Optional)

#### Using NSSM (Non-Sucking Service Manager):
1. Download NSSM from [nssm.cc](https://nssm.cc/download)
2. Extract to a folder (e.g., C:\nssm)
3. Open Command Prompt as Administrator:

```cmd
# Install service
C:\nssm\nssm.exe install HestiaInfo

# Configure service
C:\nssm\nssm.exe set HestiaInfo Application C:\Python39\python.exe
C:\nssm\nssm.exe set HestiaInfo AppParameters C:\path\to\hestia-info\run.py
C:\nssm\nssm.exe set HestiaInfo AppDirectory C:\path\to\hestia-info

# Start service
C:\nssm\nssm.exe start HestiaInfo
```

### Step 6: Windows Firewall Configuration
```cmd
# Allow Python through Windows Firewall (run as Administrator)
netsh advfirewall firewall add rule name="Hestia Info" dir=in action=allow protocol=TCP localport=5001
```

---

## Configuration

### Serial Interface Configuration
1. Access the web interface
2. Go to "Serial Interface Configuration"
3. Set the correct serial port:
   - **Mac**: `/dev/tty.usbserial-*` or `/dev/tty.usbmodem*`
   - **Linux**: `/dev/ttyUSB0` or `/dev/ttyACM0`
   - **Windows**: `COM3`, `COM4`, etc.
4. Click "Save Serial Interface"

### Initial Setup
1. Start Hestia Info service
2. Wait for dongle initialization
3. Check NTN Status Details for connection status
4. Verify network details are populated

---

## Troubleshooting

### Common Issues

**Serial Port Access Denied (Linux/Mac)**:
```bash
# Add user to appropriate group
sudo usermod -a -G dialout $USER  # Linux
sudo usermod -a -G uucp $USER     # Some distributions

# Or change permissions temporarily
sudo chmod 666 /dev/ttyUSB0
```

**Python Module Not Found**:
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# Check if you're in the correct virtual environment
which python
```

**Port Already in Use**:
```bash
# Check what's using port 5001
# Linux/Mac:
lsof -i :5001

# Windows:
netstat -ano | findstr :5001

# Kill the process or change port in run.py
```

**Dongle Not Detected**:
1. Check USB connection
2. Verify driver installation
3. Try different USB port
4. Check Device Manager (Windows) or dmesg (Linux)

### Log Files
- Application logs: Check console output or redirect to file
- System logs:
  - **Linux**: `/var/log/syslog` or `journalctl -u hestia-info`
  - **Mac**: Console.app or `tail -f /var/log/system.log`
  - **Windows**: Event Viewer

---

## Performance Optimization

### System Requirements
- **RAM**: Minimum 512MB, Recommended 1GB+
- **CPU**: Any modern processor
- **Storage**: 100MB for application + logs
- **Network**: Ethernet or WiFi for web interface

### Production Deployment
1. Use a reverse proxy (nginx, Apache)
2. Configure SSL/TLS certificates
3. Set up log rotation
4. Configure automatic backups
5. Monitor system resources

---

## Security Considerations

1. **Change default passwords** if any
2. **Restrict network access** to the web interface
3. **Use HTTPS** in production
4. **Keep system updated**
5. **Monitor logs** for suspicious activity

---

## Support

For issues and support:
1. Check the troubleshooting section
2. Review log files
3. Verify hardware connections
4. Contact system administrator

---

## Quick Reference

### Default Configuration
- **Web Interface**: http://localhost:5001/hestia_info
- **Default Serial**: `/dev/ttyUSB0` (Linux), `COM3` (Windows)
- **Log Level**: INFO
- **Update Interval**: 5 seconds

### Key Files
- `run.py` - Main application entry point
- `requirements.txt` - Python dependencies
- `hestia_info.ini` - Configuration and data storage
- `temp_data_queue.json` - Transmission queue

### Service Management
```bash
# Linux (systemd)
sudo systemctl start|stop|restart|status hestia-info

# Windows (NSSM)
nssm start|stop|restart HestiaInfo
```