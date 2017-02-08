import json
from uuid import uuid4

from sqlalchemy_jsonapi.errors import (PermissionDeniedError,
                                       RelationshipNotFoundError,
                                       ResourceNotFoundError, ValidationError)


def test_200_on_to_one_set_to_resource(post, user, client):
    payload = {'data': {'type': 'users', 'id': str(user.id)}}
    response = client.patch(
        '/api/blog-posts/{}/relationships/author/'.format(post.id),
        data=json.dumps(payload),
        content_type='application/vnd.api+json').validate(200)
    assert response.json_data['data']['id'] == str(user.id)


def test_200_on_to_one_set_to_null(post, client):
    payload = {'data': None}
    response = client.patch(
        '/api/blog-posts/{}/relationships/author/'.format(post.id),
        data=json.dumps(payload),
        content_type='application/vnd.api+json').validate(200)
    assert response.json_data['data'] == None


def test_200_on_to_many_set_to_resources(post, comment, client):
    payload = {'data': [{'type': 'blog-comments', 'id': str(comment.id)}]}
    response = client.patch('/api/blog-posts/{}/relationships/comments/'.format(
        post.id),
                            data=json.dumps(payload),
                            content_type='application/vnd.api+json').validate(
                                200)
    assert response.json_data['data'][0]['id'] == str(comment.id)
    assert len(response.json_data['data']) == 1


def test_200_on_to_many_set_to_empty(post, client):
    payload = {'data': []}
    response = client.patch('/api/blog-posts/{}/relationships/comments/'.format(
        post.id),
                            data=json.dumps(payload),
                            content_type='application/vnd.api+json').validate(
                                200)
    assert len(response.json_data['data']) == 0


def test_409_on_to_one_set_to_empty_list(post, client):
    payload = {'data': []}
    client.patch('/api/blog-posts/{}/relationships/author/'.format(
        post.id),
                 data=json.dumps(payload),
                 content_type='application/vnd.api+json').validate(
                     409, ValidationError)


def test_409_on_to_many_set_to_null(post, client):
    payload = {'data': None}
    client.patch('/api/blog-posts/{}/relationships/comments/'.format(
        post.id),
                 data=json.dumps(payload),
                 content_type='application/vnd.api+json').validate(
                     409, ValidationError)


def test_404_on_resource_not_found(client):
    client.patch('/api/blog-posts/{}/relationships/comments/'.format(
        uuid4()),
                 data='{}',
                 content_type='application/vnd.api+json').validate(
                     404, ResourceNotFoundError)


def test_404_on_relationship_not_found(client, post):
    client.patch('/api/blog-posts/{}/relationships/comment/'.format(
        post.id),
                 data='{}',
                 content_type='application/vnd.api+json').validate(
                     404, RelationshipNotFoundError)


def test_404_on_related_item_not_found(post, client):
    payload = {'data': [{'type': 'blog-comments', 'id': str(uuid4())}]}
    client.patch('/api/blog-posts/{}/relationships/comments/'.format(
        post.id),
                 data=json.dumps(payload),
                 content_type='application/vnd.api+json').validate(
                     404, ResourceNotFoundError)


def test_403_on_permission_denied(user, log, client):
    payload = {'data': {'type': 'users', 'id': str(user.id)}}
    client.patch('/api/logs/{}/relationships/user/'.format(
        log.id),
                 data=json.dumps(payload),
                 content_type='application/vnd.api+json').validate(
                     403, PermissionDeniedError)


def test_403_on_permission_denied_on_related(log, user, client):
    payload = {'data': {'type': 'logs', 'id': str(log.id)}}
    client.patch('/api/users/{}/relationships/logs/'.format(
        user.id),
                 data=json.dumps(payload),
                 content_type='application/vnd.api+json').validate(
                     403, PermissionDeniedError)


def test_409_on_to_one_with_incompatible_model(post, comment, client):
    payload = {'data': {'type': 'blog-comments', 'id': str(comment.id)}}
    client.patch('/api/blog-posts/{}/relationships/author/'.format(
        post.id),
                 data=json.dumps(payload),
                 content_type='application/vnd.api+json').validate(
                     409, ValidationError)


def test_409_on_to_many_with_incompatible_model(post, client):
    payload = {'data': [{'type': 'blog-posts', 'id': str(post.id)}]}
    client.patch('/api/blog-posts/{}/relationships/author/'.format(
        post.id),
                 data=json.dumps(payload),
                 content_type='application/vnd.api+json').validate(
                     409, ValidationError)
