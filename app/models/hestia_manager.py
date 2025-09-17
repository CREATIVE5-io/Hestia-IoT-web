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

        return {
            'imsi': config['ntn-info'].get('imsi', ''),
            'rsrp': config['ntn-info'].get('rsrp', ''),
            'sinr': config['ntn-info'].get('sinr', ''),
            'longitude': config['ntn-info'].get('longitude', ''),
            'latitude': config['ntn-info'].get('latitude', ''),
            'ntn-status': config['ntn-info'].get('ntn-status', ''),
            'last-update': config['ntn-info'].get('last-update', ''),
            'serial_interface': config['serial-config'].get('serial_interface', '/dev/ttyUSB0'),
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
