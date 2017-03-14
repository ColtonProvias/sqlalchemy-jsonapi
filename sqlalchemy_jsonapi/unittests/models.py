"""Model file for unit testing."""

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, validates

from sqlalchemy_jsonapi import (
    Permissions, permission_test, JSONAPI
)


Base = declarative_base()


class User(Base):
    """Simple user model."""

    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first = Column(String(50), nullable=False)
    last = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(50), nullable=False)

    @permission_test(Permissions.VIEW, 'password')
    def view_password(self):
        """Password shall never be seen in a view."""
        return False

    @validates('password', 'username', 'first', 'last')
    def empty_attributes_not_allowed(self, key, value):
        assert value, 'Empty value not allowed for {0}'.format(key)
        return value


class Post(Base):
    """A blog post model."""

    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'))

    author = relationship(
        'User', lazy='joined', backref=backref('posts', lazy='dynamic'))


serializer = JSONAPI(Base)
