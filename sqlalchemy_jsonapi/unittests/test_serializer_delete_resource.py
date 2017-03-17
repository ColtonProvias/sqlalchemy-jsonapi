"""Test for serializer's delete_resource."""

from sqlalchemy_jsonapi import errors

from sqlalchemy_jsonapi.unittests.utils import testcases
from sqlalchemy_jsonapi.unittests import models


class DeleteResource(testcases.SqlalchemyJsonapiTestCase):
    """Tests for serializer.delete_resource."""

    def test_delete_resource_successs_response(self):
        """Delete a resource successfully returns 204."""
        user = models.User(
            first='Sally', last='Smith',
            username='SallySmith1', password='password')
        self.session.add(user)
        self.session.commit()

        response = models.serializer.delete_resource(
            self.session, {}, 'users', user.id)

        expected = {
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(204, response.status_code)
