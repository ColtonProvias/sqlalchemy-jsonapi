=====
Flask
=====

.. currentmodule:: sqlalchemy_jsonapi.flask

To those who use Flask, setting up SQLAlchemy-JSONAPI can be extremely complex
and frustrating.  Let's look at an example::

        from sqlalchemy_jsonapi import FlaskJSONAPI

        app = Flask(__name__)
        db = SQLAlchemy(app)
        FlaskJSONAPI(app, db)

And after all that work, you should now have a full working API.

Signals
=======

on_request
----------

on_success
----------

on_error
--------

on_response
-----------

.. autoclass:: FlaskJSONAPI
    :members:
