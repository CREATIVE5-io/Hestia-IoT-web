#!/bin/bash

# LoRa Setup Installation Script

echo "🚀 Installing LoRa Setup Application..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

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

# Create necessary directories
echo "📁 Creating configuration directories..."
mkdir -p ~/.smginfo
mkdir -p ~/run

echo "✅ Installation completed successfully!"
echo ""
echo "🚀 To start the application:"
echo "   python3 run.py"
echo ""
echo "🌐 Then open your browser and go to:"
echo "   http://localhost:5001"
echo ""
echo "📝 Note: No authentication required - direct access to LoRa configuration"