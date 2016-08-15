import json
from uuid import uuid4

from sqlalchemy_jsonapi.errors import (BadRequestError, PermissionDeniedError,
                                       ResourceNotFoundError, ValidationError)


# TODO: Sparse Fieldsets
# TODO: Related Includes
# TODO: Bad query param


def test_200(client, post, user):
    payload = {
        'data': {
            'type': 'blog-posts',
            'id': str(post.id),
            'attributes': {
                'title': 'I just lost the game'
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
    response = client.patch(
        '/api/blog-posts/{}/'.format(post.id),
        data=json.dumps(payload),
        content_type='application/vnd.api+json').validate(200)
    assert response.json_data['data']['id'] == str(post.id)
    assert response.json_data['data']['type'] == 'blog-posts'
    assert response.json_data['data']['attributes'][
        'title'] == 'I just lost the game'


def test_400_missing_type(post, client):
    client.patch('/api/blog-posts/{}/'.format(post.id),
                 data=json.dumps({}),
                 content_type='application/vnd.api+json').validate(
                     400, BadRequestError)


def test_404_resource_not_found(client):
    client.patch('/api/blog-posts/{}/'.format(uuid4()),
                 content_type='application/vnd.api+json',
                 data='{}').validate(404, ResourceNotFoundError)


def test_404_related_resource_not_found(client, post):
    payload = {
        'data': {
            'type': 'blog-posts',
            'id': str(post.id),
            'relationships': {
                'author': {
                    'data': {
                        'type': 'users',
                        'id': str(uuid4())
                    }
                }
            }
        }
    }
    client.patch('/api/blog-posts/{}/'.format(post.id),
                 data=json.dumps(payload),
                 content_type='application/vnd.api+json').validate(
                     404, ResourceNotFoundError)


def test_400_field_not_found(client, post, user):
    payload = {
        'data': {
            'type': 'blog-posts',
            'id': str(post.id),
            'relationships': {
                'authors': {
                    'data': {
                        'type': 'users',
                        'id': str(user.id)
                    }
                }
            }
        }
    }
    client.patch('/api/blog-posts/{}/'.format(post.id),
                 data=json.dumps(payload),
                 content_type='application/vnd.api+json').validate(
                     400, BadRequestError)


def test_409_type_mismatch_to_one(client, post, user):
    payload = {
        'data': {
            'type': 'blog-posts',
            'id': str(post.id),
            'relationships': {
                'comments': {
                    'data': {
                        'type': 'users',
                        'id': str(user.id)
                    }
                }
            }
        }
    }
    client.patch('/api/blog-posts/{}/'.format(post.id),
                 data=json.dumps(payload),
                 content_type='application/vnd.api+json').validate(
                     409, ValidationError)


def test_400_type_mismatch_to_many(client, post, user):
    payload = {
        'data': {
            'type': 'blog-posts',
            'id': str(post.id),
            'relationships': {
                'author': [{
                    'data': {
                        'type': 'users',
                        'id': str(user.id)
                    }
                }]
            }
        }
    }
    client.patch('/api/blog-posts/{}/'.format(post.id),
                 data=json.dumps(payload),
                 content_type='application/vnd.api+json').validate(
                     400, BadRequestError)


def test_409_validation_failed(client, post, user):
    payload = {
        'data': {
            'type': 'blog-posts',
            'id': str(post.id),
            'attributes': {
                'title': None
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
    client.patch('/api/blog-posts/{}/'.format(post.id),
                 data=json.dumps(payload),
                 content_type='application/vnd.api+json').validate(
                     409, ValidationError)


def test_400_type_does_not_match_endpoint(client, post, user):
    payload = {
        'data': {
            'type': 'users',
            'id': str(post.id),
            'attributes': {
                'title': 'I just lost the game'
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
    client.patch('/api/blog-posts/{}/'.format(post.id),
                 data=json.dumps(payload),
                 content_type='application/vnd.api+json').validate(
                     400, BadRequestError)


def test_403_permission_denied(user, client):
    client.patch('/api/users/{}/'.format(user.id),
                 data='{}',
                 content_type='application/vnd.api+json').validate(
                     403, PermissionDeniedError)
