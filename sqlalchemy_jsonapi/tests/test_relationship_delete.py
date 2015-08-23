import json
from uuid import uuid4

from sqlalchemy_jsonapi.errors import (
    BadRequestError, PermissionDeniedError, RelationshipNotFoundError,
    ResourceNotFoundError, ToManyExpectedError, MissingContentTypeError)


def test_200_on_deletion_from_to_many(comment, client):
    payload = {'data': [{'type': 'comments', 'id': str(comment.id)}]}
    response = client.delete(
        '/api/posts/{}/relationships/comments/'.format(
            comment.post.id),
        data=json.dumps(payload),
        content_type='application/vnd.api+json').validate(200)
    for item in response.json_data['data']:
        assert {'id', 'type'} == set(item.keys())
    assert payload['data'][0]['id'] not in [str(x['id'])
                                            for x in response.json_data['data']
                                            ]


def test_404_on_resource_not_found(client):
    client.delete('/api/posts/{}/relationships/comments/'.format(uuid4()),
                  data='{}',
                  content_type='application/vnd.api+json').validate(
                      404, ResourceNotFoundError)


def test_404_on_relationship_not_found(post, client):
    client.delete('/api/posts/{}/relationships/comment/'.format(
        post.id),
                  data='{}',
                  content_type='application/vnd.api+json').validate(
                      404, RelationshipNotFoundError)


def test_403_on_permission_denied(user, client):
    client.delete('/api/users/{}/relationships/logs/'.format(
        user.id),
                  data='{}',
                  content_type='application/vnd.api+json').validate(
                      403, PermissionDeniedError)


def test_409_on_to_one_provided(post, client):
    client.delete('/api/posts/{}/relationships/author/'.format(
        post.id),
                  data='{}',
                  content_type='application/vnd.api+json').validate(
                      409, ToManyExpectedError)


def test_409_missing_content_type_header(post, client):
    client.delete('/api/posts/{}/relationships/comment/'.format(
        post.id),
                  data='{}').validate(409, MissingContentTypeError)
