"""
SQLAlchemy-JSONAPI Testing Fixtures.

Colton J. Provias <cj@coltonprovias.com>
MIT License
"""

import json

import jsonschema
import pytest
from addict import Dict
from faker import Faker
from flask import Response
from flask.testing import FlaskClient
from sqlalchemy.orm import sessionmaker

from app import db as db_
from app import app

Session = sessionmaker()

fake = Faker()

with open('tests/jsonapi_schema.json', 'r') as f:
    api_schema = json.load(f)


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
def session(request, db):
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
        print(self.data)
        assert self.status_code == status_code
        assert self.headers['Content-Type'] == 'application/vnd.api+json'
        if status_code != 204:
            json_data = json.loads(self.data.decode())
            jsonschema.validate(json_data, api_schema)
            self.json_data = Dict(json_data)
            if error:
                assert self.status_code == error.status_code
                assert self.json_data['errors'][0]['code'] == error.code
                assert self.json_data['errors'][0][
                    'status'] == error.status_code
        return self


@pytest.fixture
def client(flask_app):
    """Set up the testing client."""
    with FlaskClient(
            flask_app, use_cookies=True,
            response_wrapper=TestingResponse) as c:
        return c
