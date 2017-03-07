"""Test for serializer's post_collection."""

from sqlalchemy_jsonapi.unittests.utils import testcases
from sqlalchemy_jsonapi.unittests.models import serializer


class PostCollection(testcases.SqlalchemyJsonapiTestCase):
    """Tests for serializer.post_collection."""

    def test_201_resource_creation(self):
        """Create resource object succesfully."""
        payload = {
            'data': {
                'type': 'users',
                'attributes': {
                    'first': 'Sally',
                    'last': 'Smith'
                }
            }
        }
        response = serializer.post_collection(self.session, payload, 'users')

        expected_response = {
            'data': {
                'attributes': {
                    'first': 'Sally',
                    'last': 'Smith'
                },
                'id': 1,
                'relationships': {},
                'type': 'users'
            },
            'included': [],
            'jsonapi': {
                'version': '1.0'
            },
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            }
        }

        actual = response.data
        self.assertEqual(expected_response, actual)
        self.assertEqual(201, response.status_code)
