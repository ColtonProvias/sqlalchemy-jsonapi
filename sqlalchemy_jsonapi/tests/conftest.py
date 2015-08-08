"""
SQLAlchemy-JSONAPI Testing Fixtures.

Colton J. Provias <cj@coltonprovias.com>
MIT License
"""

import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy_jsonapi.tests.app import app, db as db_

Session = sessionmaker()


@pytest.yield_fixture(scope='session')
def flask_app():
    """Set up the application context for testing."""
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.yield_fixture(scope='session')
def db(flask_app):
    """Set up the database as a session-wide fixture."""
    db_.app = flask_app
    db_.drop_all()
    db_.create_all()
    yield db_


@pytest.yield_fixture(scope='function')
def session(db):
    """Create the transaction for each function so we don't rebuild."""
    connection = db.engine.connect()
    transaction = connection.begin()
    options = {'bind': connection}
    session = db.create_scoped_session(options=options)
    yield session
    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture
def client(flask_app):
    """Set up the testing client."""
    with flask_app.test_client() as c:
        return c
