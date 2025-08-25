"""
Authentication utilities
"""

from functools import wraps
from flask import session, redirect, url_for, current_app


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def check_credentials(username, password):
    """Check if provided credentials are valid"""
    return (username == current_app.config['VALID_USERNAME'] and 
            password == current_app.config['VALID_PASSWORD'])