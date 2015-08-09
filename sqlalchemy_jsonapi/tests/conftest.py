"""
SQLAlchemy-JSONAPI Testing Fixtures.

Colton J. Provias <cj@coltonprovias.com>
MIT License
"""

import json

import pytest
from flask import Response
from flask.testing import FlaskClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy_jsonapi.tests.app import db as db_
from sqlalchemy_jsonapi.tests.app import app

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


class TestingResponse(Response):
    def validate(self, status_code, error=None):
        assert self.status_code == status_code
        assert self.headers['Content-Type'] == 'application/vnd.api+json'
        self.json_data = json.loads(self.data.decode())
        return self


@pytest.fixture
def client(flask_app):
    """Set up the testing client."""
    with FlaskClient(flask_app,
                     use_cookies=True,
                     response_wrapper=TestingResponse) as c:
        return c


@pytest.fixture(scope='session')
def fake_data(db):
    pass
