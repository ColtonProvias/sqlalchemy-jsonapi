"""Test for serializer's patch_relationship."""

from sqlalchemy_jsonapi import errors

from sqlalchemy_jsonapi.unittests.utils import testcases
from sqlalchemy_jsonapi.unittests import models
from sqlalchemy_jsonapi import __version__


class GPatchRelationship(testcases.SqlalchemyJsonapiTestCase):
    """Tests for serializer.patch_relationship."""

    def test_patch_relationship_on_to_one_set_to_resource_response(self):
        """Patch single relationship and set resource returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        new_user = models.User(
            first='Bob', last='Joe',
            password='password', username='BobJoe2')
        self.session.add(new_user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        self.session.commit()
        payload = {
            'data': {
                'type': 'users',
                'id': new_user.id
            }
        }

        response = models.serializer.patch_relationship(
            self.session, payload, 'posts', blog_post.id, 'author')

        expected = {
            'data': {
                'id': new_user.id,
                'type': 'users'
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

    def test_patch_relationship_on_to_one_set_to_resource_successful(self):
        """Patch single relationship successfully updates resource."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        new_user = models.User(
            first='Bob', last='Joe',
            password='password', username='BobJoe2')
        self.session.add(new_user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        self.session.commit()
        payload = {
            'data': {
                'type': 'users',
                'id': new_user.id
            }
        }

        models.serializer.patch_relationship(
            self.session, payload, 'posts', blog_post.id, 'author')

        self.assertEqual(blog_post.author.id, new_user.id)
        self.assertEqual(blog_post.author, new_user)

    def test_patch_relationship_on_to_one_set_resource_to_null_response(self):
        """Patch relationship of a single resource and set to null returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        self.session.commit()
        payload = {
            'data': None
        }

        response = models.serializer.patch_relationship(
            self.session, payload, 'posts', blog_post.id, 'author')

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

    def test_patch_relationship_on_to_one_set_resource_to_null_successful(self):
        """Patch relationship of single resource and set to null is successful."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        self.session.commit()
        payload = {
            'data': None
        }

        models.serializer.patch_relationship(
            self.session, payload, 'posts', blog_post.id, 'author')

        self.assertEqual(blog_post.author, None)

    def test_patch_relationship_on_to_many_set_resources_response(self):
        """Patch relationships on many and set resources returns 200."""
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
        new_comment = models.Comment(
            content='This is a new comment 2', author_id=user.id,
            author=user)
        self.session.add(new_comment)
        self.session.commit()
        payload = {
            'data': [{
                'type': 'comments',
                'id': new_comment.id
            }]
        }

        response = models.serializer.patch_relationship(
            self.session, payload, 'posts', blog_post.id, 'comments')

        expected = {
            'data': [{
                'type': 'comments',
                'id': 2
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

    def test_patch_relationship_on_to_many_set_resources_successful(self):
        """Patch relationships on many and set resources is successful."""
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
        new_comment = models.Comment(
            content='This is a new comment 2', author_id=user.id,
            author=user)
        self.session.add(new_comment)
        self.session.commit()
        payload = {
            'data': [{
                'type': 'comments',
                'id': new_comment.id
            }]
        }

        models.serializer.patch_relationship(
            self.session, payload, 'posts', blog_post.id, 'comments')

        self.assertEqual(new_comment.post.id, blog_post.id)
        self.assertEqual(new_comment.post, blog_post)

    def test_patch_relationship_on_to_many_set_to_empty_response(self):
        """Patch relationships on many and set to empty returns 200."""
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
        payload = {
            'data': []
        }

        response = models.serializer.patch_relationship(
            self.session, payload, 'posts', blog_post.id, 'comments')

        expected = {
            'data': [],
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

    def test_patch_relationship_on_to_many_set_to_empty_successful(self):
        """Patch relationships on many and set to empty is successful."""
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
        payload = {
            'data': []
        }

        models.serializer.patch_relationship(
            self.session, payload, 'posts', blog_post.id, 'comments')

        self.assertEqual(comment.post, None)

    def test_patch_relationship_on_to_one_with_empty_list(self):
        """Patch relationship on to one with empty list returns 409.

        A ValidationError is raised.
        """
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        new_user = models.User(
            first='Bob', last='Joe',
            password='password', username='BobJoe2')
        self.session.add(new_user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        self.session.commit()
        payload = {
            'data': []
        }

        with self.assertRaises(errors.ValidationError) as error:
            models.serializer.patch_relationship(
                self.session, payload, 'posts', blog_post.id, 'author')

        expected_detail = 'Provided data must be a hash.'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 409)

    def test_patch_relationship_on_to_many_with_null(self):
        """Patch relationship on to many with null returns 409.

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
            content='This is comment 1', author_id=user.id,
            post_id=blog_post.id, author=user, post=blog_post)
        self.session.add(comment)
        self.session.commit()
        payload = {
            'data': None
        }

        with self.assertRaises(errors.ValidationError) as error:
            models.serializer.patch_relationship(
                self.session, payload, 'posts', blog_post.id, 'comments')

        expected_detail = 'Provided data must be an array.'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 409)

    def test_patch_relationship_with_unknown_relationship(self):
        """Patch relationship with unknown relationship returns 404.

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
            content='This is comment 1', author_id=user.id,
            post_id=blog_post.id, author=user, post=blog_post)
        self.session.add(comment)
        self.session.commit()
        payload = {
            'data': {}
        }

        with self.assertRaises(errors.RelationshipNotFoundError) as error:
            models.serializer.patch_relationship(
                self.session, payload, 'posts',
                blog_post.id, 'unknown-relationship')

        self.assertEqual(error.exception.status_code, 404)

    def test_patch_relationship_on_to_one_with_incompatible_model(self):
        """Patch relationship on to one with incompatible model returns 409.

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
            content='This is comment 1', author_id=user.id,
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
            models.serializer.patch_relationship(
                self.session, payload, 'posts', blog_post.id, 'author')

        expected_detail = 'Incompatible Type'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 409)

    def test_patch_relationship_on_to_many_with_incompatible_model(self):
        """Patch relationship on to many with incompatible model returns 409.

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
            content='This is comment 1', author_id=user.id,
            post_id=blog_post.id, author=user, post=blog_post)
        self.session.add(comment)
        self.session.commit()
        payload = {
            'data': [{
                'type': 'users',
                'id': user.id
            }]
        }

        with self.assertRaises(errors.ValidationError) as error:
            models.serializer.patch_relationship(
                self.session, payload, 'posts', blog_post.id, 'comments')

        expected_detail = 'Incompatible Type'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 409)
