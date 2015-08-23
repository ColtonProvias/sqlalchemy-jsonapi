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

        from sqlalchemy_jsonapi import attr_descriptor, AttributeActions

        class User(Base):
            id = Column(UUIDType)
            # ...

            @attr_descriptor(AttributeActions.GET, 'id')
            def id_getter(self):
                return str(self.id)

            @attr_descriptor(AttributeActions.SET, 'id')
            def id_setter(self, new_id):
                self.id = UUID(new_id)

Relationship Descriptors
========================

Permission Testing
==================