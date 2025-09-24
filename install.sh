#!/bin/bash

# LoRa Setup Installation Script

echo "🚀 Installing LoRa Setup Application..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Check if Python 3 is available in venv
if ! command -v python &> /dev/null; then
    echo "❌ Python 3 is not available in virtual environment."
    exit 1
fi

# Check if pip is available in venv
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not available in virtual environment."
    exit 1
fi

# Install Python dependencies in venv
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "⚠️  Redis is not installed. Installing Redis..."
    
    # Detect OS and install Redis
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y redis-server
        elif command -v yum &> /dev/null; then
            sudo yum install -y redis
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y redis
        else
            echo "❌ Unable to install Redis automatically. Please install Redis manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install redis
        else
            echo "❌ Homebrew not found. Please install Redis manually or install Homebrew first."
            exit 1
        fi
    else
        echo "❌ Unsupported OS. Please install Redis manually."
        exit 1
    fi
fi

# Start Redis service
echo "🔄 Starting Redis service..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew services start redis
fi

# Create and start application service
echo "🔄 Setting up application service..."
PROJECT_DIR=$(pwd)
USER=$(whoami)

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Create systemd service file
    SERVICE_FILE="/etc/systemd/system/hestia-iot-web.service"
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Hestia IoT Web Service
After=network.target redis-server.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/.venv/bin/python $PROJECT_DIR/run.py
Restart=always
Environment=FLASK_ENV=production

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd, enable and start service
    sudo systemctl daemon-reload
    sudo systemctl enable hestia-iot-web.service
    sudo systemctl start hestia-iot-web.service

elif [[ "$OSTYPE" == "darwin"* ]]; then
    # Create launchd plist
    PLIST_FILE="$HOME/Library/LaunchAgents/com.hestia-iot-web.plist"
    mkdir -p "$HOME/Library/LaunchAgents"
    cat > "$PLIST_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hestia-iot-web</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/.venv/bin/python</string>
        <string>$PROJECT_DIR/run.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>FLASK_ENV</key>
        <string>production</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/hestia-iot-web.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/hestia-iot-web.log</string>
</dict>
</plist>
EOF

    # Load and start the service
    launchctl load "$PLIST_FILE"
    launchctl start com.hestia-iot-web
fi

echo ""
echo "🔧 Service management commands:"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "   To stop the service: sudo systemctl stop hestia-iot-web.service"
    echo "   To restart the service: sudo systemctl restart hestia-iot-web.service"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   To unload the service: launchctl unload $PLIST_FILE"
    echo "   To load the service: launchctl load $PLIST_FILE"
    echo "   To restart the service: launchctl unload $PLIST_FILE && launchctl load $PLIST_FILE"
fi


echo "✅ Installation completed successfully!"
echo ""
echo "🌐 The application is now running as a service."
echo "   Open your browser and go to:"
echo "   http://localhost:5001"
echo ""
echo "📝 Note: No authentication required - direct access to LoRa configuration"
echo ""
echo "🔄 To check service status:"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "   sudo systemctl status hestia-iot-web.service"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   launchctl list | grep hestia-iot-web"
fi
