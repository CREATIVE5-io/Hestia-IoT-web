"""
Celery Configuration and Tasks
"""

from celery import Celery
import subprocess


def make_celery(app):
    """Create Celery instance"""
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
    )
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery


# Celery tasks for LoRa setup
def restart_lora_service():
    """Restart LoRa service task"""
    try:
        # This would be customized based on your LoRa service setup
        subprocess.run(['/usr/bin/sudo', '/usr/bin/systemctl', 'restart', 'lora-service'], 
                      capture_output=True, text=True, check=True)
        return {"status": "success", "message": "LoRa service restart initiated"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Error restarting LoRa service: {e.stderr}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error restarting LoRa service: {str(e)}"}