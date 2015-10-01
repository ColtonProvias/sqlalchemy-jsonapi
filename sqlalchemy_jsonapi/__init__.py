try:
    from .flaskext import FlaskJSONAPI, Method, Endpoint
except ImportError:
    FlaskJSONAPI, Method, Endpoint = None, None, None

from .serializer import (JSONAPI, AttributeActions, RelationshipActions,
                         Permissions, attr_descriptor, relationship_descriptor,
                         permission_test, INTERACTIVE_PERMISSIONS,
                         ALL_PERMISSIONS)
