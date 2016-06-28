from uuid import uuid4

from sqlalchemy_jsonapi.errors import (RelationshipNotFoundError,
                                       ResourceNotFoundError)

# TODO: Sparse Fieldsets
# TODO: Related Includes
# TODO: Sorting
# TODO: Pagination
# TODO: Ember-style filtering
# TODO: Simple filtering
# TODO: Complex filtering
# TODO: Bad query param


def test_200_result_of_to_one(post, client):
    response = client.get('/api/blog-posts/{}/author/'.format(
        post.id)).validate(200)
    assert response.json_data['data']['type'] == 'users'


def test_200_collection_of_to_many(comment, client):
    response = client.get('/api/blog-posts/{}/comments/'.format(
        comment.post.id)).validate(200)
    assert len(response.json_data['data']) > 0


def test_404_when_relationship_not_found(post, client):
    client.get('/api/blog-posts/{}/last_comment/'.format(post.id)).validate(
        404, RelationshipNotFoundError)


def test_404_when_resource_not_found(client):
    client.get('/api/blog-posts/{}/comments/'.format(uuid4())).validate(
        404, ResourceNotFoundError)
