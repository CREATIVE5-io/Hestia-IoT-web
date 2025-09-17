"""
LoRa device setup utility functions
"""
import configparser
import json
import logging
import os
import threading
from datetime import datetime
from time import sleep

from app.models.lora_manager import LoRaConfigManager
from app.models.hestia_operations import hestia
from app.models.hestia_manager import HestiaInfoManager
from app.models.config_manager import ConfigManager

logger = logging.getLogger(__name__)

def dl_callback(data, d_len):
    try:
        logger.debug(f'dl_callback: {d_len}, {data}')
    except Exception as e:
        logger.error(e)

class hestiaInfo(ConfigManager):
    """Class to hold Hestia info data"""
    def __init__(self):
        super().__init__()
        self.hestia_info = {}
        self.lock = threading.Lock()
        self.last_update = None
        self.ntn_dongle = None
        self.running = False
        self.thread = None
        self.hestia_info_file = os.path.join(self.run_dir, 'hestia_info.ini')
        print(f"Hestia info file path: {self.hestia_info_file}")
        try:
            config = HestiaInfoManager().read_hestia_info()
            logger.info(f"Hestia Config: {config}")
            ser_interface = config.get('serial_interface', '/dev/ttyUSB0')
            logger.info(f"Using serial interface: {ser_interface}")
            self.ntn_dongle = hestia(port=ser_interface, dl_callback=dl_callback, lock=threading.Lock())  # Assuming lock is needed, using threading.Lock()

            validpasswd = self.ntn_dongle.set_password((0,0,0,0))
            # Initialize the dongle
            if not validpasswd:
                raise ValueError("Failed to initialize dongle")

            logger.info(f"Dongle connected successfully on {ser_interface}")
        except Exception as e:
            logger.error(f"Failed to connect to dongle: {str(e)}")
            self.ntn_dongle = None
            
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.update_info)
            self.thread.daemon = True
            self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        if self.ntn_dongle:
            self.ntn_dongle = None

    def write_to_ini(self):
        # Read existing config or create new one
        config = configparser.ConfigParser()
        if os.path.exists(self.hestia_info_file):
            config.read(self.hestia_info_file)

        # Ensure ntn-info section exists
        if 'ntn-info' not in config:
            config['ntn-info'] = {}
        if 'lora-info' not in config:
            config['lora-info'] = {}

        # Update with current NTN info
        config['ntn-info']['imsi'] = self.hestia_info.get('imsi', '')
        network = self.hestia_info.get('network_info', {})
        config['ntn-info']['rsrp'] = str(network.get('rsrp', ''))
        config['ntn-info']['sinr'] = str(network.get('sinr', ''))
        gps = self.hestia_info.get('gps_info', {})
        config['ntn-info']['longitude'] = str(gps.get('longitude', ''))
        config['ntn-info']['latitude'] = str(gps.get('latitude', ''))
        config['ntn-info']['ntn-status'] = str(self.hestia_info.get('module_status', ''))
        config['ntn-info']['last-update'] = str(self.hestia_info.get('last-update', ''))
        
        config['lora-info']['devaddr'] = self.hestia_info.get('lora-info', {}).get('devAddr', '')
        config['lora-info']['data'] = self.hestia_info.get('lora-info', {}).get('data', '')
        config['lora-info']['rssi'] = self.hestia_info.get('lora-info', {}).get('rssi', '')
        config['lora-info']['snr'] = self.hestia_info.get('lora-info', {}).get('snr', '')
        config['lora-info']['last-update'] = self.hestia_info.get('lora-info', {}).get('last-update', '')

        # Write to file
        with open(self.hestia_info_file, 'w') as f:
            config.write(f)

    def update_info(self):
        while self.running:
            try:
                if self.ntn_dongle:
                    imsi = self.ntn_dongle.imsi()
                    if imsi:
                        with self.lock:
                            self.hestia_info['imsi'] = imsi
                        logger.info(f'IMSI: {imsi}')
                    
                    module_status = self.ntn_dongle.module_status()
                    logger.info(f'Module Status: {module_status}')
                    network_info = self.ntn_dongle.get_network_info()
                    logger.info(f'Network Info: {network_info}')
                    gps_info = self.ntn_dongle.get_gps_info()
                    logger.info(f'GPS Info: {gps_info}')
                    
                    with self.lock:
                        self.hestia_info['module_status'] = module_status
                        self.hestia_info['network_info'] = network_info
                        self.hestia_info['gps_info'] = gps_info
                        self.hestia_info['last-update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                    devices = LoRaConfigManager().get_devices_data()
                    logger.info(f"LoRa Devices: {devices}")
                    if len(devices) > 0:
                        data = self.ntn_dongle.pcie2_cmd('AT+BISGET=?')
                        logger.info(f'{data=}')
                        
                        if data:
                            lora_info = {}
                            data = data.split(',')
                            lora_info['devAddr'] = data[0]
                            lora_info['data'] = data[1]
                            lora_info['rssi'] = data[2]
                            lora_info['snr'] = data[3]
                            lora_info['last-update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            with self.lock:
                                self.hestia_info['lora-info'] = lora_info
                            logger.info(f'LoRa Info: {lora_info}')
                    logger.info(f'Updated Hestia Info: {self.hestia_info}')            
                    self.write_to_ini()
                    sleep(5)
                else:
                    sleep(10)  # Retry after some time if dongle is not connected
            except Exception as e:
                logger.error(f"Error during info retrieval: {e}")
                sleep(10)  # Wait before retrying
