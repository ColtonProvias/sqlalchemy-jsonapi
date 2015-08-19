import json
from uuid import uuid4

from sqlalchemy_jsonapi.errors import (BadRequestError, PermissionDeniedError,
                                       ResourceNotFoundError)


def test_200():
    raise NotImplementedError


def test_400_missing_type(post, client):
    client.patch('/api/posts/{}/'.format(post.id),
                 data=json.dumps({}),
                 content_type='application/vnd.api+json').validate(
                     400, BadRequestError)


def test_404_resource_not_found(client):
    client.patch('/api/posts/{}/'.format(uuid4()),
                 content_type='application/vnd.api+json',
                 data='{}').validate(
                     404, ResourceNotFoundError)


def test_404_related_resource_not_found():
    raise NotImplementedError


def test_400_field_not_found():
    raise NotImplementedError


def test_409_type_mismatch_to_one():
    raise NotImplementedError


def test_409_type_mismatch_to_many():
    raise NotImplementedError


def test_409_validation_failed():
    raise NotImplementedError


def test_400_type_does_not_match_endpoint():
    raise NotImplementedError


def test_403_permission_denied(user, client):
    client.patch('/api/users/{}/'.format(user.id),
                 data='{}',
                 content_type='application/vnd.api+json').validate(
                     403, PermissionDeniedError)
