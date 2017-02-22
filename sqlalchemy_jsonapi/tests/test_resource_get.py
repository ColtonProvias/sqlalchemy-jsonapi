from sqlalchemy_jsonapi.errors import (
    ResourceNotFoundError, PermissionDeniedError)
from uuid import uuid4


def test_200_without_querystring(post, client):
    response = client.get('/api/blog-posts/{}/'.format(post.id)).validate(200)
    assert response.json_data['data']['type'] == 'blog-posts'
    assert response.json_data['data']['id']


def test_404_resource_not_found(client):
    client.get('/api/blog-posts/{}/'.format(uuid4())).validate(
        404, ResourceNotFoundError)


def test_403_permission_denied(unpublished_post, client):
    client.get('/api/blog-posts/{}/'.format(unpublished_post.id)).validate(
        403, PermissionDeniedError)


def test_200_with_single_included_model(post, client):
    response = client.get('/api/blog-posts/{}/?include=author'.format(
        post.id)).validate(200)
    assert response.json_data['data']['type'] == 'blog-posts'
    assert response.json_data['included'][0]['type'] == 'users'


def test_200_with_including_model_and_including_inbetween(comment, client):
    response = client.get('/api/blog-comments/{}/?include=post.author'.format(
        comment.id)).validate(200)
    assert response.json_data['data']['type'] == 'blog-comments'
    for data in response.json_data['included']:
        assert data['type'] in ['blog-posts', 'users']


def test_200_with_multiple_includes(post, client):
    response = client.get('/api/blog-posts/{}/?include=comments,author'.format(
        post.id)).validate(200)
    assert response.json_data['data']['type'] == 'blog-posts'
    for data in response.json_data['included']:
        assert data['type'] in ['blog-comments', 'users']


def test_200_with_single_field(post, client):
    response = client.get(
        '/api/blog-posts/{}/?fields[blog-posts]=title'.format(
            post.id)).validate(200)
    assert {'title'} == set(response.json_data['data']['attributes'].keys())
    assert len(response.json_data['data']['relationships']) == 0


def test_200_with_multiple_fields(post, client):
    response = client.get(
        '/api/blog-posts/{}/?fields[blog-posts]=title,content'.format(
            post.id)).validate(200)
    assert {'title', 'content'
            } == set(response.json_data['data']['attributes'].keys())
    assert len(response.json_data['data']['relationships']) == 0


def test_200_with_single_field_across_a_relationship(post, client):
    response = client.get(
        '/api/blog-posts/{}/?fields[blog-posts]=title,content&fields[blog-comments]=author&include=comments'.format(  # NOQA
            post.id)).validate(200)
    assert {'title', 'content'
            } == set(response.json_data['data']['attributes'].keys())
    assert len(response.json_data['data']['relationships']) == 0
    for item in response.json_data['included']:
        assert {'title', 'content'} == set(item['attributes'].keys())
        assert len(item['attributes']) == 0
        assert {'author'} == set(item['relationships'].keys())
