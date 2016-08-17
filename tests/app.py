"""
SQLAlchemy JSONAPI Test App.

This app implements the backend of a web forum.  It's rather simple but
provides us with a more comprehensive example for testing.

Colton Provias <cj@coltonprovias.com>
MIT License
"""

from uuid import uuid4

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Column, Enum, ForeignKey, Unicode, UnicodeText
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship, validates
from sqlalchemy_utils import (EmailType, IPAddressType, PasswordType,
                              Timestamp, URLType, UUIDType)

import enum

# ================================ APP CONFIG ================================

app = Flask(__name__)

app.testing = True

db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SQLALCHEMY_ECHO'] = False

#api = FlaskJSONAPI(app, db)

# ================================== MODELS ==================================


class User(db.Model, Timestamp):
    __tablename__ = 'users'

    id = Column(UUIDType, default=uuid4, primary_key=True, nullable=False)
    email = Column(EmailType, nullable=False)
    display_name = Column(Unicode(100), nullable=False)
    password = Column(PasswordType(schemes=['bcrypt']), nullable=False)
    is_admin = Column(Boolean, default=False)
    last_ip_address = Column(IPAddressType)
    website = Column(URLType)

    @validates('email')
    def validate_email(self, key, email):
        """Strong email validation."""
        assert '@' in email, 'Not an email'
        return email


class Forum(db.Model, Timestamp):
    __tablename__ = 'forums'

    id = Column(UUIDType, default=uuid4, primary_key=True, nullable=False)
    name = Column(Unicode(255), nullable=False)
    can_public_read = Column(Boolean, default=True)
    can_public_write = Column(Boolean, default=True)


class Thread(db.Model, Timestamp):
    __tablename__ = 'threads'

    id = Column(UUIDType, default=uuid4, primary_key=True, nullable=False)
    forum_id = Column(UUIDType, ForeignKey('forums.id'), nullable=False)
    started_by_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)
    title = Column(Unicode(255), nullable=False)


class Post(db.Model, Timestamp):
    __tablename__ = 'posts'

    id = Column(UUIDType, default=uuid4, primary_key=True, nullable=False)
    user_id = Column(UUIDType, ForeignKey('posts.id'), nullable=False)
    content = Column(UnicodeText, nullable=False)
    is_removed = Column(Boolean, default=False)


class ReportTypes(enum.Enum):
    USER = 0
    POST = 1


class Report(db.Model, Timestamp):
    __tablename__ = 'reports'

    id = Column(UUIDType, default=uuid4, primary_key=True, nullable=False)
    report_type = Column(Enum(ReportTypes), nullable=False)
    reporter_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)
    complaint = Column(UnicodeText, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'employee',
        'polymorphic_on': report_type,
        'with_polymorphic': '*'
    }


class UserReport(db.Model):
    __tablename__ = 'user_reports'

    id = Column(
        UUIDType,
        ForeignKey('reports.id'),
        default=uuid4,
        primary_key=True,
        nullable=False)
    user_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)

    __mapper_args__ = {'polymorphic_identity': ReportTypes.USER}


class PostReport(db.Model):
    __tablename__ = 'post_reports'

    id = Column(
        UUIDType,
        ForeignKey('reports.id'),
        default=uuid4,
        primary_key=True,
        nullable=False)
    post_id = Column(UUIDType, ForeignKey('posts.id'), nullable=False)

    __mapper_args__ = {'polymorphic_identity': ReportTypes.POST}

# ============================== EVENT HANDLERS ==============================


@app.before_request
def handle_auth():
    pass

# ============================== API OVERRIDES  ==============================

#@api.wrap_handler(['blog-posts'], [Method.GET], [Endpoint.COLLECTION])
#def sample_override(next, *args, **kwargs):
#    return next(*args, **kwargs)

# ================================ APP RUNNER ================================

if __name__ == '__main__':
    app.run()
