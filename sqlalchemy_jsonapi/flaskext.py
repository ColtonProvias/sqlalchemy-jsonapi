"""
SQLAlchemy-JSONAPI
Flask Adapter
Colton J. Provias
MIT License
"""

import datetime
import json
import uuid

from blinker import signal
from flask import make_response, request

from .errors import BaseError, MissingContentTypeError
from .serializer import JSONAPI

try:
    from enum import Enum
except ImportError:
    from enum34 import Enum


class Method(Enum):
    """ HTTP Methods used by JSON API """

    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    DELETE = 'DELETE'


class Endpoint(Enum):
    """ Four paths specified in JSON API """

    COLLECTION = '/<api_type>/'
    RESOURCE = '/<api_type>/<obj_id>/'
    RELATED = '/<api_type>/<obj_id>/<relationship>/'
    RELATIONSHIP = '/<api_type>/<obj_id>/relationships/<relationship>/'


class JSONAPIEncoder(json.JSONEncoder):
    """ JSONEncoder Implementation that allows for UUID and datetime """

    def default(self, value):
        """
        Handle UUID, datetime, and callables.

        :param value: Value to encode
        """
        if isinstance(value, uuid.UUID):
            return str(value)
        elif isinstance(value, datetime.datetime):
            return value.isoformat()
        elif callable(value):
            return str(value)
        return json.JSONEncoder.default(self, value)

#: The views to generate
views = [
    (Method.GET, Endpoint.COLLECTION), (Method.GET, Endpoint.RESOURCE),
    (Method.GET, Endpoint.RELATED), (Method.GET, Endpoint.RELATIONSHIP),
    (Method.POST, Endpoint.COLLECTION), (Method.POST, Endpoint.RELATIONSHIP),
    (Method.PATCH, Endpoint.RESOURCE), (Method.PATCH, Endpoint.RELATIONSHIP),
    (Method.DELETE, Endpoint.RESOURCE), (Method.DELETE, Endpoint.RELATIONSHIP)
]


def override(original, results):
    """
    If a receiver to a signal returns a value, we override the original value
    with the last returned value.

    :param original: The original value
    :param results: The results from the signal
    """
    overrides = [v for fn, v in results if v is not None]
    if len(overrides) == 0:
        return original
    return overrides[-1]


class FlaskJSONAPI(object):
    """ Flask Adapter """

    #: Fires before the serializer is called.  Functions should implement the
    #: following args: (sender, method, endpoint, data, req_args)
    on_request = signal('jsonapi-on-request')

    #: Fires before we return the response.  Included args are:
    #: (sender, method, endpoint, data, req_args, rendered_response)
    on_response = signal('jsonapi-on-response')

    #: Fires after a successful call to the serializer.
    #: (sender, method, endpoint, data, req_args, response)
    on_success = signal('jsonapi-on-success')

    #: Fires when an error is encountered.
    #: (sender, method, endpoint, data, req_args, error)
    on_error = signal('jsonapi-on-error')

    def __init__(self,
                 app=None,
                 sqla=None,
                 namespace='api',
                 route_prefix='/api'):
        """
        Initialize the adapter.  If app isn't passed here, it should be passed
        in init_app.

        :param app: Flask application
        :param sqla: Flask-SQLAlchemy instance
        :param namespace: Prefixes all generated routes
        :param route_prefix: The base path for the generated routes
        """
        self.app = app
        self.sqla = sqla

        if app is not None:
            self._setup_adapter(namespace, route_prefix)

    def init_app(self, app, sqla, namespace='api', route_prefix='/api'):
        """
        Initialize the adapter if it hasn't already been initialized.

        :param app: Flask application
        :param sqla: Flask-SQLAlchemy instance
        :param namespace: Prefixes all generated routes
        :param route_prefix: The base path for the generated routes
        """
        self.app = app
        self.sqla = sqla

        self._setup_adapter(namespace, route_prefix)

    def _setup_adapter(self, namespace, route_prefix):
        """
        Initialize the serializer and loop through the views to generate them.

        :param namespace: Prefix for generated endpoints
        :param route_prefix: Prefix for route patterns
        """
        self.serializer = JSONAPI(self.sqla.Model)
        for view in views:
            method, endpoint = view
            pattern = route_prefix + endpoint.value
            name = '{}_{}_{}'.format(namespace, method.name, endpoint.name)
            view = self._generate_view(method, endpoint)
            self.app.add_url_rule(pattern, name, view, methods=[method.name])

    def _generate_view(self, method, endpoint):
        """
        Generate a view for the specified method and endpoint.

        :param method: HTTP Method
        :param endpoint: Pattern
        """

        def new_view(**kwargs):
            if method == Method.GET:
                data = request.args
            else:
                if int(request.headers.get('content-length', 0)) > 0:
                    content_type = request.headers.get('content-type', None)
                    if content_type != 'application/vnd.api+json':
                        data = MissingContentTypeError().data
                        data = json.dumps(data, cls=JSONAPIEncoder)
                        response = make_response(data)
                        response.status_code = 409
                        response.content_type = 'application/vnd.api+json'
                        return response
                    data = request.get_json(force=True)
                else:
                    data = None

            event_kwargs = {
                'method': method,
                'endpoint': endpoint,
                'data': data,
                'req_args': kwargs
            }
            results = self.on_request.send(self, **event_kwargs)
            data = override(data, results)

            args = [self.sqla.session, data, kwargs['api_type']]
            if 'obj_id' in kwargs.keys():
                args.append(kwargs['obj_id'])
            if 'relationship' in kwargs.keys():
                args.append(kwargs['relationship'])

            try:
                attr = '{}_{}'.format(method.name, endpoint.name).lower()
                handler = getattr(self.serializer, attr)
                response = handler(*args)
                results = self.on_success.send(self,
                                               response=response,
                                               **event_kwargs)
                response = override(response, results)
            except BaseError as exc:
                self.sqla.session.rollback()
                results = self.on_error.send(self, error=exc, **event_kwargs)
                response = override(exc, results)
            rendered_response = make_response()
            if response.status_code != 204:
                data = json.dumps(response.data, cls=JSONAPIEncoder)
                rendered_response = make_response(data)
            rendered_response.status_code = response.status_code
            rendered_response.content_type = 'application/vnd.api+json'
            results = self.on_response.send(self,
                                            response=rendered_response,
                                            **event_kwargs)
            return override(rendered_response, results)

        return new_view
