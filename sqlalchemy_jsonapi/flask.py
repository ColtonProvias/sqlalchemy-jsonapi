"""
SQLAlchemy-JSONAPI Flask Adapter.

Colton J. Provias
MIT License
"""

import datetime
import json
import uuid

from blinker import signal
from enum import Enum
from flask import make_response, request

from .errors import BaseError, MissingContentTypeError
from .serializer import JSONAPI


class Method(Enum):
    """ HTTP Methods used in JSON API. """

    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    DELETE = 'DELETE'


class Endpoint(Enum):
    """ The four endpoint paths of JSON API. """

    COLLECTION = '/<api_type>/'
    RESOURCE = '/<api_type>/<obj_id>/'
    RELATED = '/<api_type>/<obj_id>/<relationship>/'
    RELATIONSHIP = '/<api_type>/<obj_id>/relationships/<relationship>/'


class JSONAPIEncoder(json.JSONEncoder):
    """ JSONEncoder that handles UUID and datetime. """

    def default(self, value):
        """ Handle UUID, datetime, and callables. """
        if isinstance(value, uuid.UUID):
            return str(value)
        elif isinstance(value, datetime.datetime):
            return value.isoformat()
        elif callable(value):
            return str(value)
        return json.JSONEncoder.default(self, value)


views = [
    (Method.GET, Endpoint.COLLECTION),
    (Method.GET, Endpoint.RESOURCE),
    (Method.GET, Endpoint.RELATED),
    (Method.GET, Endpoint.RELATIONSHIP),
    (Method.POST, Endpoint.COLLECTION),
    (Method.POST, Endpoint.RELATIONSHIP),
    (Method.PATCH, Endpoint.RESOURCE),
    (Method.PATCH, Endpoint.RELATIONSHIP),
    (Method.DELETE, Endpoint.RESOURCE),
    (Method.DELETE, Endpoint.RELATIONSHIP)
]


def override(original, results):
    overrides = [v for fn, v in results if v is not None]
    if len(overrides) == 0:
        return original
    return overrides[-1]


class FlaskJSONAPI(object):

    on_request = signal('jsonapi-on-request')
    on_response = signal('jsonapi-on-response')
    on_success = signal('jsonapi-on-success')
    on_error = signal('jsonapi-on-error')

    def __init__(self, app=None, sqla=None, namespace='api',
            route_prefix='/api'):
        self.app = app
        self.sqla = sqla

        if app is not None:
            self.setup_adapter(namespace, route_prefix)

    def init_app(self, app, sqla, namespace='api', route_prefix='/api'):
        self.app = app
        self.sqla = sqla

        self.setup_adapter(namespace, route_prefix)

    def setup_adapter(self, namespace, route_prefix):
        self.serializer = JSONAPI(self.sqla.Model)
        for view in views:
            method, endpoint = view
            self.app.add_url_rule(route_prefix + endpoint.value,
                                  '{}_{}_{}'.format(namespace,
                                                    method.name,
                                                    endpoint.name),
                                  self.generate_view(method, endpoint),
                                  methods=[method.name])

    def generate_view(self, method, endpoint):
        def new_view(**kwargs):
            if method == Method.GET:
                data = request.args
            else:
                if request.headers.get('content-type', None) != 'application/vnd.api+json':
                    response = make_response(json.dumps(MissingContentTypeError().data, cls=JSONAPIEncoder))
                    response.status_code = 409
                    response.content_type = 'application/vnd.api+json'
                    return response
                data = request.get_json(force=True)
            data = override(data,
                            self.on_request.send(self,
                                                 method=method,
                                                 endpoint=endpoint,
                                                 data=data,
                                                 req_args=kwargs))
            try:
                handler = getattr(self.serializer,
                                  '{}_{}'.format(method.name.lower(),
                                                 endpoint.name.lower()))
                response = handler(self.sqla.session, data, kwargs)
                response = override(response,
                                    self.on_success.send(self,
                                                         method=method,
                                                         endpoint=endpoint,
                                                         data=data,
                                                         req_args=kwargs,
                                                         response=response))
            except BaseError as exc:
                self.sqla.session.rollback()
                response = override(exc,
                                    self.on_error.send(self,
                                                       method=method,
                                                       endpoint=endpoint,
                                                       data=data,
                                                       req_args=kwargs,
                                                       error=exc))
            rendered_response = make_response()
            if response.status_code != 204:
                rendered_response = make_response(
                    json.dumps(response.data, cls=JSONAPIEncoder)
                )
            rendered_response.status_code = response.status_code
            rendered_response.content_type = 'application/vnd.api+json'
            return override(rendered_response,
                            self.on_response.send(self,
                                                  method=method,
                                                  endpoint=endpoint,
                                                  data=data,
                                                  req_args=kwargs,
                                                  response=rendered_response))
        return new_view
