from sqlalchemy_jsonapi.errors import ResourceNotFoundError, PermissionDeniedError
from uuid import uuid4


def test_200_without_querystring():
    raise NotImplementedError


def test_404_resource_not_found(client):
    client.get('/api/posts/{}/'.format(uuid4())).validate(
        404, ResourceNotFoundError)


def test_403_permission_denied(unpublished_post, client):
    client.get('/api/posts/{}/'.format(unpublished_post.id)).validate(
        403, PermissionDeniedError)


def test_200_with_single_included_model():
    raise NotImplementedError


def test_200_with_including_model_and_including_inbetween():
    raise NotImplementedError


def test_200_with_multiple_includes():
    raise NotImplementedError


def test_400_when_given_attribute_for_include_instead_of_relationship():
    raise NotImplementedError


def test_400_when_given_missing_field_for_include():
    raise NotImplementedError


def test_200_with_single_field():
    raise NotImplementedError


def test_200_with_multiple_fields():
    raise NotImplementedError


def test_200_with_single_field_across_a_relationship():
    raise NotImplementedError


def test_400_when_incorrect_field_given():
    raise NotImplementedError
