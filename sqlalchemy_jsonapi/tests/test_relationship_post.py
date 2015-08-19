import json
from uuid import uuid4

from sqlalchemy_jsonapi.errors import ValidationError, ResourceNotFoundError, RelationshipNotFoundError


def test_200_on_to_many(comment, post, client):
    payload = {'data': [{'type': 'comments', 'id': str(comment.id)}]}
    response = client.post('/api/posts/{}/relationships/comments/'.format(
        post.id),
                           data=json.dumps(payload),
                           content_type='application/vnd.api+json').validate(
                               200)
    assert comment.id in [str(x['id']) for x in response.json_data['data']]


def test_409_on_hash_instead_of_array_provided(comment, post, client):
    payload = {'data': {'type': 'comments', 'id': str(comment.id)}}
    client.post('/api/posts/{}/relationships/comments/'.format(
        post.id),
                data=json.dumps(payload),
                content_type='application/vnd.api+json').validate(
                    409, ValidationError)


def test_409_on_incompatible_model(user, post, client):
    payload = {'data': [{'type': 'users', 'id': str(user.id)}]}
    client.post('/api/posts/{}/relationships/comments/'.format(
        post.id),
                data=json.dumps(payload),
                content_type='application/vnd.api+json').validate(
                    409, ValidationError)


def test_409_on_to_one_relationship(post, client):
    client.post(
        '/api/posts/{}/relationships/author/'.format(post.id),
        data='{}',
        content_type='application/vnd.api+json').validate(409, ValidationError)


def test_404_on_resource_not_found(client):
    client.post('/api/posts/{}/relationships/comments/'.format(uuid4()),
                data='{}',
                content_type='application/vnd.api+json').validate(
                    404, ResourceNotFoundError)


def test_404_on_relationship_not_found(post, client):
    client.post('/api/posts/{}/relationships/comment/'.format(
        post.id),
                data='{}',
                content_type='application/vnd.api+json').validate(
                    404, RelationshipNotFoundError)
