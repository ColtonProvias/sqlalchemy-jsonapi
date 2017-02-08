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
from app import db as db_
from app import app, User, BlogPost, BlogComment, Log
from faker import Faker

Session = sessionmaker()

fake = Faker()


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
            self.json_data = json.loads(self.data.decode())
            if error:
                assert self.status_code == error.status_code
                assert self.json_data['errors'][0]['code'] == error.code
                assert self.json_data['errors'][0]['status'
                                                   ] == error.status_code
        return self


@pytest.fixture
def client(flask_app):
    """Set up the testing client."""
    with FlaskClient(flask_app,
                     use_cookies=True,
                     response_wrapper=TestingResponse) as c:
        return c


@pytest.fixture
def user(session):
    new_user = User(email=fake.email(),
                    password=fake.sentence(),
                    username=fake.user_name())
    session.add(new_user)
    session.commit()
    return new_user


@pytest.fixture
def post(user, session):
    new_post = BlogPost(author=user,
                    title=fake.sentence(),
                    content=fake.paragraph(),
                    is_published=True)
    session.add(new_post)
    session.commit()
    return new_post


@pytest.fixture
def unpublished_post(user, session):
    new_post = BlogPost(author=user,
                    title=fake.sentence(),
                    content=fake.paragraph(),
                    is_published=False)
    session.add(new_post)
    session.commit()
    return new_post


@pytest.fixture
def bunch_of_posts(user, session):
    for x in range(30):
        new_post = BlogPost(author=user,
                        title=fake.sentence(),
                        content=fake.paragraph(),
                        is_published=fake.boolean())
        session.add(new_post)
        new_post.comments.append(BlogComment(author=user,
                                         content=fake.paragraph()))
    session.commit()


@pytest.fixture
def comment(user, post, session):
    new_comment = BlogComment(author=user, post=post, content=fake.paragraph())
    session.add(new_comment)
    session.commit()
    return new_comment


@pytest.fixture
def log(user, post, session):
    new_log = Log(user=user, post=post)
    session.add(new_log)
    session.commit()
    return new_log
