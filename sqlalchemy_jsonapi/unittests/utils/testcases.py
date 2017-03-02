"""Testcases for sqlalchemy_jsonapi unittests."""

import unittest

from sqlalchemy_jsonapi.unittests.models import Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


class SqlalchemyJsonapiTestCase(unittest.TestCase):
    """Base testcase for SQLAclehmy-related tests."""

    def setUp(self, *args, **kwargs):
        """Configure sqlalchemy and session."""
        super(SqlalchemyJsonapiTestCase, self).setUp(*args, **kwargs)
        self.engine = create_engine('sqlite://')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)

    def tearDown(self, *args, **kwargs):
        """Reset the sqlalchemy engine."""
        super(SqlalchemyJsonapiTestCase, self).tearDown(*args, **kwargs)
        Base.metadata.drop_all(self.engine)
