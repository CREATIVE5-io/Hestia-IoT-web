"""
LoRa device management routes
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import json
import logging
import os
import time
from time import sleep
from app.utils.auth import login_required
from app.models.lora_manager import LoRaConfigManager
from app.utils.lora_setup import setup_lora_devices, setup_lora

logger = logging.getLogger(__name__)

lora_bp = Blueprint('lora', __name__)

@lora_bp.route('/')
def index():
    """Redirect root URL to LoRa page"""
    return redirect(url_for('lora.lora_page'))

@lora_bp.route('/lora', methods=['GET', 'POST'])
def lora_page():
    """LoRa configuration page"""
    config_manager = LoRaConfigManager()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update':
            # Handle LoRa settings update
            frequency = request.form.get('frequency')
            sf = request.form.get('sf')
            ch_plan = request.form.get('ch_plan')
            serial_interface = request.form.get('serial_interface')
            
            # Update configuration file
            config_manager.update_lora_settings(frequency, sf, ch_plan, serial_interface)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # For AJAX requests, return updated data
                updated_data = {
                    'frequency': frequency,
                    'sf': sf,
                    'ch_plan': ch_plan,
                    'serial_interface': serial_interface
                }
                return jsonify({'status': 'success', 'data': updated_data})
            
        elif action == 'add':
            # Handle adding new device
            device_data = {
                'idx': request.form.get('device_idx'),
                'id': request.form.get('device_id'),
                'ns_key': request.form.get('device_ns_key'),
                'app_key': request.form.get('device_app_key'),
                'transmit_interval': request.form.get('device_transmit_interval', '0'),
            }
            config_manager.add_device(device_data)
            
        elif action == 'delete':
            # Handle deleting devices
            device_nums = request.form.getlist('device_nums')
            if device_nums:
                config_manager.delete_devices(device_nums)
                
        elif action == 'setupLoraConfig':
            # Initiate Lora Configuration Setup
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Start the setup process and return immediately
                # The frontend will poll for progress updates
                from threading import Thread
                import time
                import json
                import os

                # Create a progress file to track status
                progress_file = os.path.join(config_manager.run_dir, 'lora_setup_progress.json')

                def progress_callback(percentage, message):
                    """Save progress to file for polling"""
                    progress_data = {
                        'percentage': percentage,
                        'message': message,
                        'timestamp': time.time()
                    }
                    try:
                        with open(progress_file, 'w') as f:
                            json.dump(progress_data, f)
                    except:
                        pass
                
                def setup_thread():
                    """Run setup in background thread"""
                    try:
                        setup_status = _setup_lora_config(config_manager, progress_callback)
                        # Save final result
                        final_data = {
                            'percentage': 100,
                            'message': 'Setup completed',
                            'setup_status': setup_status,
                            'completed': True,
                            'timestamp': time.time()
                        }
                        with open(progress_file, 'w') as f:
                            json.dump(final_data, f)
                    except Exception as e:
                        error_data = {
                            'percentage': 100,
                            'message': f'Setup failed: {str(e)}',
                            'setup_status': f'Setup failed: {str(e)}',
                            'completed': True,
                            'error': True,
                            'timestamp': time.time()
                        }
                        with open(progress_file, 'w') as f:
                            json.dump(error_data, f)

                # Start setup in background
                thread = Thread(target=setup_thread)
                thread.daemon = True
                thread.start()

                return jsonify({'status': 'started', 'message': 'Setup process started'})
            else:
                # For non-AJAX requests, run synchronously (no progress callback needed)
                setup_status = _setup_lora_config(config_manager)
            
        elif action == 'setupLoraDevices':
            # Initiate LoRa setup
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Start the setup process and return immediately
                # The frontend will poll for progress updates
                from threading import Thread
                import time
                import json
                import os

                # Create a progress file to track status
                progress_file = os.path.join(config_manager.run_dir, 'lora_setup_progress.json')

                def progress_callback(percentage, message):
                    """Save progress to file for polling"""
                    progress_data = {
                        'percentage': percentage,
                        'message': message,
                        'timestamp': time.time()
                    }
                    try:
                        with open(progress_file, 'w') as f:
                            json.dump(progress_data, f)
                    except:
                        pass

                def setup_thread():
                    """Run setup in background thread"""
                    try:
                        setup_status, failed_devices = _setup_lora_devices(config_manager, progress_callback)
                        # Save final result
                        final_data = {
                            'percentage': 100,
                            'message': 'Setup completed',
                            'setup_status': setup_status,
                            'failed_devices': failed_devices,
                            'completed': True,
                            'timestamp': time.time()
                        }
                        with open(progress_file, 'w') as f:
                            json.dump(final_data, f)
                    except Exception as e:
                        error_data = {
                            'percentage': 100,
                            'message': f'Setup failed: {str(e)}',
                            'setup_status': f'Setup failed: {str(e)}',
                            'failed_devices': ['System error'],
                            'completed': True,
                            'error': True,
                            'timestamp': time.time()
                        }
                        with open(progress_file, 'w') as f:
                            json.dump(error_data, f)

                # Start setup in background
                thread = Thread(target=setup_thread)
                thread.daemon = True
                thread.start()

                return jsonify({'status': 'started', 'message': 'Setup process started'})
            else:
                # For non-AJAX requests, run synchronously (no progress callback needed)
                setup_status, failed_devices = _setup_lora_devices(config_manager)
            
        elif action == 'upload_csv':
            # Handle CSV upload (if implemented)
            if 'csv_file' in request.files:
                # Add CSV handling logic here if needed
                pass
        
        return redirect(url_for('lora.lora_page'))
    
    # GET request handling
    lora_data = config_manager.get_lora_data()
    print(f"LoRa data: {lora_data}")
    devices_data = config_manager.get_devices_data()
    print(f"Devices data: {devices_data}")
    
    return render_template('lora.html', 
                         lora=lora_data, 
                         devices=devices_data)

@lora_bp.route('/lora/update_settings', methods=['POST'])
def update_lora_settings():
    """Update LoRa dongle settings"""
    try:
        data = request.get_json()
        frequency = data.get('frequency', '')
        sf = data.get('sf', '')
        ch_plan = data.get('ch_plan', '')
        
        config_manager = LoRaConfigManager()
        config_manager.update_lora_settings(frequency, sf, ch_plan)
        
        return jsonify({'status': 'success', 'message': 'LoRa settings updated successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@lora_bp.route('/lora/add_device', methods=['POST'])
def add_lora_device():
    """Add a new LoRa device"""
    try:
        data = request.get_json()
        
        device_data = {
            'idx': data.get('idx', ''),
            'id': data.get('id', ''),
            'ns_key': data.get('ns_key', ''),
            'app_key': data.get('app_key', ''),
            'transmit_interval': data.get('transmit_interval', ''),
        }
        
        config_manager = LoRaConfigManager()
        success, message = config_manager.add_device(device_data)
        
        if success:
            return jsonify({'status': 'success', 'message': message})
        else:
            return jsonify({'status': 'error', 'message': message})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@lora_bp.route('/lora/delete_devices', methods=['POST'])
def delete_lora_devices():
    """Delete selected LoRa devices"""
    try:
        data = request.get_json()
        device_nums = data.get('device_nums', [])
        
        if not device_nums:
            return jsonify({'status': 'error', 'message': 'No devices selected'})
        
        config_manager = LoRaConfigManager()
        config_manager.delete_devices(device_nums)
        
        return jsonify({'status': 'success', 'message': f'Deleted {len(device_nums)} device(s)'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@lora_bp.route('/lora/clear_devices', methods=['POST'])
def clear_lora_devices():
    """Clear all LoRa devices"""
    try:
        config_manager = LoRaConfigManager()
        config_manager.clear_devices()
        
        return jsonify({'status': 'success', 'message': 'All devices cleared'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def _setup_lora_devices(config_manager, progress_callback=None):
    """Setup LoRa devices with real progress tracking"""
    return setup_lora_devices(config_manager, progress_callback)

def _setup_lora_config(config_manager, progress_callback=None):
    """Setup LoRa config with real progress tracking"""
    return setup_lora(config_manager, progress_callback)
