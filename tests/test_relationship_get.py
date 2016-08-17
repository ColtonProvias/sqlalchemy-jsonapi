"""from sqlalchemy_jsonapi.errors import (
    RelationshipNotFoundError, ResourceNotFoundError, PermissionDeniedError)
from uuid import uuid4

# TODO: Sorting
# TODO: Pagination
# TODO: Ember-style filtering
# TODO: Simple filtering
# TODO: Complex filtering
# TODO: Bad query param


def test_200_on_to_many(post, client):
    response = client.get('/api/blog-posts/{}/relationships/comments/'.format(
        post.id)).validate(200)
    for item in response.json_data['data']:
        assert {'id', 'type'} == set(item.keys())


def test_200_on_to_one(post, client):
    response = client.get('/api/blog-posts/{}/relationships/author/'.format(
        post.id)).validate(200)
    assert response.json_data['data']['type'] == 'users'


def test_404_on_resource_not_found(client):
    client.get('/api/blog-posts/{}/relationships/comments/'.format(uuid4(
    ))).validate(404, ResourceNotFoundError)


def test_404_on_relationship_not_found(post, client):
    client.get('/api/blog-posts/{}/relationships/comment/'.format(
        post.id)).validate(404, RelationshipNotFoundError)


def test_403_on_permission_denied(unpublished_post, client):
    client.get('/api/blog-posts/{}/relationships/comment/'.format(
        unpublished_post.id)).validate(403, PermissionDeniedError)
"""
