""""Model file used for unit testing.

More elaborate models will need to be added
as more tests are added. For example when testing
relationships and permissions.
"""


from sqlalchemy_jsonapi.unittests.main import db

from sqlalchemy_jsonapi import JSONAPI


class User(db.Model):
    """Simple user model."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String(50), nullable=False)
    last = db.Column(db.String(50), nullable=False)


serializer = JSONAPI(db.Model)
