"""
LoRa device setup utility functions
"""
import json
import logging
import os
from time import sleep

from app.models.lora_manager import LoRaConfigManager
from app.models.hestia_operations import hestia

logger = logging.getLogger(__name__)

def setup_lora_devices(config_manager, progress_callback=None):
    """Setup LoRa devices with progress tracking.
    
    Args:
        ser_interface (str): Serial interface to connect to
        config_manager (LoRaConfigManager): Configuration manager instance
        progress_callback (callable): Optional callback for progress updates
        
    Returns:
        tuple: (setup_status, failed_devices)
    """
    ntn_dongle = None
    failed_devices = []
    
    def update_progress(percentage, message):
        """Helper to update progress"""
        if progress_callback:
            progress_callback(percentage, message)

    try:
        update_progress(5, "Initializing LoRa dongle...")
        
        config = config_manager.read_lora_config()
        try:
            update_progress(15, "Connecting to dongle...")
            ser_interface = config['NTN-DONGLE'].get('serial_interface', '/dev/ttyUSB0')
            logger.debug(f"Using serial interface: {ser_interface}")
            ntn_dongle = hestia(port=ser_interface, dl_callback=None, lock=None)
           
            validpasswd = ntn_dongle.set_password((0,0,0,0)) 
            # Initialize the dongle
            if not validpasswd:
                raise ValueError("Failed to initialize dongle")
            
            update_progress(20, f"Dongle connected successfully on {ser_interface}")
        except Exception as e:
            update_progress(20, f"Failed to connect to dongle: {str(e)}")
            raise
        
        # Clear all devices first (20% to 50% of progress)
        update_progress(25, "Clearing existing device configurations...")
        for i in range(16):
            cmd = f'AT+BISDEV={i}:ffffffff:ffffffffffffffffffffffffffffffff:ffffffffffffffffffffffffffffffff'
            if ntn_dongle:
                data = ntn_dongle.pcie2_cmd(cmd)
                if data:
                    data = data.strip()
            else:
                data = "OK"  # Simulation
                sleep(0.1)  # Simulate some processing time

            if not data or data != "OK":
                logger.error(f"Failed to clear device {i}")
                failed_devices.append(f"Device {i}")

            # Update progress for clearing devices (25% to 50%)
            clear_progress = 25 + (i + 1) * (25 / 16)
            update_progress(clear_progress, f"Cleared device slot {i}")

        if not failed_devices:
            devices = {k: v for k, v in config['DEVICES'].items() if k.endswith('_id')}
            total_devices = len(devices)

            if total_devices == 0:
                update_progress(90, "No devices to configure")
            else:
                update_progress(55, f"Configuring {total_devices} devices...")

                # Configure devices (50% to 90% of progress)
                for device_index, device_key in enumerate(devices.keys()):
                    dev = device_key.split('_')[0]
                    idx = config['DEVICES'][dev+'_idx']
                    device_id = config['DEVICES'][dev+'_id']

                    update_progress(
                        55 + (device_index * 35 / total_devices),
                        f"Configuring device {idx} (ID: {device_id})"
                    )

                    cmd = f'AT+BISDEV={idx}:{config["DEVICES"][dev+"_id"]}:{config["DEVICES"][dev+"_ns_key"]}:{config["DEVICES"][dev+"_app_key"]}'

                    if ntn_dongle:
                        data = ntn_dongle.pcie2_cmd(cmd)
                        if data:
                            data = data.strip()
                    else:
                        data = "OK"  # Simulation
                        sleep(0.2)  # Simulate some processing time
                    logger.info(f'response: {data}')
                    if not data or data != "OK":
                        logger.error(f"Failed to configure device {idx}")
                        failed_devices.append(f"Device {idx}")
                        update_progress(
                            55 + ((device_index + 1) * 35 / total_devices),
                            f"Failed to configure device {idx}"
                        )
                    else:
                        update_progress(
                            55 + ((device_index + 1) * 35 / total_devices),
                            f"Successfully configured device {idx}"
                        )
        
        setup_status = "Setup completed: " + ("OK" if not failed_devices else "Failed")
        update_progress(95, "Finalizing setup...")
        
        data = ntn_dongle.pcie2_cmd('AT+BISS')
        logger.info(f'response: {data}')
        data = ntn_dongle.pcie2_cmd('ATZ')
        logger.info(f'response: {data}')
    except Exception as e:
        setup_status = f"Setup failed: {str(e)}"
        failed_devices = [f"Device {i}" for i in range(16)]  # Assume all failed on exception
        logger.error(f"Error during setup: {e}")
        update_progress(95, f"Setup failed: {str(e)}")

    finally:
        if ntn_dongle:
            ntn_dongle = None

        final_message = "Setup completed successfully" if not failed_devices else f"Setup completed with {len(failed_devices)} failed devices"
        update_progress(100, final_message)
    
    return setup_status, failed_devices

def setup_lora(config_manager, progress_callback=None):
    """Setup LoRa module with progress tracking.
    
    Args:
        config_manager (LoRaConfigManager): Configuration manager instance
        progress_callback (callable): Optional callback for progress updates
        
    Returns:
        bool: setup_status
    """
    ntn_dongle = None
    
    def update_progress(percentage, message):
        """Helper to update progress"""
        if progress_callback:
            progress_callback(percentage, message)

    try:
        update_progress(5, "Initializing LoRa dongle...")

        config = config_manager.read_lora_config()
        try:
            update_progress(15, "Connecting to dongle...")
            ser_interface = config['NTN-DONGLE'].get('serial_interface', '/dev/ttyUSB0')
            logger.debug(f"Using serial interface: {ser_interface}")
            ntn_dongle = hestia(port=ser_interface, dl_callback=None)
           
            validpasswd = ntn_dongle.set_password((0,0,0,0)) 
            # Initialize the dongle
            if not validpasswd:
                raise ValueError("Failed to initialize dongle")
            
            update_progress(20, f"Dongle connected successfully on {ser_interface}")
        except Exception as e:
            update_progress(20, f"Failed to connect to dongle: {str(e)}")
            raise
    
        logger.info('--- LoRa Setup ---')
        data = ntn_dongle.pcie2_cmd('AT+BISFMT=1')
        logger.info(f'response: {data}')
        update_progress(40, f"successfully on set FMT=1")
        
        if config['LORA']:
            frequency = config['LORA'].get('frequency', '')
            sf = config['LORA'].get('sf', '')
            ch_plan = config['LORA'].get('ch_plan', '')
            
            if frequency:
                data = ntn_dongle.pcie2_cmd(f'AT+BISRXF={frequency}')
                logger.info(f'response: {data}')
                if data:
                    data = data.strip()
                    logger.info(f"Set frequency response: {data}")
                if "OK" in data:
                    update_progress(55, f"successfully on set frequency {frequency}")
                else:
                    update_progress(55, f"Failed to set frequency {frequency}")
            
            if sf:
                data = ntn_dongle.pcie2_cmd(f'AT+BISRXSF={sf}')
                logger.info(f'response: {data}')
                if data:
                    data = data.strip()
                if "OK" in data:
                    update_progress(70, f"successfully on set spreading factor {sf}")
                else:
                    update_progress(70, f"Failed to set spreading factor {sf}")
            
            if ch_plan:
                data = ntn_dongle.pcie2_cmd(f'AT+BISCHPLAN={ch_plan}')
                logger.info(f'response: {data}')
                if data:
                    data = data.strip()
                if "OK" in data:
                    update_progress(85, f"successfully on set channel plan {ch_plan}")
                else:
                    update_progress(85, f"Failed to set channel plan {ch_plan}")
                
        data = ntn_dongle.pcie2_cmd('AT+BISS')
        logger.info(f'response: {data}')
        data = ntn_dongle.pcie2_cmd('ATZ')
        logger.info(f'response: {data}')
        update_progress(95, "Finalizing setup...")
        setup_status = "Setup completed successfully"
    except Exception as e:
        setup_status = f"Setup failed: {str(e)}"
        logger.error(f"Error during setup: {e}")
        update_progress(95, f"Setup failed: {str(e)}")
    finally:
        if ntn_dongle:
            ntn_dongle = None

        final_message = "Setup completed successfully" if setup_status.startswith("Setup completed") else f"Setup failed: {setup_status}"
        update_progress(100, final_message)
    return setup_status