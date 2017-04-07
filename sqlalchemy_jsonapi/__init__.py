from .constants import Endpoint, Method  # NOQA
from .serializer import (  # NOQA
    ALL_PERMISSIONS, INTERACTIVE_PERMISSIONS, JSONAPI, AttributeActions,
    Permissions, RelationshipActions, attr_descriptor, permission_test,
    relationship_descriptor)
from ._version import __version__  # NOQA

try:
    from .flaskext import FlaskJSONAPI
except ImportError:
    FlaskJSONAPI = None
