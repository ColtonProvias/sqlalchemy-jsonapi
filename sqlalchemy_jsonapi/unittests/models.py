"""Model file for unit testing."""

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, validates

from sqlalchemy_jsonapi import (
    Permissions, permission_test, ALL_PERMISSIONS,
    JSONAPI, AttributeActions, attr_descriptor
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

    # For demonstration purposes, we want to store
    # the first name as SET-ATTR:first in database.
    @attr_descriptor(AttributeActions.SET, 'first')
    def set_first_to_start_with_set_attr(self, new_first):
        self.first = 'SET-ATTR:{0}'.format(new_first)

    # For demonstration purposes, we don't want to show
    # how we stored first internally in database.
    @attr_descriptor(AttributeActions.GET, 'first')
    def get_first_starts_with_get_attr(self):
        if 'SET-ATTR:' in self.first:
            return self.first[9::]
        return self.first


class Post(Base):
    """A blog post model."""

    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))

    author = relationship('User',
                          lazy='joined',
                          backref=backref('posts',
                                          lazy='dynamic',
                                          cascade='all,delete'))


class Comment(Base):
    """Comment for each Post."""

    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'))
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)

    post = relationship('Post',
                        lazy='joined',
                        backref=backref('comments',
                                        lazy='dynamic', cascade='all,delete'))
    author = relationship('User',
                          lazy='joined',
                          backref=backref('comments',
                                          lazy='dynamic'))


class Log(Base):
    """Log information model."""

    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship(
        'User', lazy='joined', backref=backref('logs', lazy='dynamic'))

    @permission_test(ALL_PERMISSIONS)
    def block_interactive(cls):
        """Unable to Create, Edit, or Delete a log."""
        return False


serializer = JSONAPI(Base)
