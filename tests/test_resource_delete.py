"""from uuid import uuid4

from sqlalchemy_jsonapi.errors import (
    PermissionDeniedError, ResourceNotFoundError, ResourceTypeNotFoundError)

# TODO: Bad query param


def test_200_on_success(comment, client):
    client.delete('/api/blog-comments/{}/'.format(comment.id)).validate(204)
    client.get('/api/blog-comments/{}/'.format(comment.id)).validate(
        404, ResourceNotFoundError)


def test_404_on_resource_type_not_found(client):
    client.delete('/api/nonexistant/somevalue/').validate(
        404, ResourceTypeNotFoundError)


def test_403_on_permission_denied(user, client):
    client.delete('/api/users/{}/'.format(user.id)).validate(
        403, PermissionDeniedError)


def test_404_on_resource_not_found(client):
    client.delete('/api/blog-comments/{}/'.format(uuid4())).validate(
        404, ResourceNotFoundError)
"""
