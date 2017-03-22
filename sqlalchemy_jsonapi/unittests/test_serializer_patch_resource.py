"""Test for serializer's patch_resource."""

from sqlalchemy_jsonapi import errors

from sqlalchemy_jsonapi.unittests.utils import testcases
from sqlalchemy_jsonapi.unittests import models


class PatchResource(testcases.SqlalchemyJsonapiTestCase):
    """Tests for serializer.patch_resource."""

    def test_patch_resource_successful(self):
        """Patch resource is successful"""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content')
        self.session.add(blog_post)
        self.session.commit()
        payload = {
            'data': {
                'type': 'posts',
                'id': blog_post.id,
                'attributes': {
                    'title': 'This is a new title'
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

        models.serializer.patch_resource(
            self.session, payload, 'posts', blog_post.id)

        self.assertEqual(blog_post.author.id, user.id)
        self.assertEqual(blog_post.author, user)

    @testcases.fragile
    def test_patch_resource_response(self):
        """Patch resource response returns resource and 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content')
        self.session.add(blog_post)
        self.session.commit()
        payload = {
            'data': {
                'type': 'posts',
                'id': blog_post.id,
                'attributes': {
                    'title': 'This is a new title'
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

        response = models.serializer.patch_resource(
            self.session, payload, 'posts', blog_post.id)

        expected = {
            'data': {
                'id': 1,
                'attributes': {
                    'content': u'This is the content',
                    'title': u'This is a new title'
                },
                'type': 'posts',
                'relationships': {
                    'comments': {
                        'links': {
                            'related': '/posts/1/comments',
                            'self': '/posts/1/relationships/comments'
                        }
                    },
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
        self.assertEqual(200, response.status_code)

    def test_patch_resource_with_missing_type(self):
        """Patch resource with missing type results in 400.

        A BadRequestError is raised.
        """
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content')
        self.session.add(blog_post)
        self.session.commit()
        payload = {
            'data': {
                'type': 'posts',
                'attributes': {
                    'title': 'This is a new title'
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

        with self.assertRaises(errors.BadRequestError) as error:
            models.serializer.patch_resource(
                self.session, payload, 'posts', blog_post.id)

        expected_detail = 'Missing type or id'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 400)

    def test_patch_resource_with_mismatched_id(self):
        """Patch resource with mismatched id results in 400.

        A BadRequestError is raised.
        """
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content')
        self.session.add(blog_post)
        self.session.commit()
        payload = {
            'data': {
                'type': 'posts',
                'id': 2,
                'attributes': {
                    'title': 'This is a new title'
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

        with self.assertRaises(errors.BadRequestError) as error:
            models.serializer.patch_resource(
                self.session, payload, 'posts', blog_post.id)

        expected_detail = 'IDs do not match'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 400)

    def test_patch_resource_with_mismatched_type(self):
        """Patch resource with mismatched type results in 400.

        A BadRequestError is raised.
        """
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content')
        self.session.add(blog_post)
        self.session.commit()
        payload = {
            'data': {
                'type': 'comments',
                'id': blog_post.id,
                'attributes': {
                    'title': 'This is a new title'
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

        with self.assertRaises(errors.BadRequestError) as error:
            models.serializer.patch_resource(
                self.session, payload, 'posts', blog_post.id)

        expected_detail = 'Type does not match'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 400)

    def test_patch_resource_relationship_field_not_found(self):
        """Patch resource with unknown relationship field returns 400.

        A BadRequestError is raised.
        """
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        comment = models.Comment(
            content='This is a comment', author_id=user.id,
            post_id=blog_post.id, author=user, post=blog_post)
        self.session.add(comment)
        self.session.commit()
        payload = {
            'data': {
                'type': 'posts',
                'id': blog_post.id,
                'relationships': {
                    'nonexistant': {
                        'data': {
                            'type': 'users',
                            'id': user.id
                        }
                    }
                }
            }
        }

        with self.assertRaises(errors.BadRequestError) as error:
            models.serializer.patch_resource(
                self.session, payload, 'posts', blog_post.id)

        expected_detail = 'nonexistant not relationships for posts.1'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 400)
