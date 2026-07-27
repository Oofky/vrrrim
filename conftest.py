import pytest
import os

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['FLASK_KEY'] = 'test-secret-key'

from app import create_app, db as _db

@pytest.fixture(scope='session')
def app():
    flask_app = create_app()
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
    })

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()

@pytest.fixture
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def registered_user(client, db):
    client.post('/', data={
        'clicked': 'signup',
        'username': 'testuser',
        'password': 'testpass'
    })
    return {'username': 'testuser', 'password': 'testpass'}

@pytest.fixture
def logged_in_client(client, registered_user):
    client.post('/', data={
        'clicked': 'login',
        'username': registered_user['username'],
        'password': registered_user['password']
    })
    return client