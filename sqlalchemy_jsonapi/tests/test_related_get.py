from uuid import uuid4

from sqlalchemy_jsonapi.errors import (RelationshipNotFoundError,
                                       ResourceNotFoundError)


def test_200_result_of_to_one(post, client):
    response = client.get('/api/posts/{}/author/'.format(post.id)).validate(
        200)
    assert response.json_data['data']['type'] == 'users'


def test_200_collection_of_to_many(post, client):
    response = client.get('/api/posts/{}/comments/'.format(
        post.id)).validate(200)
    assert len(response.json_data['data']) > 0


def test_404_when_relationship_not_found(post, client):
    client.get('/api/posts/{}/last_comment/'.format(
        post.id)).validate(404, RelationshipNotFoundError)


def test_404_when_resource_not_found(client):
    client.get('/api/posts/{}/comments/'.format(uuid4())).validate(
        404, ResourceNotFoundError)

    # TODO: Inclusion, sorting, filtering, and all that jazz
