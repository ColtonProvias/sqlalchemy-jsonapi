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

    def test_delete_nonexistant_resource(self):
        """Delete notexistant resource returns 404.

        A ResourceTypeNotFoundError is raised.
        """
        with self.assertRaises(errors.ResourceTypeNotFoundError) as error:
            models.serializer.delete_resource(
                self.session, {}, 'non-existant', 1)

        self.assertEqual(error.exception.status_code, 404)

    def test_delete_resource_cascade_with_one_many_relationship(self):
        """Delete a resource with a cascade and one-to-many relationship.

        Ensure all referencing models are removed.
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
            content='This is comment 1', author_id=user.id,
            post_id=blog_post.id, author=user, post=blog_post)
        self.session.add(comment)
        self.session.commit()

        models.serializer.delete_resource(self.session, {}, 'users', 1)

        post = self.session.query(models.Post).get(1)
        comment = self.session.query(models.Comment).get(1)
        self.assertEqual(post, None)
        self.assertEqual(comment, None)
