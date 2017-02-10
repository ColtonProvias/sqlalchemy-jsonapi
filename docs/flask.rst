=====
Flask
=====

.. currentmodule:: sqlalchemy_jsonapi.flask

To those who use Flask, setting up SQLAlchemy-JSONAPI can be extremely complex
and frustrating.  Let's look at an example::

        from sqlalchemy_jsonapi import FlaskJSONAPI

        app = Flask(__name__)
        db = SQLAlchemy(app)
        api = FlaskJSONAPI(app, db)

And after all that work, you should now have a full working API.

Signals
=======

As Flask makes use of signals via Blinker, it would be appropriate to make use
of them in the Flask module for SQLALchemy-JSONAPI.  If a signal receiver
returns a value, it can alter the final response.

on_request
----------

Triggered before serialization::

        @api.on_request.connect
        def process_api_request(sender, method, endpoint, data, req_args):
            # Handle the request

on_success
----------

Triggered after successful serialization::

        @api.on_success.connect
        def process_api_success(sender, method, endpoint, data, req_args, response):
            # Handle the response dictionary


on_error
--------

Triggered after failed handling::

        @api.on_error.connect
        def process_api_error(sender, method, endpoint, data, req_args, error):
            # Handle the error

on_response
-----------

Triggered after rendering of response::

        @api.on_response.connect
        def process_api_response(sender, method, endpoint, data, req_args, rendered_response):
            # Handle the rendered response

Wrapping the Handlers
=====================

While signals provide some control, sometimes you want to wrap or override the handler for the particular endpoint and method.  This can be done through a specialized decorator that allows you to specify in what cases you want the handler wrapped::

        @api.wrap_handler(['users'], [Methods.GET], [Endpoints.COLLECTION, Endpoints.RESOURCE])
        def log_it(next, *args, **kwargs):
            logging.info('In a wrapped handler!')
            return next(*args, **kwargs)

Handlers are placed into a list and run in order of placement within the list.  That means you can perform several layers of checks and override as needed.

API
===

.. autoclass:: FlaskJSONAPI
    :members:
