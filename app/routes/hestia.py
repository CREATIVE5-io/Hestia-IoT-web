"""
Routes for managing NTN dongle communication and NTN information pages.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app.models.hestia_manager import HestiaInfoManager
#from app.models.hestia_operations import hestia
from app.utils.hestia_info import hestiaInfo

hestia = Blueprint('hestia', __name__)
_hestia_info_instance = None

@hestia.route('/')
def index():
    """Redirect root URL to HestiaInfo page"""
    return redirect(url_for('hestia.hestia_info_page'))

@hestia.route('/hestia_info', methods=['GET', 'POST'])
def hestia_info_page():
    """Hestia information page"""
    global _hestia_info_instance
    if request.method == 'POST':
        if request.form.get('action') == 'update_serial':
            try:
                serial_interface = request.form.get('serial_interface')
                hestia_manager = HestiaInfoManager()
                hestia_manager.update_serial_interface(serial_interface)
                flash('Serial interface updated successfully.')
            except Exception as e:
                flash(f'Serial interface update failed: {str(e)}')
            return redirect(url_for('hestia.hestia_info_page'))
        elif request.form.get('action') == 'start_hestia_info':
            try:
                if _hestia_info_instance is None:
                    _hestia_info_instance = hestiaInfo()
                _hestia_info_instance.start()
                #flash('Hestia info collection started.')
            except Exception as e:
                flash(f'Service start failed: {str(e)}')
            return redirect(url_for('hestia.hestia_info_page'))
        elif request.form.get('action') == 'stop_hestia_info':
            try:
                if _hestia_info_instance:
                    _hestia_info_instance.stop()
                    _hestia_info_instance = None
                #flash('Hestia info collection stopped.')
            except Exception as e:
                flash(f'Service stop failed: {str(e)}')
            return redirect(url_for('hestia.hestia_info_page'))
        elif request.form.get('action') == 'clear_messages':
            try:
                hestia_manager = HestiaInfoManager()
                hestia_manager.clear_downlink_messages()
                flash('Downlink messages cleared.')
            except Exception as e:
                flash(f'Clear messages failed: {str(e)}')
            return redirect(url_for('hestia.hestia_info_page'))
        elif request.form.get('action') == 'clear_uplink_messages':
            try:
                hestia_manager = HestiaInfoManager()
                # Clear the pending queue file
                import os
                queue_file = os.path.join(hestia_manager.run_dir, 'temp_data_queue.json')
                if os.path.exists(queue_file):
                    os.remove(queue_file)
                flash('Uplink queue cleared.')
            except Exception as e:
                flash(f'Clear uplink queue failed: {str(e)}')
            return redirect(url_for('hestia.hestia_info_page'))
        elif request.form.get('action') == 'capture_data':
            try:
                hestia_manager = HestiaInfoManager()
                result = hestia_manager.capture_location_data()
                if result['success']:
                    flash(f'Location data captured successfully! Total captures: {result["total_captures"]} (saved to {result["filename"]})')
                else:
                    flash(f'Capture failed: {result["error"]}')
            except Exception as e:
                flash(f'Capture data failed: {str(e)}')
            return redirect(url_for('hestia.hestia_info_page'))
    hestia_manager = HestiaInfoManager()
    hestia_info = hestia_manager.read_hestia_info()
    return render_template('hestia_info.html', hestia_info=hestia_info)

@hestia.route('/hestia_info_data', methods=['GET'])
def ntn_info_data():
    """NTN information data API endpoint"""
    hestia_manager = HestiaInfoManager()
    hestia_info = hestia_manager.read_hestia_info()
    file_hash = hestia_manager.get_file_hash()
    return jsonify({
        'hestia_info': hestia_info,
        'hash': file_hash
    })
 