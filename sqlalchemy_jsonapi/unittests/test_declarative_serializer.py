"""Tests for declarative JSONAPISerializer serialize method."""

from sqlalchemy_jsonapi.unittests.utils import testcases
from sqlalchemy_jsonapi.unittests import models
from sqlalchemy_jsonapi.declarative import serializer


class UserSerializer(serializer.JSONAPISerializer):
    """A serializer for the User model."""
    fields = ['id', 'first', 'last', 'username']
    model = models.User


class TestDeclarativeSerializer(testcases.SqlalchemyJsonapiTestCase):
    """Tests for JSONAPISerializer.serialize."""

    def test_serialize_a_single_resource_success(self):
        """Serialize a single resource successfully.

        A jsonapi compliant object is returned."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        self.session.commit()
        user = self.session.query(models.User).get(user.id)

        user_serializer = UserSerializer()
        serialized_data = user_serializer.serialize(user)

        expected = {
            'data': {
                'type': 'users',
                'id': '1',
                'attributes': {
                    'first': u'Sally',
                    'last': u'Smith',
                    'username': u'SallySmith1'
                },
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
                }
            },
            'included': [],
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        self.assertEqual(expected, serialized_data)

    def test_serialize_collection_of_resources(self):
        """Serialize a collection of resources successfully returns a jsonapi compliant object."""
        for x in range(2):
            user = models.User(
                first='Sally-{0}'.format(x+1),
                last='Joe-{0}'.format(x+1),
                username='SallyJoe{0}'.format(x+1),
                password='password')
            self.session.add(user)
        self.session.commit()
        collection = self.session.query(models.User)

        user_serializer = UserSerializer()
        actual = user_serializer.serialize(collection)

        expected = {
            'data': [{
                'type': 'users',
                'id': '1',
                'attributes': {
                    'first': u'Sally-1',
                    'last': u'Joe-1',
                    'username': u'SallyJoe1'
                },
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
                }
            }, {
                'type': 'users',
                'id': '2',
                'attributes': {
                    'first': u'Sally-2',
                    'last': u'Joe-2',
                    'username': u'SallyJoe2'
                },
                'relationships': {
                    'posts': {
                        'links': {
                            'related': '/users/2/posts',
                            'self': '/users/2/relationships/posts'
                        }
                    },
                    'logs': {
                        'links': {
                            'related': '/users/2/logs',
                            'self': '/users/2/relationships/logs'
                        }
                    },
                    'comments': {
                        'links': {
                            'related': '/users/2/comments',
                            'self': '/users/2/relationships/comments'
                        }
                    }
                }
            }],
            'included': [],
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        self.assertEqual(expected['data'], actual['data'])
        self.assertEqual(expected['meta'], actual['meta'])
        self.assertEqual(expected['jsonapi'], actual['jsonapi'])
        self.assertEqual(expected['included'], actual['included'])

    def test_serialize_resource_with_missing_required_attribute_id(self):
        """Serialize resource without required attriute of 'id' raises AttributeError."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        self.session.commit()
        user = self.session.query(models.User).get(user.id)

        class InvalidUserSerializer(serializer.JSONAPISerializer):
            fields = ['first', 'last', 'username']
            model = models.User

        user_serializer = InvalidUserSerializer()
        with self.assertRaises(AttributeError):
            user_serializer.serialize(user)

    def test_serialize_resource_with_relationships_as_attributes(self):
        """Serialize a resource with fields that are relationships raises an AttributeError.

        The serializer should only serialize attributes and not relationships.
        Relationships are shown under the resource objects top member 'relationships'.
        """
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        self.session.commit()
        post = self.session.query(models.Post).get(blog_post.id)

        class InvalidBlogPostSerializer(serializer.JSONAPISerializer):
            fields = ['title', 'content', 'author', 'comments']
            model = models.Post

        blog_post_serializer = InvalidBlogPostSerializer()
        with self.assertRaises(AttributeError):
            blog_post_serializer.serialize(post)

    def test_serialize_resource_with_mismatched_resource(self):
        """Serialize a resource with mismatched serializer model raises TypeError."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        self.session.commit()
        post = self.session.query(models.Post).get(blog_post.id)

        user_serializer = UserSerializer()
        with self.assertRaises(TypeError):
            user_serializer.serialize(post)
