from uuid import uuid4

from sqlalchemy_jsonapi.errors import (RelationshipNotFoundError,
                                       ResourceNotFoundError)


def test_200_result_of_to_one(fake_data, client):
    response = client.get('/api/posts/{}/author/'.format(
        fake_data['posts'][0].id)).validate(200)
    assert response.json_data['data']['type'] == 'users'


def test_200_collection_of_to_many(fake_data, client):
    response = client.get('/api/posts/{}/comments/'.format(
        fake_data['posts'][0].id)).validate(200)
    assert len(response.json_data['data']) > 0


def test_404_when_relationship_not_found(fake_data, client):
    client.get('/api/posts/{}/last_comment/'.format(
        fake_data['posts'][0].id)).validate(404, RelationshipNotFoundError)


def test_404_when_resource_not_found(fake_data, client):
    client.get('/api/posts/{}/comments/'.format(uuid4())).validate(
        404, ResourceNotFoundError)

    # TODO: Inclusion, sorting, filtering, and all that jazz
