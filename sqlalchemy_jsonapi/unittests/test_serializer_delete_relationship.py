"""Test for serializer's delete_relationship."""

from sqlalchemy_jsonapi import errors

from sqlalchemy_jsonapi.unittests.utils import testcases
from sqlalchemy_jsonapi.unittests import models


class DeleteRelationship(testcases.SqlalchemyJsonapiTestCase):
    """Tests for serializer.delete_resource."""

    def test_delete_one_to_many_relationship_successs(self):
        """Delete a relationship from a resource is successful.
        
        Ensure objects are no longer related in database.
        I don't want this comment to be associated with this post
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
            'data': [{
                'type': 'comments',
                'id': comment.id
            }]
        }

        response = models.serializer.delete_relationship(
            self.session, payload, 'posts', blog_post.id, 'comments')
        
        updated_comment = self.session.query(models.Comment).get(comment.id)
        self.assertEquals(updated_comment.post_id, None)
        self.assertEquals(updated_comment.post, None)

    def test_delete_one_to_many_relationship_response_success(self):
        """Delete a relationship from a resource is successful returns 200."""
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
            'data': [{
                'type': 'comments',
                'id': comment.id
            }]
        }

        response = models.serializer.delete_relationship(
            self.session, payload, 'posts', blog_post.id, 'comments')

        expected = {'data': []}
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(200, response.status_code)


    def test_delete_one_to_many_relationship_with_invalid_data(self):
        """Delete a relationship from a resource is successful returns 200."""
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
                'type': 'comments',
                'id': comment.id
            }
        }

        with self.assertRaises(errors.ValidationError) as error:
            models.serializer.delete_relationship(
                self.session, payload, 'posts', blog_post.id, 'comments')

        self.assertEquals(
            error.exception.detail, 'Provided data must be an array.')
        self.assertEquals(error.exception.status_code, 409)

    def test_delete_many_to_one_relationship_response(self):
        """Delete a many-to-one relationship returns a 409.
        
        A ToManyExpectedError is returned.
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
            'data': [{
                'type': 'users',
                'id': user.id
            }]
        }

        response = models.serializer.delete_relationship(
            self.session, payload, 'posts', blog_post.id, 'author')

        expected_detail = 'posts.1.author is not a to-many relationship'
        self.assertEqual(expected_detail, response.detail)
        self.assertEqual(409, response.status_code)
