import json

from sqlalchemy_jsonapi.errors import (
    InvalidTypeForEndpointError, MissingTypeError, PermissionDeniedError,
    ValidationError, MissingContentTypeError, NotAnAttributeError,
    BadRequestError)
from faker import Faker

fake = Faker()


def test_200_resource_creation(client):
    payload = {
        'data': {
            'type': 'users',
            'attributes': {
                'username': fake.user_name(),
                'email': 'user@example.com',
                'password': 'password'
            }
        }
    }
    response = client.post('/api/users/',
                           data=json.dumps(payload),
                           content_type='application/vnd.api+json').validate(
                               201)
    assert response.json_data['data']['type'] == 'users'
    user_id = response.json_data['data']['id']
    response = client.get('/api/users/{}/'.format(user_id)).validate(200)


def test_200_resource_creation_with_relationships(user, client):
    payload = {
        'data': {
            'type': 'blog-posts',
            'attributes': {
                'title': 'Some title',
                'content': 'Hello, World!',
                'is-published': True
            },
            'relationships': {
                'author': {
                    'data': {
                        'type': 'users',
                        'id': str(user.id)
                    }
                }
            }
        }
    }
    response = client.post('/api/blog-posts/',
                           data=json.dumps(payload),
                           content_type='application/vnd.api+json').validate(
                               201)
    assert response.json_data['data']['type'] == 'blog-posts'
    post_id = response.json_data['data']['id']
    response = client.get('/api/blog-posts/{}/?include=author'.format(post_id)).validate(200)
    assert response.json_data['data']['relationships']['author']['data'][
        'id'
    ] == str(user.id)


def test_403_when_access_is_denied(client):
    payload = {'data': {'type': 'logs'}}
    client.post('/api/logs/',
                data=json.dumps(payload),
                content_type='application/vnd.api+json').validate(
                    403, PermissionDeniedError)


def test_409_when_id_already_exists(user, client):
    payload = {
        'data': {
            'type': 'users',
            'id': str(user.id),
            'attributes': {
                'username': 'my_user',
                'email': 'user@example.com',
                'password': 'password'
            }
        }
    }
    client.post('/api/users/',
                data=json.dumps(payload),
                content_type='application/vnd.api+json').validate(
                    409, ValidationError)


def test_409_when_type_doesnt_match_endpoint(client):
    payload = {'data': {'type': 'blog-posts'}}
    client.post('/api/users/',
                data=json.dumps(payload),
                content_type='application/vnd.api+json').validate(
                    409, InvalidTypeForEndpointError)


def test_409_when_missing_content_type(client):
    client.post('/api/users/',
                data='{}').validate(409, MissingContentTypeError)


def test_409_when_missing_type(client):
    payload = {
        'data': {
            'attributes': {
                'username': 'my_user',
                'email': 'user@example.com',
                'password': 'password'
            }
        }
    }
    client.post('/api/users/',
                data=json.dumps(payload),
                content_type='application/vnd.api+json').validate(
                    409, MissingTypeError)


def test_409_for_invalid_value(client):
    payload = {
        'data': {
            'type': 'users',
            'attributes': {
                'username': 'my_user',
                'email': 'bad_email',
                'password': 'password'
            }
        }
    }
    client.post('/api/users/',
                data=json.dumps(payload),
                content_type='application/vnd.api+json').validate(
                    409, ValidationError)


def test_409_for_wrong_field_name(client):
    payload = {
        'data': {
            'type': 'users',
            'attributes': {
                'username': 'my_user',
                'email': 'some@example.com',
                'password': 'password',
                'wrong_field': True
            }
        }
    }
    client.post('/api/users/',
                data=json.dumps(payload),
                content_type='application/vnd.api+json').validate(
                    409, ValidationError)
