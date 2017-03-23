"""Test for serializer's post_relationship."""

from sqlalchemy_jsonapi import errors

from sqlalchemy_jsonapi.unittests.utils import testcases
from sqlalchemy_jsonapi.unittests import models


class PostRelationship(testcases.SqlalchemyJsonapiTestCase):
    """Tests for serializer.post_relationship."""
    def test_post_relationship_on_to_many_success(self):
        """Post relationship creates a relationship on many resources."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        comment_one = models.Comment(
            content='This is the first comment',
            author_id=user.id, author=user)
        self.session.add(comment_one)
        comment_two = models.Comment(
            content='This is the second comment',
            author_id=user.id, author=user)
        self.session.add(comment_two)
        self.session.commit()
        payload = {
            'data': [{
                'type': 'comments',
                'id': comment_one.id
            }, {
                'type': 'comments',
                'id': comment_two.id
            }]
        }

        models.serializer.post_relationship(
            self.session, payload, 'posts', blog_post.id, 'comments')

        self.assertEqual(comment_one.post.id, blog_post.id)
        self.assertEqual(comment_one.post, blog_post)
        self.assertEqual(comment_two.post.id, blog_post.id)
        self.assertEqual(comment_two.post.id, blog_post.id)

    def test_post_relationship_on_to_many_response(self):
        """Post relationship creates a relationship on many resources returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        comment_one = models.Comment(
            content='This is the first comment',
            author_id=user.id, author=user)
        self.session.add(comment_one)
        comment_two = models.Comment(
            content='This is the second comment',
            author_id=user.id, author=user)
        self.session.add(comment_two)
        self.session.commit()
        payload = {
            'data': [{
                'type': 'comments',
                'id': comment_one.id
            }, {
                'type': 'comments',
                'id': comment_two.id
            }]
        }

        response = models.serializer.post_relationship(
            self.session, payload, 'posts', blog_post.id, 'comments')

        expected = {
            'data': [{
                'type': 'comments',
                'id': comment_one.id
            }, {
                'type': 'comments',
                'id': comment_two.id
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

    def test_post_relationship_with_hash_instead_of_array(self):
        """Post relalationship with a hash instead of an array returns 409.

        A ValidationError is raised.
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
            content='This is the first comment',
            author_id=user.id, author=user)
        self.session.add(comment)
        self.session.commit()
        payload = {
            'data': {
                'type': 'comments',
                'id': comment.id
            }
        }

        with self.assertRaises(errors.ValidationError) as error:
            models.serializer.post_relationship(
                self.session, payload, 'posts', blog_post.id, 'comments')

        expected_detail = '/data must be an array'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 409)

    def test_post_relationship_with_incompatible_data_model(self):
        """Post relationship with incompatible data model returns 409.

        The model type in the payload must match the relationship type.
        A ValidationError is raised.
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
            content='This is the first comment',
            author_id=user.id, author=user)
        self.session.add(comment)
        self.session.commit()
        payload = {
            'data': [{
                'type': 'users',
                'id': user.id
            }]
        }

        with self.assertRaises(errors.ValidationError) as error:
            models.serializer.post_relationship(
                self.session, payload, 'posts', blog_post.id, 'comments')

        expected_detail = 'Incompatible type provided'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 409)

    def test_post_relationship_with_to_one_relationship(self):
        """Post relationship with to one relationship returns 409.

        Cannot post to a to-one relationship.
        A ValidationError is raised.
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
            content='This is the first comment',
            author_id=user.id, author=user)
        self.session.add(comment)
        self.session.commit()

        with self.assertRaises(errors.ValidationError) as error:
            models.serializer.post_relationship(
                self.session, {}, 'comments', comment.id, 'author')

        expected_detail = 'Cannot post to to-one relationship'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 409)

    def test_post_relationship_with_unknown_relationship(self):
        """Post relationship with unknown relationship results in a 404.

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
            content='This is the first comment',
            author_id=user.id, author=user)
        self.session.add(comment)
        self.session.commit()

        with self.assertRaises(errors.RelationshipNotFoundError) as error:
            models.serializer.post_relationship(
                self.session, {}, 'posts',
                blog_post.id, 'unknown-relationship')

        self.assertEqual(error.exception.status_code, 404)

    def test_post_relationship_with_extra_data_keys(self):
        """Post relationship with data keys other than 'id' and 'type' results in 404.

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
            content='This is the first comment',
            author_id=user.id, author=user)
        self.session.add(comment)
        self.session.commit()
        payload = {
            'data': [{
                'type': 'comments',
                'id': comment.id,
                'extra-key': 'foo'
            }]
        }
        with self.assertRaises(errors.BadRequestError) as error:
            models.serializer.post_relationship(
                self.session, payload, 'posts', blog_post.id, 'comments')

        expected_detail = 'comments must have type and id keys'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 400)
