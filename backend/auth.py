import os
from functools import wraps
from flask import session, jsonify
from dotenv import load_dotenv

load_dotenv()

def check_password(provided_password: str, correct_password: str = None) -> bool:
    """
    Check if provided password matches the configured password

    Args:
        provided_password: Password provided by user
        correct_password: Override password (for testing), defaults to env var

    Returns:
        True if password matches, False otherwise
    """
    if correct_password is None:
        correct_password = os.getenv('APP_PASSWORD')

    return provided_password == correct_password

def login_required(f):
    """
    Decorator to require authentication for routes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function
