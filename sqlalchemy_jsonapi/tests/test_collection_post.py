import json

from sqlalchemy_jsonapi.errors import (
    BadRequestError, IDAlreadyExistsError, InvalidTypeForEndpointError,
    MissingTypeError, NotAFieldError, PermissionDeniedError, ValidationError)


def test_200_resource_creation(client):
    payload = {
        'data': {
            'type': 'users',
            'attributes': {
                'username': 'my_user',
                'email': 'user@example.com',
                'password': 'password'
            }
        }
    }
    response = client.post('/api/users/',
                           data=json.dumps(payload),
                           content_type='application/vnd.api+json').validate(
                               201)
    assert response.json_data['data']['links']['self'] == response.headers[
        'Location'
    ]
    assert response.json_data['data']['type'] == 'users'
    user_id = response.json_data['data']['id']
    response = client.get('/api/users/{}/'.format(user_id)).validate(200)


def test_200_resource_creation_with_relationships(fake_data, client):
    payload = {
        'data': {
            'type': 'posts',
            'attributes': {
                'title': 'Some title',
                'content': 'Hello, World!',
                'is_published': True
            },
            'relationships': {
                'author': {
                    'data': {
                        'type': 'users',
                        'id': fake_data['users'][0].id
                    }
                }
            }
        }
    }
    response = client.post('/api/posts',
                           data=json.dumps(payload),
                           content_type='application/vnd.api+json').validate(
                               201)
    assert response.json_data['data']['links']['self'] == response.headers[
        'Location'
    ]
    assert response.json_data['data']['type'] == 'posts'
    post_id = response.json_data['data']['id']
    response = client.get('/api/posts/{}/'.format(post_id)).validate(200)
    assert response.json_data['data']['relationships']['author']['data'][
        'id'
    ] == fake_data['users'][0].id


def test_403_when_access_is_denied(client):
    client.post('/api/logs/',
                data='{}',
                content_type='application/vnd.api+json').validate(
                    403, PermissionDeniedError)


def test_409_when_id_already_exists(fake_data, client):
    payload = {
        'data': {
            'type': 'users',
            'id': fake_data['users'][0].id,
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
                    409, IDAlreadyExistsError)


def test_409_when_type_doesnt_match_endpoint(fake_data, client):
    payload = {'data': {'type': 'posts'}}
    client.post('/api/users/',
                data=json.dumps(payload),
                content_type='application/vnd.api+json').validate(
                    409, InvalidTypeForEndpointError)


def test_400_when_missing_content_type(fake_data, client):
    client.post('/api/users/', data='{}').validate(409, BadRequestError)


def test_409_when_missing_type(fake_data, client):
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


def test_409_for_invalid_value(fake_data, client):
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


def test_409_for_wrong_field_name(fake_data, client):
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
                    409, NotAFieldError)
