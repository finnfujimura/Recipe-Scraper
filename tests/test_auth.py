import pytest
from flask import Flask
from backend.auth import check_password, login_required

def test_check_password_correct():
    """Test that correct password returns True"""
    # We'll use a test password
    assert check_password("testpassword", "testpassword") == True

def test_check_password_incorrect():
    """Test that incorrect password returns False"""
    assert check_password("wrongpassword", "testpassword") == False

def test_login_required_decorator():
    """Test that login_required blocks unauthenticated requests"""
    app = Flask(__name__)
    app.secret_key = 'test_secret'

    @app.route('/protected')
    @login_required
    def protected_route():
        return 'Access granted'

    with app.test_client() as client:
        # Without login, should return 401
        response = client.get('/protected')
        assert response.status_code == 401

        # With login session
        with client.session_transaction() as sess:
            sess['authenticated'] = True

        response = client.get('/protected')
        assert response.status_code == 200
        assert b'Access granted' in response.data
