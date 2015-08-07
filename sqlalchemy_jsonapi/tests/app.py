"""
SQLAlchemy JSONAPI Test App.

Colton Provias <cj@coltonprovias.com>
MIT License
"""

from uuid import uuid4

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Column, ForeignKey, Unicode, UnicodeText
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship, validates
from sqlalchemy_jsonapi import FlaskJSONAPI
from sqlalchemy_utils import EmailType, PasswordType, Timestamp, UUIDType

app = Flask(__name__)

app.testing = True

db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql+psycopg2://localhost/sqlalchemy_jsonapi'
app.config['SQLALCHEMY_ECHO'] = False


class User(Timestamp, db.Model):

    """Quick and dirty user model."""

    #: If __jsonapi_type__ is not provided, it will use the class name instead.
    __tablename__ = 'users'

    id = Column(UUIDType, default=uuid4, primary_key=True)
    username = Column(Unicode(30), unique=True, nullable=False)
    email = Column(EmailType, nullable=False)
    password = Column(PasswordType(schemes=['bcrypt']), nullable=False, info={'allow_serialize': False})
    is_admin = Column(Boolean, default=False)

    @hybrid_property
    def total_comments(self):
        """
        Total number of comments.

        Provides an example of a computed property.
        """
        return self.comments.count()

    @validates('email')
    def validate_email(self, key, email):
        """Strong email validation."""
        assert '@' in email, 'Not an email'

    @validates('username')
    def validate_username(self, key, username):
        """
        Check the length of the username.

        Here's hoping nobody submits something in unicode that is 31 characters
        long!!
        """
        assert len(username) >= 5 and len(username) <= 30, 'Must be 5 to 30 characters long.'

    @validates('password')
    def validate_password(self, key, password):
        """Validate a password's length."""
        assert len(password) >= 5, 'Password must be 5 characters or longer.'


class Post(Timestamp, db.Model):

    """Post model, as if this is a blog."""

    __tablename__ = 'posts'

    id = Column(UUIDType, default=uuid4, primary_key=True)
    title = Column(Unicode(100), nullable=False)
    slug = Column(Unicode(100))
    content = Column(UnicodeText, nullable=False)
    is_published = Column(Boolean, default=False)
    author_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)

    author = relationship('User', lazy='joined',
                          backref=backref('posts', lazy='dynamic'))

    @validates('title')
    def validate_title(self, key, title):
        """Keep titles from getting too long."""
        assert len(title) >= 5 or len(title) <= 100, 'Must be 5 to 100 '\
            'characters long.'

    def jsonapi_allow_serialize(self):
        return self.is_published


class Comment(Timestamp, db.Model):

    """Comment for each Post."""

    __tablename__ = 'comments'

    id = Column(UUIDType, default=uuid4, primary_key=True)
    post_id = Column(UUIDType, ForeignKey('posts.id'), nullable=False)
    author_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)
    content = Column(UnicodeText, nullable=False)

    post = relationship('Post', lazy='joined',
                        backref=backref('comments', lazy='dynamic'))
    author = relationship('User', lazy='joined',
                          backref=backref('comments', lazy='dynamic'))


api = FlaskJSONAPI(app, db)


if __name__ == '__main__':
    app.run()
