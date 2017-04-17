"""Tests for declarative JSONAPISerializer serialize method."""

import unittest
import datetime

from sqlalchemy import (
    create_engine, Column, String, Integer, ForeignKey, Boolean, DateTime)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, sessionmaker

from sqlalchemy_jsonapi.declarative import serializer


class SerializeResourcesWithoutRelatedModels(unittest.TestCase):
    """Tests for serializing a resource that has no related models."""

    def setUp(self):
        """Configure sqlalchemy and session."""
        self.engine = create_engine('sqlite://')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.Base = declarative_base()

        class User(self.Base):
            __tablename__ = 'users'
            id = Column(Integer, primary_key=True)
            first_name = Column(String(50), nullable=False)
            age = Column(Integer, nullable=False)
            username = Column(String(50), unique=True, nullable=False)
            is_admin = Column(Boolean, default=False)
            date_joined = Column(DateTime)

        self.User = User
        self.Base.metadata.create_all(self.engine)

    def tearDown(self):
        """Reset the sqlalchemy engine."""
        self.Base.metadata.drop_all(self.engine)

    def test_serialize_single_resource_with_only_id_field(self):
        """Serialize a resource with only an 'id' field.

        If attributes, other than 'id', are not specified in fields,
        then the attributes remain an empty object.
        """

        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for User."""
            fields = ['id']
            model = self.User
            dasherize = True

        user = self.User(
            first_name='Sally', age=27, is_admin=True,
            username='SallySmith1', date_joined=datetime.date(2017, 12, 5))
        self.session.add(user)
        self.session.commit()
        user = self.session.query(self.User).get(user.id)

        user_serializer = UserSerializer()
        serialized_data = user_serializer.serialize(user)

        expected_data = {
            'data': {
                'id': str(user.id),
                'type': user.__tablename__,
                'attributes': {},
                'relationships': {}
            },
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        self.assertEqual(expected_data, serialized_data)

    def test_serialize_single_resource_with_dasherize_true(self):
        """Serialize a resource where attributes are dasherized.

        Attribute keys contain dashes instead of underscores.
        """

        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for User."""
            fields = [
                'id', 'first_name', 'username',
                'age', 'date_joined', 'is_admin']
            model = self.User
            dasherize = True

        user = self.User(
            first_name='Sally', age=27, is_admin=True,
            username='SallySmith1', date_joined=datetime.date(2017, 12, 5))
        self.session.add(user)
        self.session.commit()
        user = self.session.query(self.User).get(user.id)

        user_serializer = UserSerializer()
        serialized_data = user_serializer.serialize(user)

        expected_data = {
            'data': {
                'id': str(user.id),
                'type': u'{}'.format(user.__tablename__),
                'attributes': {
                    'date-joined': user.date_joined.isoformat(),
                    'username': u'{}'.format(user.username),
                    'age': user.age,
                    'first-name': u'{}'.format(user.first_name),
                    'is-admin': user.is_admin
                },
                'relationships': {}
            },
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        self.assertEqual(expected_data, serialized_data)

    def test_serialize_single_resource_with_dasherize_false(self):
        """Serialize a resource where attributes are not dasherized.

        Attribute keys are underscored like in serializer model.
        """

        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for User."""
            fields = [
                'id', 'first_name', 'username',
                'age', 'date_joined', 'is_admin']
            model = self.User
            dasherize = False

        user = self.User(
            first_name='Sally', age=27, is_admin=True,
            username='SallySmith1', date_joined=datetime.date(2017, 12, 5))
        self.session.add(user)
        self.session.commit()
        user = self.session.query(self.User).get(user.id)

        user_serializer = UserSerializer()
        serialized_data = user_serializer.serialize(user)

        expected_data = {
            'data': {
                'id': str(user.id),
                'type': u'{}'.format(user.__tablename__),
                'attributes': {
                    'date_joined': user.date_joined.isoformat(),
                    'username': u'{}'.format(user.username),
                    'age': user.age,
                    'first_name': u'{}'.format(user.first_name),
                    'is_admin': user.is_admin
                },
                'relationships': {}
            },
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        self.assertEqual(expected_data, serialized_data)

    def test_serialize_collection_of_resources(self):
        """Serialize a collection of resources returns a list of objects."""

        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for User."""
            fields = ['id']
            model = self.User
            dasherize = True

        user = self.User(
            first_name='Sally', age=27, is_admin=True,
            username='SallySmith1', date_joined=datetime.date(2017, 12, 5))
        self.session.add(user)
        self.session.commit()
        users = self.session.query(self.User)

        user_serializer = UserSerializer()
        serialized_data = user_serializer.serialize(users)

        expected_data = {
            'data': [{
                'id': str(user.id),
                'type': 'users',
                'attributes': {},
                'relationships': {}
            }],
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        self.assertEquals(expected_data, serialized_data)

    def test_serialize_empty_collection(self):
        """Serialize a collection that is empty returns an empty list."""

        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for User."""
            fields = ['id']
            model = self.User
            dasherize = True

        users = self.session.query(self.User)

        user_serializer = UserSerializer()
        serialized_data = user_serializer.serialize(users)

        expected_data = {
            'data': [],
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        self.assertEquals(expected_data, serialized_data)

    def test_serialize_resource_not_found(self):
        """Serialize a resource that does not exist returns None."""

        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for User."""
            fields = ['id']
            model = self.User
            dasherize = True

        # Nonexistant user
        user = self.session.query(self.User).get(99999999)

        user_serializer = UserSerializer()
        serialized_data = user_serializer.serialize(user)

        expected_data = {
            'data': None,
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        self.assertEqual(expected_data, serialized_data)


class SerializeResourceWithRelatedModels(unittest.TestCase):
    """Tests for serializing a resource that has related models."""

    def setUp(self):
        """Configure sqlalchemy and session."""
        self.engine = create_engine('sqlite://')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.Base = declarative_base()

        class User(self.Base):
            __tablename__ = 'users'
            id = Column(Integer, primary_key=True)
            first_name = Column(String(50), nullable=False)

        class Post(self.Base):
            __tablename__ = 'posts'
            id = Column(Integer, primary_key=True)
            title = Column(String(100), nullable=False)
            author_id = Column(Integer, ForeignKey('users.id',
                                                   ondelete='CASCADE'))

            blog_author = relationship('User',
                                       lazy='joined',
                                       backref=backref('posts',
                                                       lazy='dynamic',
                                                       cascade='all,delete'))

        self.User = User
        self.Post = Post
        self.Base.metadata.create_all(self.engine)

    def tearDown(self):
        """Reset the sqlalchemy engine."""
        self.Base.metadata.drop_all(self.engine)

    def test_serialize_resource_with_to_many_relationship_success(self):
        """Serailize a resource with a to-many relationship."""

        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for User."""
            fields = ['id', 'first_name']
            model = self.User

        user = self.User(first_name='Sally')
        self.session.add(user)
        self.session.commit()
        user = self.session.query(self.User).get(user.id)

        user_serializer = UserSerializer()
        serialized_data = user_serializer.serialize(user)

        expected_data = {
            'data': {
                'id': str(user.id),
                'type': user.__tablename__,
                'attributes': {
                    'first-name': u'{}'.format(user.first_name)
                },
                'relationships': {
                    'posts': {
                        'links': {
                            'self': '/users/1/relationships/posts',
                            'related': '/users/1/posts'
                        }
                    }
                }
            },
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        self.assertEqual(expected_data, serialized_data)

    def test_serialize_resource_with_to_one_relationship_success(self):
        """Serialize a resource with a to-one relationship."""

        class PostSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for Post."""
            fields = ['id', 'title']
            model = self.Post

        blog_post = self.Post(title='Foo')
        self.session.add(blog_post)
        self.session.commit()
        post = self.session.query(self.Post).get(blog_post.id)

        blog_post_serializer = PostSerializer()
        serialized_data = blog_post_serializer.serialize(post)

        expected_data = {
            'data': {
                'id': str(blog_post.id),
                'type': blog_post.__tablename__,
                'attributes': {
                    'title': u'{}'.format(blog_post.title)
                },
                'relationships': {
                    'blog-author': {
                        'links': {
                            'self': '/posts/1/relationships/blog-author',
                            'related': '/posts/1/blog-author'
                        }
                    }
                }
            },
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        self.assertEqual(expected_data, serialized_data)

    def test_serialize_resource_with_relationship_given_dasherize_false(self):
        """Serialize a resource with to-one relationship given dasherize false.

        Relationship keys are underscored like in model.
        """

        class PostSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for Post."""
            fields = ['id', 'title']
            model = self.Post
            dasherize = False

        blog_post = self.Post(title='Foo')
        self.session.add(blog_post)
        self.session.commit()
        post = self.session.query(self.Post).get(blog_post.id)

        blog_post_serializer = PostSerializer()
        serialized_data = blog_post_serializer.serialize(post)

        expected_data = {
            'data': {
                'id': str(blog_post.id),
                'type': blog_post.__tablename__,
                'attributes': {
                    'title': u'{}'.format(blog_post.title)
                },
                'relationships': {
                    'blog_author': {
                        'links': {
                            'self': '/posts/1/relationships/blog_author',
                            'related': '/posts/1/blog_author'
                        }
                    }
                }
            },
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        self.assertEqual(expected_data, serialized_data)


class TestSerializeErrors(unittest.TestCase):
    """Tests for errors raised in serialize method."""

    def setUp(self):
        """Configure sqlalchemy and session."""
        self.engine = create_engine('sqlite://')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.Base = declarative_base()

        class User(self.Base):
            __tablename__ = 'users'
            id = Column(Integer, primary_key=True)
            first_name = Column(String(50), nullable=False)

        class Post(self.Base):
            __tablename__ = 'posts'
            id = Column(Integer, primary_key=True)
            title = Column(String(100), nullable=False)
            author_id = Column(Integer, ForeignKey('users.id',
                                                   ondelete='CASCADE'))

            blog_author = relationship('User',
                                       lazy='joined',
                                       backref=backref('posts',
                                                       lazy='dynamic',
                                                       cascade='all,delete'))

        self.User = User
        self.Post = Post
        self.Base.metadata.create_all(self.engine)

    def tearDown(self):
        """Reset the sqlalchemy engine."""
        self.Base.metadata.drop_all(self.engine)

    def test_serialize_resource_with_mismatched_model(self):
        """A serializers model type much match the resource it serializes."""

        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for User."""
            fields = ['id']
            model = self.Post

        user = self.User(first_name='Sally')
        self.session.add(user)
        self.session.commit()
        user = self.session.query(self.User).get(user.id)

        user_serializer = UserSerializer()
        with self.assertRaises(TypeError):
            user_serializer.serialize(user)

    def test_serialize_resource_with_unknown_attribute_in_fields(self):
        """Cannot serialize attributes that are unknown to resource."""

        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for User."""
            fields = ['id', 'firsts_names_unknown']
            model = self.User

        user = self.User(first_name='Sally')
        self.session.add(user)
        self.session.commit()
        user = self.session.query(self.User).get(user.id)

        user_serializer = UserSerializer()
        with self.assertRaises(AttributeError):
            user_serializer.serialize(user)

    def test_serialize_resource_with_related_model_in_fields(self):
        """Model serializer fields cannot contain related models.

        It is against json-api spec to serialize related models as attributes.
        """

        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for User."""
            fields = ['id', 'posts']
            model = self.User

        user = self.User(first_name='Sally')
        self.session.add(user)
        self.session.commit()
        user = self.session.query(self.User).get(user.id)

        user_serializer = UserSerializer()
        with self.assertRaises(AttributeError):
            user_serializer.serialize(user)

    def test_serialize_resource_with_foreign_key_in_fields(self):
        """Model serializer fields cannot contain foreign keys.

        It is against json-api spec to serialize foreign keys as attributes.
        """

        class PostSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for Post."""
            fields = ['id', 'author_id']
            model = self.Post

        blog_post = self.Post(title='Foo')
        self.session.add(blog_post)
        self.session.commit()
        post = self.session.query(self.Post).get(blog_post.id)

        blog_post_serializer = PostSerializer()
        with self.assertRaises(AttributeError):
            blog_post_serializer.serialize(post)

    def test_serialize_resource_with_invalid_primary_key(self):
        """Resource cannot have unknown primary key.

        The primary key must be an attribute on the resource.
        """

        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for Post."""
            fields = ['unknown_primary_key', 'first_name']
            primary_key = 'unknown_primary_key'
            model = self.User

        user = self.User(first_name='Sally')
        self.session.add(user)
        self.session.commit()
        user = self.session.query(self.User).get(user.id)

        user_serializer = UserSerializer()
        with self.assertRaises(AttributeError):
            user_serializer.serialize(user)


class TestSerializerInstantiationErrors(unittest.TestCase):
    """Test exceptions raised in instantiation of serializer."""

    def setUp(self):
        """Configure sqlalchemy and session."""
        self.engine = create_engine('sqlite://')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.Base = declarative_base()

        class User(self.Base):
            __tablename__ = 'users'
            id = Column(Integer, primary_key=True)
            first_name = Column(String(50), nullable=False)

        self.User = User
        self.Base.metadata.create_all(self.engine)

    def tearDown(self):
        """Reset the sqlalchemy engine."""
        self.Base.metadata.drop_all(self.engine)

    def test_serializer_with_no_defined_model(self):
        """Serializer requires model member."""

        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for User."""
            fields = ['id']

        with self.assertRaises(TypeError):
            UserSerializer()

    def test_serializer_with_no_defined_fields(self):
        """At minimum fields must exist."""
        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for User."""
            model = self.User

        with self.assertRaises(ValueError):
            UserSerializer()

    def test_serializer_with_missing_id_field(self):
        """An 'id' is required in serializer fields."""

        class UserSerializer(serializer.JSONAPISerializer):
            """Declarative serializer for User."""
            fields = ['first_name']
            model = self.User

        with self.assertRaises(ValueError):
            UserSerializer()
