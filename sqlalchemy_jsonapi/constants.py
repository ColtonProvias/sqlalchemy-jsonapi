"""
SQLAlchemy-JSONAPI
Constants
Colton J. Provias
MIT License
"""


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

    COLLECTION = '/<api_type>'
    RESOURCE = '/<api_type>/<obj_id>'
    RELATED = '/<api_type>/<obj_id>/<relationship>'
    RELATIONSHIP = '/<api_type>/<obj_id>/relationships/<relationship>'