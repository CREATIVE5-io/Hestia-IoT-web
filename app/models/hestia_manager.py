"""
Module for managing NTN dongle communication.
"""
import configparser
import hashlib
import logging
import os
import threading
import fcntl
import json
import time
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
        self.temp_queue_file = os.path.join(self.run_dir, 'temp_data_queue.json')
        self.file_lock = threading.Lock()
        self.upload_thread = None
        self.upload_running = False

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

        # Ensure uplink-messages section exists
        if 'uplink-messages' not in config:
            config['uplink-messages'] = {}
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

        # Get uplink messages (pending queue items)
        uplink_messages = self._get_pending_uplink_messages()

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
            'uplink_messages': uplink_messages[:3],  # Keep only first 3 messages (newest)
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

    def clear_uplink_messages(self):
        """Clear all uplink messages"""
        config = configparser.ConfigParser()
        if os.path.exists(self.hestia_info_file):
            config.read(self.hestia_info_file)

        # Clear all messages
        if 'uplink-messages' in config:
            config.remove_section('uplink-messages')
            config['uplink-messages'] = {}

        # Save the updated configuration
        self._save_config(config)
        logger.info("Cleared all uplink messages")

    def add_uplink_message(self, data, success, message_type='Auto'):
        """Add an uplink message"""
        import datetime
        config = configparser.ConfigParser()
        if os.path.exists(self.hestia_info_file):
            config.read(self.hestia_info_file)

        # Ensure uplink-messages section exists
        if 'uplink-messages' not in config:
            config['uplink-messages'] = {}

        # Create timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Convert data to string if needed
        if isinstance(data, dict):
            data_str = json.dumps(data)
        else:
            data_str = str(data)

        # Generate unique key
        key = f"msg_{int(datetime.datetime.now().timestamp())}"

        # Store message in format: timestamp|data|success|type
        config['uplink-messages'][key] = f"{timestamp}|{data_str}|{success}|{message_type}"

        # Keep only last 3 messages to prevent file from growing too large
        messages = dict(config['uplink-messages'])
        if len(messages) > 3:
            # Remove oldest messages, keep only latest 3
            oldest_keys = sorted(messages.keys())[:len(messages)-3]
            for old_key in oldest_keys:
                del config['uplink-messages'][old_key]

        # Save the updated configuration
        self._save_config(config)
        logger.info(f"Added uplink message: {data_str[:50]}... Success: {success} Type: {message_type}")

    def _get_pending_uplink_messages(self):
        """Get the oldest 3 pending messages from temp_data_queue.json"""
        uplink_messages = []
        try:
            if not os.path.exists(self.temp_queue_file):
                return uplink_messages

            with self.file_lock:
                with open(self.temp_queue_file, 'r') as f:
                    if self._acquire_file_lock(f):
                        lines = f.readlines()
                        self._release_file_lock(f)
                    else:
                        return uplink_messages

            # Parse messages and comments
            current_comment = None
            message_count = 0

            for line in lines:
                line = line.strip()
                if line.startswith('//'):
                    # Extract timestamp from comment
                    if 'at ' in line:
                        timestamp_part = line.split('at ', 1)[1]
                        current_comment = timestamp_part
                elif line and not line.startswith('//'):
                    # This is a data line
                    try:
                        data = json.loads(line)
                        uplink_messages.append({
                            'timestamp': current_comment or 'Unknown',
                            'data': json.dumps(data),
                            'status': 'Pending',
                            'position': message_count + 1
                        })
                        message_count += 1

                        # Only get first 3 (oldest)
                        if message_count >= 3:
                            break

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Error reading pending uplink messages: {e}")

        return uplink_messages

    def capture_location_data(self):
        """Capture current RSRP, SINR, Longitude, Latitude and append to file"""
        import datetime
        import json

        try:
            # Read current hestia info
            hestia_info = self.read_hestia_info()

            # Extract the required data
            latitude = hestia_info.get('latitude', '')
            longitude = hestia_info.get('longitude', '')
            rsrp = hestia_info.get('rsrp', '')
            sinr = hestia_info.get('sinr', '')
            rsrp = '-126'
            sinr = '-1'

            # Check if all required data is available
            if not all([latitude, longitude, rsrp, sinr]):
                missing_fields = []
                if not latitude: missing_fields.append('Latitude')
                if not longitude: missing_fields.append('Longitude')
                if not rsrp: missing_fields.append('RSRP')
                if not sinr: missing_fields.append('SINR')

                return {
                    'success': False,
                    'error': f'Missing required data: {", ".join(missing_fields)}'
                }

            # Convert to appropriate data types
            try:
                lat_float = float(latitude)
                lon_float = float(longitude)
                rsrp_float = float(rsrp)
                sinr_float = float(sinr)
            except ValueError as e:
                return {
                    'success': False,
                    'error': f'Invalid data format: {str(e)}'
                }

            # Create the data structure
            capture_data = {
                'm': [lat_float, lon_float, rsrp_float, sinr_float]
            }

            # Use fixed filename for all captures
            filename = "temp_data_queue.json"

            # Thread-safe write to queue file
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            success = self._write_to_queue_file(
                json.dumps(capture_data),
                f"Captured at {timestamp}"
            )

            logger.info(f"Location data captured: {capture_data} -> {filename}")

            # Count total captures in file
            try:
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                capture_count = sum(1 for line in lines if line.strip().startswith('{"m":'))
            except:
                capture_count = 1

            return {
                'success': True,
                'filename': filename,
                'data': capture_data,
                'total_captures': capture_count
            }

        except Exception as e:
            logger.error(f"Error capturing location data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def auto_capture_from_downlink(self, dl_data):
        """Auto-capture location data triggered by downlink message with specific keys"""
        import datetime
        import json

        try:
            # Create the data structure for downlink trigger
            capture_data = {
                'D': [dl_data]
            }

            # Use same filename as manual captures
            filename = "temp_data_queue.json"

            # Thread-safe write to queue file
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            success = self._write_to_queue_file(
                json.dumps(capture_data),
                f"Auto-captured from downlink at {timestamp}"
            )

            logger.info(f"Auto-captured downlink data: {capture_data} -> {filename}")
        except Exception as e:
            logger.error(f"Error auto-capturing downlink data: {str(e)}")

    def _acquire_file_lock(self, file_handle):
        """Acquire file lock for safe file operations"""
        try:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
            return True
        except Exception as e:
            logger.error(f"Error acquiring file lock: {e}")
            return False

    def _release_file_lock(self, file_handle):
        """Release file lock"""
        try:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            logger.error(f"Error releasing file lock: {e}")

    def _write_to_queue_file(self, data_line, timestamp_comment):
        """Thread-safe write to queue file"""
        with self.file_lock:
            try:
                with open(self.temp_queue_file, 'a') as f:
                    if self._acquire_file_lock(f):
                        f.write(f"// {timestamp_comment}\n")
                        f.write(data_line + "\n")
                        self._release_file_lock(f)
                        return True
                    else:
                        logger.error("Could not acquire file lock for writing")
                        return False
            except Exception as e:
                logger.error(f"Error writing to queue file: {e}")
                return False

    def _read_and_process_queue(self):
        """Read first data entry from queue and return it"""
        with self.file_lock:
            try:
                if not os.path.exists(self.temp_queue_file):
                    return None, []

                with open(self.temp_queue_file, 'r') as f:
                    if self._acquire_file_lock(f):
                        lines = f.readlines()
                        self._release_file_lock(f)
                    else:
                        logger.error("Could not acquire file lock for reading")
                        return None, []

                if not lines:
                    return None, []

                # Find first data line (not comment)
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line and not line.startswith('//'):
                        try:
                            data = json.loads(line)
                            # Return data and remaining lines
                            remaining_lines = lines[:i] + lines[i+1:]
                            return data, remaining_lines
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON in queue file: {line}")
                            continue

                return None, lines

            except Exception as e:
                logger.error(f"Error reading queue file: {e}")
                return None, []

    def _update_queue_file(self, remaining_lines):
        """Update queue file with remaining lines after successful send"""
        with self.file_lock:
            try:
                with open(self.temp_queue_file, 'w') as f:
                    if self._acquire_file_lock(f):
                        f.writelines(remaining_lines)
                        self._release_file_lock(f)
                        return True
                    else:
                        logger.error("Could not acquire file lock for updating")
                        return False
            except Exception as e:
                logger.error(f"Error updating queue file: {e}")
                return False

    def start_upload_thread(self, hestia_instance):
        """Start background thread to process upload queue"""
        if not self.upload_running:
            self.upload_running = True
            self.hestia_instance = hestia_instance
            self.upload_thread = threading.Thread(target=self._upload_worker, daemon=True)
            self.upload_thread.start()
            logger.info("Upload thread started")

    def stop_upload_thread(self):
        """Stop background upload thread"""
        self.upload_running = False
        if self.upload_thread and self.upload_thread.is_alive():
            self.upload_thread.join(timeout=5)
        logger.info("Upload thread stopped")

    def _upload_worker(self):
        """Background worker thread to process upload queue"""
        logger.info("Upload worker thread started")

        while self.upload_running:
            try:
                # Check if queue file has data
                data, remaining_lines = self._read_and_process_queue()

                if data is None:
                    # No data to process, wait before checking again
                    time.sleep(5)
                    continue

                logger.info(f"Processing queue data: {data}")

                # Check module status and upload availability before sending
                if hasattr(self.hestia_instance, 'send_data'):
                    try:
                        # Check if module is ready
                        module_status = self.hestia_instance.module_status()
                        if not module_status or not module_status.get('all_ready', False):
                            logger.warning(f"Module not ready for transmission: {module_status}")
                            time.sleep(10)
                            continue

                        # Check if upload is available
                        if not self.hestia_instance.is_upload_available():
                            logger.warning(f"Upload not available, waiting...")
                            time.sleep(10)
                            continue

                        # All checks passed, attempt to send data
                        logger.info(f"Module ready and upload available, sending data: {data}")
                        success = self.hestia_instance.send_data(data)

                        if success:
                            logger.info(f"Successfully sent data: {data}")
                            # Add to uplink messages log
                            self.add_uplink_message(data, True, 'Auto')
                            # Remove the sent data from queue file
                            self._update_queue_file(remaining_lines)
                        else:
                            logger.warning(f"Failed to send data: {data}, will retry later")
                            # Add failed uplink to log
                            self.add_uplink_message(data, False, 'Auto')
                            # Wait before retrying
                            time.sleep(10)
                    except Exception as e:
                        logger.error(f"Error sending data: {e}")
                        time.sleep(10)
                else:
                    logger.error("Hestia instance does not have send_data method")
                    time.sleep(10)

            except Exception as e:
                logger.error(f"Error in upload worker: {e}")
                time.sleep(10)

        logger.info("Upload worker thread stopped")
