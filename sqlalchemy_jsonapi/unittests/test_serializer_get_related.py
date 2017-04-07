"""Test for serializer's get_related."""

from sqlalchemy_jsonapi import errors

from sqlalchemy_jsonapi.unittests.utils import testcases
from sqlalchemy_jsonapi.unittests import models
from sqlalchemy_jsonapi import __version__


class GetRelated(testcases.SqlalchemyJsonapiTestCase):
    """Tests for serializer.get_related."""

    @testcases.fragile
    def test_get_related_of_to_one(self):
        """Get a related single resource returns a 200.

        This test is fragile.
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

        response = models.serializer.get_related(
            self.session, {}, 'posts', blog_post.id, 'author')

        expected = {
            'data': {
                'id': 1,
                'type': 'users',
                'included': {},
                'relationships': {
                    'comments': {
                        'links': {
                            'related': '/users/1/comments',
                            'self': '/users/1/relationships/comments'
                        }
                    },
                    'logs': {
                        'links': {
                            'related': '/users/1/logs',
                            'self': '/users/1/relationships/logs'
                        }
                    },
                    'posts': {
                        'links': {
                            'related': '/users/1/posts',
                            'self': '/users/1/relationships/posts'
                        }
                    }
                },
                'attributes': {
                    'first': u'Sally',
                    'last': u'Smith',
                    'username': u'SallySmith1'
                }
            },
            'jsonapi': {
                'version': '1.0'
            },
            'meta': {
                'sqlalchemy_jsonapi_version': __version__
            }
        }
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(200, response.status_code)

    def test_get_related_of_to_many(self):
        """Get many related resource returns a 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        for x in (range(2)):
            comment = models.Comment(
                content='This is comment {0}'.format(x+1), author_id=user.id,
                post_id=blog_post.id, author=user, post=blog_post)
            self.session.add(comment)
        self.session.commit()

        response = models.serializer.get_related(
            self.session, {}, 'posts', blog_post.id, 'comments')

        expected = {
            'data': [{
                'id': 1,
                'type': 'comments',
                'included': {},
                'relationships': {
                    'post': {
                        'links': {
                            'self': '/comments/1/relationships/post',
                            'related': '/comments/1/post'
                        }
                    },
                    'author': {
                        'links': {
                            'self': '/comments/1/relationships/author',
                            'related': '/comments/1/author'
                        }
                    }
                },
                'attributes': {
                    'content': u'This is comment 1'
                }
            }, {
                'id': 2,
                'type': 'comments',
                'included': {},
                'relationships': {
                    'post': {
                        'links': {
                            'self': '/comments/2/relationships/post',
                            'related': '/comments/2/post'
                        }
                    },
                    'author': {
                        'links': {
                            'self': '/comments/2/relationships/author',
                            'related': '/comments/2/author'
                        }
                    }
                },
                'attributes': {
                    'content': u'This is comment 2'
                }
            }],
            'jsonapi': {
                'version': '1.0'
            },
            'meta': {
                'sqlalchemy_jsonapi_version': __version__
            }
        }
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(200, response.status_code)

    def test_get_related_with_unknown_relationship(self):
        """Get related resource with unknown relationship returns 404.

        A RelationshipNotFoundError is raised.
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

        with self.assertRaises(errors.RelationshipNotFoundError) as error:
            models.serializer.get_related(
                self.session, {}, 'posts',
                blog_post.id, 'invalid-relationship')

        self.assertEqual(error.exception.status_code, 404)

    def test_get_related_when_related_object_is_null(self):
        """Get a related object that is null returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content')
        self.session.add(blog_post)
        self.session.commit()

        response = models.serializer.get_related(
            self.session, {}, 'posts', blog_post.id, 'author')

        expected = {
            'data': None,
            'jsonapi': {
                'version': '1.0'
            },
            'meta': {
                'sqlalchemy_jsonapi_version': __version__
            }
        }
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(200, response.status_code)
