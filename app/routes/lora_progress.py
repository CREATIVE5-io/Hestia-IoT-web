"""
LoRa setup progress tracking routes
"""

from flask import Blueprint, jsonify
import json
import os
from app.utils.auth import login_required
from app.models.lora_manager import LoRaConfigManager

lora_progress_bp = Blueprint('lora_progress', __name__)

@lora_progress_bp.route('/lora/progress')
def get_lora_progress():
    """Get current LoRa setup progress"""
    config_manager = LoRaConfigManager()
    progress_file = os.path.join(config_manager.run_dir, 'lora_setup_progress.json')

    try:
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
            
            # Check if progress is stale (older than 30 seconds)
            import time
            if time.time() - progress_data.get('timestamp', 0) > 30:
                # Progress is stale, assume it failed
                return jsonify({
                    'percentage': 100,
                    'message': 'Setup timed out or failed',
                    'setup_status': 'Setup timed out',
                    'failed_devices': ['Timeout'],
                    'completed': True,
                    'error': True
                })
            
            return jsonify(progress_data)
        else:
            # No progress file found
            return jsonify({
                'percentage': 0,
                'message': 'Setup not started',
                'completed': False
            })
    except Exception as e:
        return jsonify({
            'percentage': 100,
            'message': f'Error reading progress: {str(e)}',
            'setup_status': f'Error: {str(e)}',
            'failed_devices': ['Progress error'],
            'completed': True,
            'error': True
        })


@lora_progress_bp.route('/lora/progress/clear')
def clear_lora_progress():
    """Clear LoRa setup progress file"""
    config_manager = LoRaConfigManager()
    progress_file = os.path.join(config_manager.run_dir, 'lora_setup_progress.json')

    try:
        if os.path.exists(progress_file):
            os.remove(progress_file)
        return jsonify({'status': 'cleared'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})