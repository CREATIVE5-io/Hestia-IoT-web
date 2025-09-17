"""
LoRa Setup Flask Application Factory
"""

import os
from flask import Flask
from app.config.settings import Config
from app.utils.celery_config import make_celery
from app.utils.logging_config import setup_logging

def create_app(config_class=Config):
    """Create and configure Flask application"""

    # Get the absolute path of the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    app = Flask(__name__,
                template_folder=os.path.abspath(os.path.join(project_root, 'templates')),
                static_folder=os.path.abspath(os.path.join(project_root, 'static')),
                static_url_path='/static')
    
    # Configure the application
    app.config.from_object(config_class)
    
    # Enable debug mode if configured
    if app.config.get('DEBUG', False):
        app.debug = True
    
    # Setup logging
    setup_logging(app)
    
    # Initialize Celery
    celery = make_celery(app)
    app.celery = celery

    # Register blueprints
    #from app.routes.auth import auth_bp
    from app.routes.lora import lora_bp
    from app.routes.lora_progress import lora_progress_bp
    from app.routes.hestia import hestia
    
    #app.register_blueprint(auth_bp)
    app.register_blueprint(lora_bp)
    app.register_blueprint(lora_progress_bp)
    app.register_blueprint(hestia)
    
    return app