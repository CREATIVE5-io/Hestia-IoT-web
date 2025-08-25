#!/usr/bin/env python3
"""
Simple test script for LoRa Setup Application
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from app import create_app
        from app.config.settings import config
        from app.models.lora_manager import LoRaConfigManager
        from app.utils.auth import check_credentials
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_creation():
    """Test that the Flask app can be created"""
    try:
        from app import create_app
        from app.config.settings import config
        
        app = create_app(config['testing'])
        print("✅ Flask app creation successful")
        return True
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False

def test_config_manager():
    """Test that the LoRa config manager works"""
    try:
        from app.models.lora_manager import LoRaConfigManager
        
        manager = LoRaConfigManager()
        lora_data = manager.get_lora_data()
        devices_data = manager.get_devices_data()
        
        print("✅ LoRa config manager working")
        print(f"   LoRa data keys: {list(lora_data.keys())}")
        print(f"   Devices count: {len(devices_data)}")
        return True
    except Exception as e:
        print(f"❌ Config manager error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing LoRa Setup Application...")
    print()
    
    tests = [
        ("Import Test", test_imports),
        ("App Creation Test", test_app_creation),
        ("Config Manager Test", test_config_manager),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application should work correctly.")
        print()
        print("🚀 To start the application:")
        print("   python3 run.py")
        print()
        print("🌐 Then open your browser and go to:")
        print("   http://localhost:5001")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()