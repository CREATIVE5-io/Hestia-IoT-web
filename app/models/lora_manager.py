"""
LoRa device management models
"""

import configparser
import logging
import os
from app.models.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class LoRaConfigManager(ConfigManager):
    """LoRa configuration manager"""
    
    def __init__(self):
        super().__init__()
        self.lora_file = os.path.join(self.run_dir, 'lora.ini')
        logger.debug(f"LoRa configuration file: {self.lora_file}")
    
    def read_lora_config(self):
        """Read LoRa configuration"""
        config = configparser.ConfigParser()
        if os.path.exists(self.lora_file):
            config.read(self.lora_file)
       
        if 'NTN-DONGLE' not in config:
            config['NTN-DONGLE'] = {
                'serial_interface': '/dev/ttyUSB0',
                'dongle_id': ''
            }
            
        if 'LORA' not in config:
            config['LORA'] = {
                'frequency': '',
                'sf': '',
                'ch_plan': '',
                'registered_status': 'no'
            }
        
        if 'DEVICES' not in config:
            config['DEVICES'] = {}
        
        self.save_lora_config(config)
        return config
    
    def save_lora_config(self, config):
        """Save LoRa configuration"""
        with open(self.lora_file, 'w') as configfile:
            config.write(configfile)
   
    def get_dongle_info(self):
        """Get LoRa dongle information"""
        config = self.read_lora_config()
        dongle_info = {
            'serial_interface': config['NTN-DONGLE'].get('serial_interface', '/dev/ttyUSB0'),
            'dongle_id': config['NTN-DONGLE'].get('dongle_id', ''),
        }
        logger.debug(f"Dongle info: {dongle_info}")
        return dongle_info
    
    def get_lora_data(self):
        """Get LoRa dongle data"""
        config = self.read_lora_config()
        data = {
            'frequency': config['LORA'].get('frequency', ''),
            'sf': config['LORA'].get('sf', ''),
            'ch_plan': config['LORA'].get('ch_plan', ''),
            'serial_interface': config['NTN-DONGLE'].get('serial_interface', '/dev/ttyUSB0'),
            'dongle_id': config['NTN-DONGLE'].get('dongle_id', '')
        }
        logger.debug(f"LoRa data: {data}")
        return data
    
    def get_devices_data(self):
        """Get LoRa devices data"""
        config = self.read_lora_config()
        devices = {}
        for key, value in config['DEVICES'].items():
            if key.endswith('_id'):
                dev_num = key.replace('device', '').replace('_id', '')
                devices[dev_num] = {
                    'idx': config['DEVICES'].get(f'device{dev_num}_idx', '0'),
                    'id': value,
                    'nsKey': config['DEVICES'].get(f'device{dev_num}_ns_key', ''),
                    'appKey': config['DEVICES'].get(f'device{dev_num}_app_key', ''),
                    'transmit_interval': config['DEVICES'].get(f'device{dev_num}_ti', ''),
                }
        return devices
    
    def update_lora_settings(self, frequency, sf, ch_plan, serial_interface=None):
        """Update LoRa dongle settings"""
        config = self.read_lora_config()
        config['LORA']['frequency'] = frequency
        config['LORA']['sf'] = sf
        config['LORA']['ch_plan'] = ch_plan
        if serial_interface is not None:
            if 'NTN-DONGLE' not in config:
                config['NTN-DONGLE'] = {}
            config['NTN-DONGLE']['serial_interface'] = serial_interface
        self.save_lora_config(config)
    
    def add_device(self, device_data):
        """Add a new LoRa device"""
        config = self.read_lora_config()
        devices = {k: v for k, v in config['DEVICES'].items() if k.endswith('_id')}
        
        if len(devices) >= 16:
            return False, "Maximum of 16 devices reached"
        
        # Check for duplicate index
        existing_idx = [config['DEVICES'].get(f'device{i}_idx', '') 
                       for i in range(1, 17) if f'device{i}_idx' in config['DEVICES']]
        
        if device_data['idx'] in existing_idx:
            return False, f"Device index {device_data['idx']} is already in use"
        
        # Validate device data
        if len(device_data['id']) != 8:
            return False, "Device ID must be exactly 8 characters long"
        if len(device_data['ns_key']) != 32:
            return False, "Network Section Key must be exactly 32 characters long"
        if len(device_data['app_key']) != 32:
            return False, "Application Section Key must be exactly 32 characters long"
        
        # Add device
        dev_num = len(devices) + 1
        config['DEVICES'][f'device{dev_num}_idx'] = device_data['idx']
        config['DEVICES'][f'device{dev_num}_id'] = device_data['id']
        config['DEVICES'][f'device{dev_num}_ns_key'] = device_data['ns_key']
        config['DEVICES'][f'device{dev_num}_app_key'] = device_data['app_key']
        config['DEVICES'][f'device{dev_num}_ti'] = device_data['transmit_interval']
        
        self.save_lora_config(config)
        return True, "Device added successfully"
    
    def delete_devices(self, device_nums):
        """Delete LoRa devices"""
        config = self.read_lora_config()
        for device_num in device_nums:
            for key in [f'device{device_num}_idx', f'device{device_num}_id',
                       f'device{device_num}_ns_key', f'device{device_num}_app_key',
                       f'device{device_num}_ti']:
                if key in config['DEVICES']:
                    del config['DEVICES'][key]
        self.save_lora_config(config)
    
    def clear_devices(self):
        """Clear all devices"""
        config = self.read_lora_config()
        config['DEVICES'] = {}
        self.save_lora_config(config)