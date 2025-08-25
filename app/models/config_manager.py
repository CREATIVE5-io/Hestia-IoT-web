"""
Configuration file management models
"""

import configparser
import logging
import os
import platform

logger = logging.getLogger(__name__)

class ConfigManager:
    """Base configuration manager"""
    
    def __init__(self):
        self.system = platform.system()
        self._setup_paths()
    
    def _setup_paths(self):
        """Setup configuration paths based on operating system"""
        # Get the project root directory (2 levels up from this file)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        self.run_dir = project_root
        logger.debug(f"Project root directory: {self.run_dir}")
        
        # Ensure directory exists
        os.makedirs(self.run_dir, exist_ok=True)