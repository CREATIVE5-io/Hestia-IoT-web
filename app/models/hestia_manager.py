"""
Module for managing NTN dongle communication.
"""
import configparser
import hashlib
import logging
import os
from app.models.config_manager import ConfigManager
from time import sleep

logger = logging.getLogger(__name__)

"""
Hestia information management
"""
class HestiaInfoManager(ConfigManager):
    """Hestia information manager"""

    def __init__(self):
        super().__init__()
        self.hestia_info_file = os.path.join(self.run_dir, 'hestia_info.ini')

    def read_hestia_info(self):
        """Read Hestia information"""
        config = configparser.ConfigParser()
        if os.path.exists(self.hestia_info_file):
            config.read(self.hestia_info_file)

        if 'ntn-info' not in config:
            config['ntn-info'] = {
                'imsi': '',
                'rsrp': '',
                'sinr': '',
                'longitude': '',
                'latitude': '',
                'ntn-status': '',
                'last-update': ''
            }
            self._save_config(config)

        if 'lora-info' not in config:
            config['lora-info'] = {
                'devAddr': '',
                'data': '',
                'rssi': '',
                'snr': '',
                'last-update': ''
            }
            self._save_config(config)

        # Ensure last-update fields exist
        if 'last-update' not in config['ntn-info']:
            config['ntn-info']['last-update'] = ''
            self._save_config(config)

        if 'last-update' not in config['lora-info']:
            config['lora-info']['last-update'] = ''
            self._save_config(config)

        # Ensure serial configuration section exists
        if 'serial-config' not in config:
            config['serial-config'] = {
                'serial_interface': '/dev/ttyUSB0'
            }
            self._save_config(config)

        # Ensure srv_mode section exists
        if 'srv_mode' not in config['ntn-info']:
            config['ntn-info']['srv_mode'] = '2'  # Default to UDP mode
            self._save_config(config)

        # Ensure downlink-messages section exists
        if 'downlink-messages' not in config:
            config['downlink-messages'] = {}
            self._save_config(config)

        # Get downlink messages
        downlink_messages = []
        if 'downlink-messages' in config:
            # Sort keys in reverse order to get newest messages first
            for key in sorted(config['downlink-messages'].keys(), reverse=True):
                message_data = config['downlink-messages'][key]
                if '|' in message_data:  # timestamp|data|length format
                    parts = message_data.split('|', 2)
                    if len(parts) >= 3:
                        downlink_messages.append({
                            'timestamp': parts[0],
                            'data': parts[1],
                            'length': parts[2]
                        })
                else:
                    # Fallback for other formats
                    downlink_messages.append({
                        'timestamp': 'Unknown',
                        'data': message_data,
                        'length': len(str(message_data))
                    })

        return {
            'imsi': config['ntn-info'].get('imsi', ''),
            'rsrp': config['ntn-info'].get('rsrp', ''),
            'sinr': config['ntn-info'].get('sinr', ''),
            'longitude': config['ntn-info'].get('longitude', ''),
            'latitude': config['ntn-info'].get('latitude', ''),
            'ntn-status': config['ntn-info'].get('ntn-status', ''),
            'srv_mode': config['ntn-info'].get('srv_mode', '2'),
            'last-update': config['ntn-info'].get('last-update', ''),
            'serial_interface': config['serial-config'].get('serial_interface', '/dev/ttyUSB0'),
            'downlink_messages': downlink_messages[:3],  # Keep only first 3 messages (newest)
            'lora-info': {
                'devAddr': config['lora-info'].get('devAddr', ''),
                'data': config['lora-info'].get('data', ''),
                'rssi': config['lora-info'].get('rssi', ''),
                'snr': config['lora-info'].get('snr', ''),
                'last-update': config['lora-info'].get('last-update', '')
            }
        }

    def _save_config(self, config):
        """Save configuration to file"""
        with open(self.hestia_info_file, 'w') as configfile:
            config.write(configfile)

    def get_file_hash(self):
        """Get file hash for change detection"""
        if not os.path.exists(self.hestia_info_file):
            return None

        sha256 = hashlib.sha256()
        with open(self.hestia_info_file, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def update_serial_interface(self, serial_interface):
        """Update serial interface configuration"""
        config = configparser.ConfigParser()
        if os.path.exists(self.hestia_info_file):
            config.read(self.hestia_info_file)

        # Ensure serial-config section exists
        if 'serial-config' not in config:
            config['serial-config'] = {}

        # Update the serial interface
        config['serial-config']['serial_interface'] = serial_interface

        # Save the updated configuration
        self._save_config(config)
        logger.info(f"Serial interface updated to: {serial_interface}")

    def add_downlink_message(self, data, length):
        """Add a downlink message from dl_callback"""
        import datetime
        config = configparser.ConfigParser()
        if os.path.exists(self.hestia_info_file):
            config.read(self.hestia_info_file)

        # Ensure downlink-messages section exists
        if 'downlink-messages' not in config:
            config['downlink-messages'] = {}

        # Create timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Convert data to string if it's bytes
        if isinstance(data, bytes):
            try:
                data_str = data.decode('utf-8')
            except:
                data_str = str(data)
        else:
            data_str = str(data)

        # Generate unique key
        key = f"msg_{int(datetime.datetime.now().timestamp())}"

        # Store message in format: timestamp|data|length
        config['downlink-messages'][key] = f"{timestamp}|{data_str}|{length}"

        # Keep only last 3 messages to prevent file from growing too large
        messages = dict(config['downlink-messages'])
        if len(messages) > 3:
            # Remove oldest messages, keep only latest 3
            oldest_keys = sorted(messages.keys())[:len(messages)-3]
            for old_key in oldest_keys:
                del config['downlink-messages'][old_key]

        # Save the updated configuration
        self._save_config(config)
        logger.info(f"Added downlink message: {data_str[:50]}... ({length} bytes)")

    def clear_downlink_messages(self):
        """Clear all downlink messages"""
        config = configparser.ConfigParser()
        if os.path.exists(self.hestia_info_file):
            config.read(self.hestia_info_file)

        # Clear all messages
        if 'downlink-messages' in config:
            config.remove_section('downlink-messages')
            config['downlink-messages'] = {}

        # Save the updated configuration
        self._save_config(config)
        logger.info("Cleared all downlink messages")
