import json
from uuid import uuid4

from sqlalchemy_jsonapi.errors import (
    BadRequestError, PermissionDeniedError, RelationshipNotFoundError,
    ResourceNotFoundError, ToManyExpectedError)


def test_200_on_deletion_from_to_many(fake_data, client):
    payload = {
        'data': [
            {
                'type': 'comments',
                'id': fake_data['posts'][0].comments.first().id
            }
        ]
    }
    response = client.delete(
        '/api/posts/{}/relationships/comments/'.format(
            fake_data['posts'][0].id),
        data=json.dumps(payload),
        content_type='application/vnd.api+json').validate(200)
    for item in response.json_data['data']:
        assert {'id', 'type'} == set(item.keys())
    assert payload['data']['id'] not in [x['id']
                                         for x in response.json_data['data']]


def test_404_on_resource_not_found(fake_data, client):
    client.delete('/api/posts/{}/relationships/comments/'.format(uuid4()),
                  data='{}',
                  content_type='application/vnd.api+json').validate(
                      404, ResourceNotFoundError)


def test_404_on_relationship_not_found(fake_data, client):
    client.delete('/api/posts/{}/relationships/comment/'.format(
        fake_data['posts'][0].id),
                  data='{}',
                  content_type='application/vnd.api+json').validate(
                      404, RelationshipNotFoundError)


def test_403_on_permission_denied(fake_data, client):
    client.delete('/api/users/{}/relationships/logs/'.format(
        fake_data['users'][0].id),
                  data='{}',
                  content_type='application/vnd.api+json').validate(
                      404, PermissionDeniedError)


def test_409_on_to_one_provided(fake_data, client):
    client.delete('/api/posts/{}/relationships/author/'.format(
        fake_data['posts'][0].id),
                  data='{}',
                  content_type='application/vnd.api+json').validate(
                      404, ToManyExpectedError)


def test_400_missing_content_type_header(fake_data, client):
    client.delete('/api/posts/{}/relationships/comment/'.format(
        fake_data['posts'][0].id),
                  data='{}').validate(404, BadRequestError)
