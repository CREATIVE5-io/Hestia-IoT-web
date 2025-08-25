"""
Routes for managing NTN dongle communication.
"""
from flask import Blueprint, jsonify, request

from app.models.ntn_manager import NTNDongleManager

ntn = Blueprint('ntn', __name__)
_ntn_dongle = None

def get_ntn_dongle():
    """Get or create NTN dongle manager instance."""
    global _ntn_dongle
    if _ntn_dongle is None:
        try:
            _ntn_dongle = NTNDongleManager()
        except Exception as e:
            return None
    return _ntn_dongle

@ntn.route('/api/ntn/status', methods=['GET'])
def get_status():
    """Get NTN dongle status."""
    ntn_dongle = get_ntn_dongle()
    if not ntn_dongle:
        return jsonify({'error': 'Failed to initialize NTN dongle'}), 500

    conn_type = request.args.get('type', 'NIDD')
    status = ntn_dongle.get_ntn_status(conn_type)
    if status is None:
        return jsonify({'error': 'Failed to get NTN status'}), 500

    return jsonify(status)

@ntn.route('/api/ntn/device', methods=['GET'])
def get_device_info():
    """Get NTN device information."""
    ntn_dongle = get_ntn_dongle()
    if not ntn_dongle:
        return jsonify({'error': 'Failed to initialize NTN dongle'}), 500

    device_info = ntn_dongle.setup_device()
    if not device_info:
        return jsonify({'error': 'Failed to get device information'}), 500

    return jsonify(device_info)

@ntn.route('/api/ntn/send', methods=['POST'])
def send_data():
    """Send data through NTN dongle."""
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({'error': 'Invalid JSON data'}), 400

    ntn_dongle = get_ntn_dongle()
    if not ntn_dongle:
        return jsonify({'error': 'Failed to initialize NTN dongle'}), 500

    response = ntn_dongle.send_data(data)
    if response is None:
        return jsonify({'error': 'Failed to send data'}), 500

    return jsonify({'response': response})
