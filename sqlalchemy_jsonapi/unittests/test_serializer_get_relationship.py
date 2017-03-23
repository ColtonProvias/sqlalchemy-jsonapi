"""Test for serializer's get_relationship."""

from sqlalchemy_jsonapi import errors

from sqlalchemy_jsonapi.unittests.utils import testcases
from sqlalchemy_jsonapi.unittests import models


class GetRelationship(testcases.SqlalchemyJsonapiTestCase):
    """Tests for serializer.get_relationship."""

    def test_get_relationship_on_to_many(self):
        """Get a relationship to many resources returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        for x in range(2):
            comment = models.Comment(
                content='This is comment {0}'.format(x+1), author_id=user.id,
                post_id=blog_post.id, author=user, post=blog_post)
            self.session.add(comment)
        self.session.commit()

        response = models.serializer.get_relationship(
            self.session, {}, 'posts', blog_post.id, 'comments')

        expected = {
            'data': [{
                'id': 1,
                'type': 'comments'
            }, {
                'id': 2,
                'type': 'comments'
            }],
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

    def test_get_relationship_on_to_one(self):
        """Get a relationship of on to one returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        self.session.commit()

        response = models.serializer.get_relationship(
            self.session, {}, 'posts', blog_post.id, 'author')

        expected = {
            'data': {
                'id': 1,
                'type': 'users'
            },
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

    def test_get_relationship_with_unknown_relationship(self):
        """Get a resources relationship with an unknown relationship returns 404.

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
            models.serializer.get_relationship(
                self.session, {}, 'posts',
                blog_post.id, 'invalid-relationship')

        self.assertEqual(error.exception.status_code, 404)
