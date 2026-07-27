import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import create_app

@pytest.fixture
def app():
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test'
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()