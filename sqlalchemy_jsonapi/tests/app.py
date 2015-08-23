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
from sqlalchemy_jsonapi import FlaskJSONAPI, Permissions, permission_test
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
    password = Column(PasswordType(schemes=['bcrypt']),
                      nullable=False,
                      info={'allow_serialize': False})
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
        return email

    @validates('username')
    def validate_username(self, key, username):
        """
        Check the length of the username.

        Here's hoping nobody submits something in unicode that is 31 characters
        long!!
        """
        assert len(username) >= 4 and len(
            username) <= 30, 'Must be 4 to 30 characters long.'
        return username

    @validates('password')
    def validate_password(self, key, password):
        """Validate a password's length."""
        assert len(password) >= 5, 'Password must be 5 characters or longer.'
        return password

    @permission_test(Permissions.VIEW, 'password')
    def view_password(self):
        """ Never let the password be seen. """
        return False

    @permission_test(Permissions.EDIT)
    def allow_edit(self):
        """ We want our users to be uneditable. """
        return False

    @permission_test(Permissions.DELETE)
    def allow_delete(self):
        """ Just like a popular social media site, we won't delete users. """
        return False


class Post(Timestamp, db.Model):
    """Post model, as if this is a blog."""

    __tablename__ = 'posts'

    id = Column(UUIDType, default=uuid4, primary_key=True)
    title = Column(Unicode(100), nullable=False)
    slug = Column(Unicode(100))
    content = Column(UnicodeText, nullable=False)
    is_published = Column(Boolean, default=False)
    author_id = Column(UUIDType, ForeignKey('users.id'))

    author = relationship('User',
                          lazy='joined',
                          backref=backref('posts',
                                          lazy='dynamic'))

    @validates('title')
    def validate_title(self, key, title):
        """Keep titles from getting too long."""
        assert len(title) >= 5 or len(
            title) <= 100, 'Must be 5 to 100 characters long.'
        return title

    @permission_test(Permissions.VIEW)
    def allow_view(self):
        """ Hide unpublished. """
        return self.is_published

    @permission_test(Permissions.DELETE, 'logs')
    def prevent_deletion_of_logs(self):
        return False


class Comment(Timestamp, db.Model):
    """Comment for each Post."""

    __tablename__ = 'comments'

    id = Column(UUIDType, default=uuid4, primary_key=True)
    post_id = Column(UUIDType, ForeignKey('posts.id'))
    author_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)
    content = Column(UnicodeText, nullable=False)

    post = relationship('Post',
                        lazy='joined',
                        backref=backref('comments',
                                        lazy='dynamic'))
    author = relationship('User',
                          lazy='joined',
                          backref=backref('comments',
                                          lazy='dynamic'))


class Log(Timestamp, db.Model):
    __tablename__ = 'logs'
    id = Column(UUIDType, default=uuid4, primary_key=True)
    post_id = Column(UUIDType, ForeignKey('posts.id'))
    user_id = Column(UUIDType, ForeignKey('users.id'))

    post = relationship('Post',
                        lazy='joined',
                        backref=backref('logs',
                                        lazy='dynamic'))
    user = relationship('User',
                        lazy='joined',
                        backref=backref('logs',
                                        lazy='dynamic'))

    @permission_test(Permissions.CREATE)
    def block_create(cls):
        return False

    @permission_test(Permissions.EDIT)
    def block_edit(cls):
        return False


api = FlaskJSONAPI(app, db)

if __name__ == '__main__':
    app.run()
