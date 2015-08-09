from sqlalchemy_jsonapi.errors import (RelationshipNotFoundError,
                                       ResourceNotFoundError)


def test_200_on_to_many(fake_data, client):
    response = client.get(
        '/api/posts/{}/relationships/comments/'.format(
            fake_data['posts'][0].id)).validate(200)
    for item in response.json_data['data']:
        assert {'id', 'type'} == set(item.keys())


def test_200_on_to_one(fake_data, client):
    response = client.get(
        '/api/posts/{}/relationships/author/'.format(
            fake_data['posts'][0].id)).validate(200)
    assert response.json_data['data']['type'] == 'users'


def test_404_on_resource_not_found(fake_data, client):
    client.get(
        '/api/posts/{}/relationships/comments/'.format(
            fake_data['posts'][0].id)).validate(404, ResourceNotFoundError)


def test_404_on_relationship_not_found(fake_data, client):
    client.get(
        '/api/posts/{}/relationships/comment/'.format(
            fake_data['posts'][0].id)).validate(404, RelationshipNotFoundError)
