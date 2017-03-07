"""Model file for unit testing."""

from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_jsonapi import JSONAPI


Base = declarative_base()


class User(Base):
    """Simple user model."""

    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first = Column(String(50), nullable=False)
    last = Column(String(50), nullable=False)


serializer = JSONAPI(Base)
