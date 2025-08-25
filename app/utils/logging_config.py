"""
Logging configuration
"""
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """Setup logging configuration for the application.
    
    Args:
        app: Flask application instance
    """
    log_level = logging.INFO
    if app.debug:
        log_level = logging.DEBUG

    # Create logs directory if it doesn't exist
    log_dir = os.path.join(app.root_path, '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Setup file handler
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'lora-setup.log'),
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(log_level)

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    console_handler.setLevel(logging.INFO)  # Show info and above in console

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Set specific levels for verbose modules
    logging.getLogger('werkzeug').setLevel(logging.INFO)  # Allow Flask development server messages
    logging.getLogger('app.models').setLevel(logging.INFO)   # Reduce model debug output
