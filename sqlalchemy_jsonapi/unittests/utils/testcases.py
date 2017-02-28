"""Testcases for sqlalchemy_jsonapi unittests."""

import unittest

from sqlalchemy_jsonapi.unittests.main import db


class SqlalchemyJsonapiTestCase(unittest.TestCase):
    """Base test case for all tests."""

    def setUp(self, *args, **kwargs):
        """Update the app config for testing.

        As future testcases require more database insertions prior to testing,
        we will need to perhaps use unittests class methods.
        """
        super(SqlalchemyJsonapiTestCase, self).setUp(*args, **kwargs)
        db.create_all()

    def tearDown(self, *args, **kwargs):
        """Reset the app config."""
        super(SqlalchemyJsonapiTestCase, self).tearDown(*args, **kwargs)
        db.session.remove()
        db.drop_all()
