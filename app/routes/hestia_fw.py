"""
Hestia Firmware Update Routes - Clean Version
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.hestia_manager import HestiaInfoManager
from app.models.hestia_operations import hestia
import logging
import os
import subprocess
import sys
import shutil
import threading
import queue
from time import sleep

logger = logging.getLogger(__name__)

hestia_fw = Blueprint('hestia_fw', __name__)

# Global variable to track firmware update status
firmware_update_status = {
    'in_progress': False,
    'progress': 0,
    'status': 'Ready',
    'result': 'No results yet',
    'success': None
}

def find_pymdfu_executable():
    """Find the pymdfu executable, handling virtual environments and cross-platform issues."""
    # For macOS/Linux virtual environments, try venv-specific paths first
    if sys.platform in ['darwin', 'linux']:
        # Check if we're in a virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            logger.info("Detected virtual environment, checking venv-specific paths")

            # Try the virtual environment's bin directory
            venv_bin = os.path.join(sys.prefix, 'bin', 'pymdfu')
            if os.path.exists(venv_bin) and os.access(venv_bin, os.X_OK):
                logger.info(f"Found pymdfu in virtual environment: {venv_bin}")
                return venv_bin

            # Also check the Scripts directory (some virtual envs use this)
            venv_scripts = os.path.join(sys.prefix, 'Scripts', 'pymdfu')
            if os.path.exists(venv_scripts) and os.access(venv_scripts, os.X_OK):
                logger.info(f"Found pymdfu in virtual environment Scripts: {venv_scripts}")
                return venv_scripts

    # Try to find pymdfu in PATH (works for system installations)
    pymdfu_path = shutil.which('pymdfu')
    if pymdfu_path:
        logger.info(f"Found pymdfu in PATH: {pymdfu_path}")
        return pymdfu_path

    # On Windows, try with .exe extension
    if sys.platform == 'win32':
        pymdfu_path = shutil.which('pymdfu.exe')
        if pymdfu_path:
            logger.info(f"Found pymdfu.exe in PATH: {pymdfu_path}")
            return pymdfu_path

        # Try to find it in Python Scripts directory
        python_scripts = os.path.join(os.path.dirname(sys.executable), 'Scripts')
        pymdfu_exe = os.path.join(python_scripts, 'pymdfu.exe')
        if os.path.exists(pymdfu_exe):
            logger.info(f"Found pymdfu in Python Scripts: {pymdfu_exe}")
            return pymdfu_exe

        pymdfu_script = os.path.join(python_scripts, 'pymdfu')
        if os.path.exists(pymdfu_script):
            logger.info(f"Found pymdfu script in Python Scripts: {pymdfu_script}")
            return pymdfu_script

    # Try using python -m pymdfu as fallback (this should work in virtual environments)
    try:
        logger.info("Testing 'python -m pymdfu' as fallback")
        # Test if pymdfu module can be imported and run
        result = subprocess.run([sys.executable, '-m', 'pymdfu', '--help'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("Successfully verified 'python -m pymdfu' works")
            return [sys.executable, '-m', 'pymdfu']
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning(f"Failed to verify 'python -m pymdfu': {e}")

    # macOS/Linux specific: Try common installation paths
    if sys.platform in ['darwin', 'linux']:
        common_paths = [
            '/usr/local/bin/pymdfu',
            '/opt/homebrew/bin/pymdfu',  # macOS Homebrew on Apple Silicon
            '/usr/bin/pymdfu',
            os.path.expanduser('~/.local/bin/pymdfu'),  # User installation
        ]

        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"Found pymdfu at common path: {path}")
                return path

    # If all else fails, return 'pymdfu' and let subprocess handle the error
    logger.warning("Could not find pymdfu executable, falling back to 'pymdfu' in PATH")
    return 'pymdfu'

@hestia_fw.route('/hestia_fw_update', methods=['GET', 'POST'])
def hestia_fw_update_page():
    """Hestia Firmware Update page"""
    
    if request.method == 'POST':
        if request.form.get('action') == 'update_serial':
            try:
                serial_interface = request.form.get('serial_interface')
                hestia_manager = HestiaInfoManager()
                hestia_manager.update_serial_interface(serial_interface)
                flash('Serial interface updated successfully.')
            except Exception as e:
                flash(f'Serial interface update failed: {str(e)}')
            return redirect(url_for('hestia_fw.hestia_fw_update_page'))
        
        elif request.form.get('action') == 'start_firmware_update':
            try:
                # Check if file was uploaded
                if 'firmware_file' not in request.files:
                    flash('No firmware file selected.')
                    return redirect(url_for('hestia_fw.hestia_fw_update_page'))
                
                file = request.files['firmware_file']
                if file.filename == '':
                    flash('No firmware file selected.')
                    return redirect(url_for('hestia_fw.hestia_fw_update_page'))
                
                # Get update mode option
                update_mode = request.form.get('update_mode', 'normal')
                retry_mode = update_mode == 'bootloader'
               
                                # Initialize hestia manager
                hestia_manager = HestiaInfoManager()

                # Save uploaded file temporarily with secure filename
                from werkzeug.utils import secure_filename
                upload_dir = os.path.join(hestia_manager.run_dir, 'firmware_uploads')
                os.makedirs(upload_dir, exist_ok=True)

                filename = secure_filename(file.filename)
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                
                # Get serial interface
                serial_interface = hestia_manager.read_hestia_info().get('serial_interface', '/dev/ttyUSB0')
                
                # Start firmware update in background thread
                def firmware_update_background():
                    global firmware_update_status
                    try:
                        firmware_update_status.update({
                            'in_progress': True,
                            'progress': 0,
                            'status': 'Initializing firmware update...',
                            'result': 'Update in progress...',
                            'success': None
                        })
                        
                        logger.info(f"Starting firmware update: {filename}, Mode: {update_mode}")
                        
                        if not retry_mode:
                            firmware_update_status.update({
                                'progress': 10,
                                'status': 'Preparing device for update...'
                            })
                            # Normal mode - put device into bootloader first
                            ntn_dongle = hestia(port=serial_interface, dl_callback=lambda d, l: None)
                            validpasswd = ntn_dongle.set_password((0,0,0,0))
                            logger.info(f'Password valid: {validpasswd}')
                            
                            if not validpasswd:
                                logger.error("Failed to initialize dongle")
                                return
                            
                            # Enable Engineering mode
                            ntn_dongle.ntn.set_register(0xFFD0, 0xAA55)
                            # Enable Bootloader Mode
                            ntn_dongle.ntn.set_register(0xD000, 0xAA55)
                            # Reset MCU
                            ntn_dongle.ntn.set_register(0xFD00, 0xAA55)
                            sleep(1)
                            
                            # Close the Modbus connection to release the serial port
                            ntn_dongle.stop()
                            sleep(0.5)
                        else:
                            logger.info("Retrying firmware update in bootloader mode")
                            sleep(0.5)
                        
                        # Find the correct pymdfu executable
                        pymdfu_cmd = find_pymdfu_executable()
                        logger.info(f'Using pymdfu command: {pymdfu_cmd}')
                        
                        firmware_update_status.update({
                            'progress': 20,
                            'status': 'Connecting to device...'
                        })
                        
                        # Build command list - simplified
                        command = [
                            pymdfu_cmd, "update",
                            "--tool", "serial",
                            "--port", serial_interface,
                            "--baudrate", '115200',
                            "--image", filepath,
                            "-v", "debug"
                        ]
                        
                        logger.info(f"Executing command: {' '.join(command)}")
                        
                        firmware_update_status.update({
                            'progress': 30,
                            'status': 'Uploading firmware...'
                        })
                        
                        # Execute firmware update
                        process = subprocess.Popen(
                            command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            universal_newlines=True
                        )
                        
                        # Log output in real-time and update progress
                        progress = 40
                        total_lines = 0
                        lines_processed = 0
                        
                        for line in process.stdout:
                            logger.info(line.rstrip())
                            lines_processed += 1
                            
                            # Update progress based on pymdfu output patterns
                            line_lower = line.lower()
                            # Connection and initialization phase
                            if 'ntn dongle init' in line_lower or 'password valid' in line_lower:
                                progress = 40
                                firmware_update_status.update({
                                    'progress': progress,
                                    'status': 'Initializing dongle connection...'
                                })
                            elif 'ntn dongle connection closed' in line_lower:
                                progress = 45
                                firmware_update_status.update({
                                    'progress': progress,
                                    'status': 'Preparing for firmware transfer...'
                                })
                            elif 'using pymdfu command' in line_lower or 'starting mdfu file transfer' in line_lower:
                                progress = 50
                                firmware_update_status.update({
                                    'progress': progress,
                                    'status': 'Starting MDFU transfer...'
                                })
                            
                            # Writing phase: Detect WRITE_CHUNK commands and increment based on sequence or count
                            # From log analysis, WRITE_CHUNK starts from seq 2-24 (~23 chunks), progress 50-85%
                            elif 'command:         write_chunk' in line_lower:
                                # Assuming ~25 chunks based on log (seq 2 to 24, plus padding)
                                write_count = write_count + 1 if 'write_count' in locals() else 1
                                progress = 50 + min((write_count / 25.0) * 35, 35)  # Scale to reach ~85%
                                firmware_update_status.update({
                                    'progress': int(progress),
                                    'status': 'Writing firmware chunks...'
                                })
                            # Verification phase: GET_IMAGE_STATE is like verify
                            elif 'command:         get_image_state' in line_lower:
                                progress = 85
                                firmware_update_status.update({
                                    'progress': progress,
                                    'status': 'Verifying image state...'
                                })
                            
                            # End transfer and success
                            elif 'ending mdfu file transfer' in line_lower or 'upgrade finished successfully' in line_lower:
                                progress = 90
                                firmware_update_status.update({
                                    'progress': progress,
                                    'status': 'Firmware update completed successfully!'
                                })
                            # Fallback for general progress during debug lines (e.g., sending/receiving frames)
                            elif ('sending frame' in line_lower or 'received a frame' in line_lower) and lines_processed % 10 == 0:
                                if progress < 80:
                                    progress = min(progress + 0.2, 80)  # Slower increment for finer control
                                    firmware_update_status['progress'] = int(progress)    

                        firmware_update_status.update({
                            'progress': 90,
                            'status': 'Finalizing update...'
                        })
                        
                        return_code = process.wait()
                        if return_code != 0:
                            logger.error(f"Firmware update failed with return code: {return_code}")
                            firmware_update_status.update({
                                'in_progress': False,
                                'progress': 0,
                                'status': 'Update failed',
                                'result': f'ERROR: Firmware update failed with return code {return_code}',
                                'success': False
                            })
                        else:
                            logger.info("Firmware update completed successfully!")
                            
                            # Get updated MCU firmware version after successful update
                            mcu_fw_version = 'Unknown'
                            try:
                                # Wait a moment for device to restart after firmware update
                                sleep(2)
                                ntn_dongle = hestia(port=serial_interface, dl_callback=lambda d, l: None)
                                while ntn_dongle.set_password((0, 0, 0, 0)) is False:
                                    logger.info("Waiting for device to reconnect...")
                                    sleep(2)
                                else:
                                    mcu_fw_version = ntn_dongle.fw_ver() or 'Unable to retrieve'
                                ntn_dongle.stop()
                                logger.info(f"Updated MCU firmware version: {mcu_fw_version}")
                            except Exception as e:
                                logger.warning(f"Could not retrieve updated MCU firmware version: {e}")
                                mcu_fw_version = 'Unable to retrieve'
                            
                            firmware_update_status.update({
                                'in_progress': False,
                                'progress': 100,
                                'status': 'Update completed',
                                'result': f'SUCCESS: Firmware updated successfully. New MCU firmware version: {mcu_fw_version}',
                                'success': True,
                                'new_fw_version': mcu_fw_version
                            })
                            
                    except Exception as e:
                        logger.error(f"Firmware update exception: {str(e)}")
                        firmware_update_status.update({
                            'in_progress': False,
                            'progress': 0,
                            'status': 'Update failed',
                            'result': f'ERROR: {str(e)}',
                            'success': False
                        })
                
                # Start background thread and return immediately
                update_thread = threading.Thread(target=firmware_update_background, daemon=True)
                update_thread.start()
                
                # Return response immediately to prevent loading state
                #flash(f'Firmware update started with file: {filename}. Update mode: {update_mode.title()}. Monitor progress below.')
                
            except Exception as e:
                flash(f'Firmware update failed: {str(e)}')
                logger.error(f"Firmware update error: {str(e)}")
            
            return redirect(url_for('hestia_fw.hestia_fw_update_page'))

    # Get current configuration for display
    hestia_manager = HestiaInfoManager()
    hestia_info = hestia_manager.read_hestia_info()
    
    # Try to get firmware version on page load with timeout protection
    fw_version = 'Not available'
    try:
        serial_interface = hestia_info.get('serial_interface', '/dev/ttyUSB0')

        # Use threading-based timeout to prevent hanging if device is in bootloader mode

        def get_firmware_version_worker(q, serial_interface):
            """Worker function to get firmware version in separate thread"""
            try:
                ntn_dongle = hestia(port=serial_interface, dl_callback=lambda d, l: None)

                if ntn_dongle.set_password((0, 0, 0, 0)):
                    retrieved_version = ntn_dongle.fw_ver()
                    if retrieved_version:
                        q.put(('success', retrieved_version))
                    else:
                        q.put(('success', None))
                else:
                    q.put(('failed', None))

                ntn_dongle.stop()
            except Exception as e:
                logger.warning(f"Worker thread exception: {e}")
                q.put(('error', str(e)))

        # Create queue for thread communication
        result_queue = queue.Queue()

        # Start worker thread
        logger.info("Starting firmware version check in background thread...")
        worker_thread = threading.Thread(
            target=get_firmware_version_worker,
            args=(result_queue, serial_interface),
            daemon=True
        )
        worker_thread.start()

        # Wait for result with timeout
        try:
            status, result = result_queue.get(timeout=5.0)  # 5-second timeout
            logger.info(f"Thread completed with status: {status}, result: {result}")

            if status == 'success' and result:
                fw_version = result
            elif status == 'success':
                fw_version = 'Version not available'
            else:
                fw_version = 'Unable to connect'

        except queue.Empty:
            logger.warning("Firmware version check timed out after 5 seconds")
            fw_version = 'Unable to connect'

    except Exception as e:
        logger.warning(f"Failed to get FW version on page load: {e}")
        fw_version = 'Unable to connect'

    return render_template('hestia_fw_update.html', hestia_info=hestia_info, fw_version=fw_version)

@hestia_fw.route('/hestia_fw_status', methods=['GET'])
def firmware_update_status_api():
    """API endpoint to get current firmware update status"""
    global firmware_update_status
    return firmware_update_status

