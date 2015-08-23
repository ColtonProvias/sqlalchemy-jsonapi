=====================
Preparing Your Models
=====================

Validation
==========
SQLAlchemy-JSONAPI makes use of the SQLAlchemy validates decorator::

        from sqlalchemy.orm import validates

        class User(Base):
            email = Column(Unicode(255))

            @validates('email')
            def validate_email(self, key, email):
                """ Ultra-strong email validation. """
                assert '@' in email, 'Not an email'
                return email

Now raise your hand if you knew SQLAlchemy had that decorator.  Well, now you
know, and it's quite useful!

Attribute Descriptors
=====================

Relationship Descriptors
========================

Permission Testing
==================