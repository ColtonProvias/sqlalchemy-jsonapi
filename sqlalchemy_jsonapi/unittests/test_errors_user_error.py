"""Test for error's user_error."""

import json
import unittest

from sqlalchemy_jsonapi import errors


class TestUserError(unittest.TestCase):
    """Tests for errors.user_error."""

    def test_user_error(self):
        """Create user error succesfully."""
        status_code = 400
        title = 'User Error Occured'
        detail = 'Testing user error'
        pointer = '/test'

        actual = errors.user_error(
            status_code, title, detail, pointer)

        data = {
            'errors': [{
                'status': status_code,
                'source': {'pointer': '{0}'.format(pointer)},
                'title': title,
                'detail': detail,
            }],
            'jsonapi': {
                'version': '1.0'
            },
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            }
        }
        expected = json.dumps(data), status_code
        self.assertEqual(expected, actual)
