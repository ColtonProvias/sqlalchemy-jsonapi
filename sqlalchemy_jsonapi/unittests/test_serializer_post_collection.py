"""Test for serializer's post_collection."""

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
        self.assertEqual(user.first, 'SET-ATTR:Sally')
        self.assertEqual(user.last, 'Smith')
        self.assertEqual(user.username, 'SallySmith1')
        self.assertEqual(user.password, 'password')

    @testcases.fragile
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
                    'password': 'password'
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
                    'username': u'SallySmith1'
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
                    },
                    'comments': {
                        'links': {
                            'related': '/users/1/comments',
                            'self': '/users/1/relationships/comments'
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
        self.assertEqual(expected, actual)
        self.assertEqual(201, response.status_code)

    def test_add_resource_with_relationship(self):
        """Create resource succesfully with many-to-one relationship."""
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

    @testcases.fragile
    def test_add_resource_with_many_to_one_relationship_response(self):
        """Create resource succesfully with many-to-one relationship returns 201."""
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
                    },
                    'comments': {
                        'links': {
                            'related': '/posts/1/comments',
                            'self': '/posts/1/relationships/comments'
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

        self.assertEqual(error.exception.detail, 'Incompatible data type')
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

        self.assertEqual(error.exception.detail, 'CREATE denied on logs.None')
        self.assertEqual(error.exception.status_code, 403)

    def test_add_resource_with_given_id(self):
        """Create resource successfully with specified id."""
        payload = {
            'data': {
                'type': 'users',
                'id': 3,
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
        self.assertEqual(user.first, 'SET-ATTR:Sally')
        self.assertEqual(user.last, 'Smith')
        self.assertEqual(user.username, 'SallySmith1')
        self.assertEqual(user.password, 'password')

    def test_add_resource_with_invalid_one_to_many_relationships(self):
        """Create resource with invalid one-to-many relationship returns 400.

        In a one-to-many relationship, the data in the relationship must be
        of type array.
        A BadRequestError is raised.
        """
        payload = {
            'data': {
                'attributes': {
                    'first': 'Sally',
                    'last': 'Smith',
                    'username': 'SallySmith1',
                    'password': 'password',
                },
                'type': 'users',
                'relationships': {
                    'posts': {
                        'data': {
                            'type': 'posts',
                            'id': 1
                        }
                    }
                }
            }
        }

        with self.assertRaises(errors.BadRequestError) as error:
            models.serializer.post_collection(
                self.session, payload, 'users')

        self.assertEqual(error.exception.detail, 'posts must be an array')
        self.assertEqual(error.exception.status_code, 400)

    def test_add_resource_with_no_data_in_many_to_one_relationship(self):
        """Create resource without data in many-to-one relationships returns 400.

        A BadRequestError is raised.
        """
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
                        'test': {
                            'type': 'users',
                            'id': user.id
                        }
                    }
                }
            }
        }

        with self.assertRaises(errors.BadRequestError) as error:
            models.serializer.post_collection(
                self.session, payload, 'posts')

        self.assertEqual(
            error.exception.detail, 'Missing data key in relationship author')
        self.assertEqual(error.exception.status_code, 400)

    def test_add_resource_when_data_in_many_to_one_relationship_not_dict(self):
        """Create resource with many-to-one relationship whose data is not a dict returns 400.

        A BadRequestError is raised.
        """
        payload = {
            'data': {
                'type': 'posts',
                'attributes': {
                    'title': 'Some Title',
                    'content': 'Some Content Inside'
                },
                'relationships': {
                    'author': {
                        'data': 'Test that not being a dictionary fails'
                    }
                }
            }
        }
        with self.assertRaises(errors.BadRequestError) as error:
            models.serializer.post_collection(
                self.session, payload, 'posts')

        self.assertEqual(error.exception.detail, 'author must be a hash')
        self.assertEqual(error.exception.status_code, 400)

    def test_add_resource_with_invalid_many_to_one_relationship_data(self):
        """Create resource with invalid many-to-one relationship data returns 400.

        A BadRequestError is raised.
        """
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
                            'id': 1,
                            'name': 'Sally'
                        }
                    }
                }
            }
        }
        with self.assertRaises(errors.BadRequestError) as error:
            models.serializer.post_collection(
                self.session, payload, 'posts')

        self.assertEqual(
            error.exception.detail, 'author must have type and id keys')
        self.assertEqual(error.exception.status_code, 400)

    def test_add_resource_with_missing_one_to_many_relationship_type(self):
        """Create resource with missing one-to-many relationship type returns 400.

        The relationship data must contain 'id' and 'type'.
        A BadRequestError is raised.
        """
        payload = {
            'data': {
                'attributes': {
                    'first': 'Sally',
                    'last': 'Smith',
                    'username': 'SallySmith1',
                    'password': 'password',
                },
                'type': 'users',
                'relationships': {
                    'posts': {
                        'data': [{
                            'type': 'posts',
                        }]
                    }
                }
            }
        }

        with self.assertRaises(errors.BadRequestError) as error:
            models.serializer.post_collection(
                self.session, payload, 'users')

        self.assertEqual(
            error.exception.detail, 'posts must have type and id keys')
        self.assertEqual(error.exception.status_code, 400)

    @testcases.fragile
    def test_add_resource_with_a_null_relationship(self):
        """Create resource with a null relationship returns 201."""
        payload = {
            'data': {
                'type': 'posts',
                'attributes': {
                    'title': 'Some Title',
                    'content': 'Some Content Inside'
                },
                'relationships': {
                    'author': {
                        'data': None
                    }
                }
            }
        }

        response = models.serializer.post_collection(
            self.session, payload, 'posts')

        expected = {
            'data': {
                'type': 'posts',
                'relationships': {
                    'author': {
                        'links': {
                            'self': '/posts/1/relationships/author',
                            'related': '/posts/1/author'
                        }
                    },
                    'comments': {
                        'links': {
                            'self': '/posts/1/relationships/comments',
                            'related': '/posts/1/comments'
                        }
                    }
                },
                'id': 1,
                'attributes': {
                    'title': u'Some Title',
                    'content': u'Some Content Inside'
                }
            },
            'jsonapi': {
                'version': '1.0'
            },
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'included': []
        }
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(201, response.status_code)
