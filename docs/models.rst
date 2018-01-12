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

Sometimes, you may need to provide your own getters and setters to attributes::

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

Note: id is not able to be altered after initial setting in JSON API to keep it
consistent.

Relationship Descriptors
========================

Relationship's come in two flavors: to-one and to-many (or tranditional and
LDS-flavored if you prefer those terms).  To one descriptors have the actions
GET and SET::

        from sqlalchemy_jsonapi import relationship_descriptor, RelationshipActions

        @relationship_descriptor(RelationshipActions.GET, 'significant_other')
        def getter(self):
            # ...

        @relationship_descriptor(RelationshipActions.SET, 'significant_other')
        def setter(self, value):
            # ...

To-many have GET, APPEND, and DELETE::

        @relationship_descriptor(RelationshipActions.GET, 'angry_exes')
        def getter(self):
            # ...

        @relationship_descriptor(RelationshipActions.APPEND, 'angry_exes')
        def appender(self):
            # ...

        @relationship_descriptor(RelationshipActions.DELETE, 'angry_exes')
        def remover(self):
            # ...


Permission Testing
==================

Permissions are a complex challenge in relational databases.  While the
solution provided right now is extremely simple, it is almost guaranteed to
evolve and change drastically as this library gets used more in production.
Thus it is advisable that on every major version number increment, you should
check this section for changes to permissions.

Anyway, there are currently four permissions that are checked: GET, CREATE,
EDIT, and DELETE. Permission tests can be applied module-wide or to specific
fields::

        @permission_test(Permissions.VIEW)
        def can_view(self):
            return self.is_published

        @permission_test(Permissions.EDIT, 'slug')
        def can_edit_slug(self):
            return False
