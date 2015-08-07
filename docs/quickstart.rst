==========
Quickstart
==========
.. currentmodule:: sqlalchemy_jsonapi

Installation
============

Installation of SQLAlchemy-JSONAPI can be done via pip::

    pip install -U sqlalchemy_jsonapi

Attaching to MetaData
=====================

To initialize the serializer, you first have to attach it to an instance of
SQLAlchemy's metadata that is connected to your models::

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

    serializer = JSONAPI(Base.metadata)

Serialization
=============

Now that your serializer is initialized, you can quickly and easily serialize
your models.  Let's do a simple collection serialization::

    @app.route('/api/users')
    def users_list():
        serialized = serializer.get(db.session, User, args=request.args)
        return jsonify(serialized)

Deserialization
===============

Deserialization is also quick and easy::

    @app.route('/api/users/<user_id>', methods=['PATCH'])
    def update_user(user_id):
        json_data = request.get_json(force=True)
        json_response = serializer.patch(db.session, User, user_id, data=json_data)
        return jsonify(json_response)

If you use Flask, this can be automated and simplified via the included Flask
module.