==========
Quickstart
==========
.. currentmodule:: sqlalchemy_jsonapi

Installation
============

Installation of SQLAlchemy-JSONAPI can be done via pip::

    pip install -U sqlalchemy_jsonapi

Attaching to Declarative Base
=============================

To initialize the serializer, you first have to attach it to an instance of
SQLAlchemy's Declarative Base that is connected to your models::

    from sqlalchemy_jsonapi import JSONAPI

    class User(Base):
        __tablename__ = 'users'
        id = Column(UUIDType, primary_key=True)
        # ...

    class Address(Base):
        __tablename__ = 'address'
        id = Column(UUIDType, primary_key=True)
        user_id = Column(UUIDType, ForeignKey('users.id'))
        # ...

    serializer = JSONAPI(Base)

Serialization
=============

Now that your serializer is initialized, you can quickly and easily serialize
your models.  Let's do a simple collection serialization::

    @app.route('/api/users')
    def users_list():
        response = serializer.get_collection(db.session, {}, 'users')
        return jsonify(response.data)

The third argument to `get_collection` where `users` is specified is
the model type. This is auto-generated from the model name, but you
can control this using `__jsonapi_type_override__`.

This is useful when you don't want hyphenated type names. For example,
a model named `UserConfig` will have a generated type of `user-config`.
You can change this declaratively on the model::

    class UserConfig(Base):
        __tablename__ = 'userconfig'
        __jsonapi_type_override__ = 'userconfig'

Deserialization
===============

Deserialization is also quick and easy::

    @app.route('/api/users/<user_id>', methods=['PATCH'])
    def update_user(user_id):
        json_data = request.get_json(force=True)
        response = serializer.patch_resource(db.session, json_data, 'users', user_id)
        return jsonify(response.data)

If you use Flask, this can be automated and simplified via the included Flask
module.
