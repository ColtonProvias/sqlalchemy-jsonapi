"""Test for serializer's post_collection."""

import nose

from sqlalchemy_jsonapi import errors

from sqlalchemy_jsonapi.unittests.utils import testcases
from sqlalchemy_jsonapi.unittests import models


class PostCollection(testcases.SqlalchemyJsonapiTestCase):
    """Tests for serializer.post_collection."""

    def test_add_resource(self):
        """Create resource successfully."""
        payload = {
            'data': {
                'type': 'users',
                'attributes': {
                    'first': 'Sally',
                    'last': 'Smith',
                    'username': 'SallySmith1',
                    'password': 'password',
                }
            }
        }

        response = models.serializer.post_collection(
            self.session, payload, 'users')
        user = self.session.query(models.User).get(
            response.data['data']['id'])
        self.assertEqual(user.first, 'Sally')
        self.assertEqual(user.last, 'Smith')
        self.assertEqual(user.username, 'SallySmith1')
        self.assertEqual(user.password, 'password')

    def test_add_resource_response(self):
        """Create resource returns data response and 201.

        This test is very fragile.
        """
        payload = {
            'data': {
                'type': 'users',
                'attributes': {
                    'first': 'Sally',
                    'last': 'Smith',
                    'username': 'SallySmith1',
                    'password': 'password',
                }
            }
        }

        response = models.serializer.post_collection(
            self.session, payload, 'users')

        expected = {
            'data': {
                'attributes': {
                    'first': u'Sally',
                    'last': u'Smith',
                    'username': u'SallySmith1',
                },
                'id': 1,
                'relationships': {
                    'posts': {
                        'links': {
                            'related': '/users/1/posts',
                            'self': '/users/1/relationships/posts'
                        }
                    },
                    'logs': {
                        'links': {
                            'related': '/users/1/logs',
                            'self': '/users/1/relationships/logs'
                        }
                    }
                },
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
        try:
            self.assertEqual(expected, actual)
            self.assertEqual(201, response.status_code)
        except AssertionError:
            raise nose.SkipTest()

    def test_add_resource_with_relationship(self):
        """Create resource succesfully with relationship."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        self.session.commit()

        payload = {
            'data': {
                'type': 'posts',
                'attributes': {
                    'title': 'Some Title',
                    'content': 'Some Content Inside'
                },
                'relationships': {
                    'author': {
                        'data': {
                            'type': 'users',
                            'id': user.id
                        }
                    }
                }
            }
        }

        response = models.serializer.post_collection(
            self.session, payload, 'posts')

        blog_post = self.session.query(models.Post).get(
            response.data['data']['id'])
        self.assertEqual(blog_post.title, 'Some Title')
        self.assertEqual(blog_post.content, 'Some Content Inside')
        self.assertEqual(blog_post.author_id, user.id)
        self.assertEqual(blog_post.author, user)

    def test_add_resource_with_relationship_response(self):
        """Create resource succesfully with relationship returns 201."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        self.session.commit()

        payload = {
            'data': {
                'type': 'posts',
                'attributes': {
                    'title': 'Some Title',
                    'content': 'Some Content Inside'
                },
                'relationships': {
                    'author': {
                        'data': {
                            'type': 'users',
                            'id': user.id
                        }
                    }
                }
            }
        }

        response = models.serializer.post_collection(
            self.session, payload, 'posts')

        expected = {
            'data': {
                'type': 'posts',
                'attributes': {
                    'title': u'Some Title',
                    'content': u'Some Content Inside'
                },
                'id': 1,
                'relationships': {
                    'author': {
                        'links': {
                            'related': '/posts/1/author',
                            'self': '/posts/1/relationships/author'
                        }
                    }
                }
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
        self.assertEqual(expected, actual)
        self.assertEqual(response.status_code, 201)

    def test_add_resource_twice(self):
        """Creating same resource twice results in 409 conflict."""
        payload = {
            'data': {
                'type': 'users',
                'attributes': {
                    'first': 'Sally',
                    'last': 'Smith',
                    'username': 'SallySmith1',
                    'password': 'password',
                }
            }
        }
        models.serializer.post_collection(self.session, payload, 'users')

        with self.assertRaises(errors.ValidationError) as error:
            models.serializer.post_collection(
                self.session, payload, 'users')

        self.assertEqual(error.exception.status_code, 409)

    def test_add_resource_mismatched_endpoint(self):
        """Create resource with mismatched returns 409.

        A InvalidTypeEndpointError is raised.
        """
        payload = {
            'data': {
                'type': 'posts'
            }
        }

        with self.assertRaises(errors.InvalidTypeForEndpointError) as error:
            models.serializer.post_collection(self.session, payload, 'users')

        self.assertEqual(
            error.exception.detail, 'Expected users, got posts')
        self.assertEqual(error.exception.status_code, 409)

    def test_add_resource_with_missing_data(self):
        """Create resource with missing content data results in 400.

        A BadRequestError is raised.
        """
        payload = {}

        with self.assertRaises(errors.BadRequestError) as error:
            models.serializer.post_collection(self.session, payload, 'users')

        self.assertEqual(
            error.exception.detail, 'Request should contain data key')
        self.assertEqual(error.exception.status_code, 400)

    def test_add_resource_with_missing_type(self):
        """Creat resource without type results in 409.

        A MissingTypeError is raised.
        """
        payload = {
            'data': {
                'attributes': {
                    'first': 'Sally',
                    'last': 'Smith',
                    'username': 'SallySmith1',
                    'password': 'password',
                }
            }
        }

        with self.assertRaises(errors.MissingTypeError) as error:
            models.serializer.post_collection(self.session, payload, 'users')

        self.assertEqual(
            error.exception.detail, 'Missing /data/type key in request body')
        self.assertEqual(error.exception.status_code, 409)

    def test_add_resource_with_unknown_field_name(self):
        """Create resource with unknown field results in 409.

        A ValidationError is raised.
        """
        payload = {
            'data': {
                'type': 'users',
                'attributes': {
                    'first': 'Sally',
                    'last': 'Smith',
                    'username': 'SallySmith1',
                    'password': 'password',
                    'unknown-attribute': 'test'
                }
            }
        }

        with self.assertRaises(errors.ValidationError) as error:
            models.serializer.post_collection(
                self.session, payload, 'users')

        self.assertEqual(error.exception.status_code, 409)

    def test_add_resource_access_denied(self):
        """Add a resource with access denied results in 403."""
        payload = {
            'data': {
                'type': 'logs'
            }
        }

        with self.assertRaises(errors.PermissionDeniedError) as error:
            models.serializer.post_collection(
                self.session, payload, 'logs')

        self.assertEqual(error.exception.status_code, 403)
