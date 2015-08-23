from sqlalchemy_jsonapi.errors import ResourceNotFoundError, PermissionDeniedError
from uuid import uuid4


def test_200_without_querystring(post, client):
    response = client.get('/api/posts/{}/'.format(post.id)).validate(200)
    assert response.json_data['data']['type'] == 'posts'
    assert response.json_data['data']['id']


def test_404_resource_not_found(client):
    client.get('/api/posts/{}/'.format(uuid4())).validate(
        404, ResourceNotFoundError)


def test_403_permission_denied(unpublished_post, client):
    client.get('/api/posts/{}/'.format(unpublished_post.id)).validate(
        403, PermissionDeniedError)


def test_200_with_single_included_model(post, client):
    response = client.get('/api/posts/{}/?include=author'.format(
        post.id)).validate(200)
    assert response.json_data['data']['type'] == 'posts'
    assert response.json_data['included'][0]['type'] == 'users'


def test_200_with_including_model_and_including_inbetween(comment, client):
    response = client.get('/api/comments/{}/?include=post.author'.format(
        comment.id)).validate(200)
    assert response.json_data['data']['type'] == 'comments'
    for data in response.json_data['included']:
        assert data['type'] in ['posts', 'users']


def test_200_with_multiple_includes(post, client):
    response = client.get('/api/posts/{}/?include=comments,author'.format(
        post.id)).validate(200)
    assert response.json_data['data']['type'] == 'posts'
    for data in response.json_data['included']:
        assert data['type'] in ['comments', 'users']


def test_200_with_single_field(post, client):
    response = client.get('/api/posts/{}/?fields[posts]=title'.format(
        post.id)).validate(200)
    assert {'title'} == set(response.json_data['data']['attributes'].keys())
    assert len(response.json_data['data']['relationships']) == 0


def test_200_with_multiple_fields(post, client):
    response = client.get('/api/posts/{}/?fields[posts]=title,content'.format(
        post.id)).validate(
            200)
    assert {'title', 'content'
            } == set(response.json_data['data']['attributes'].keys())
    assert len(response.json_data['data']['relationships']) == 0


def test_200_with_single_field_across_a_relationship(post, client):
    response = client.get(
        '/api/posts/{}/?fields[posts]=title,content&fields[comments]=author&include=comments'.format(
            post.id)).validate(
                200)
    assert {'title', 'content'
            } == set(response.json_data['data']['attributes'].keys())
    assert len(response.json_data['data']['relationships']) == 0
    for item in response.json_data['included']:
        assert {'title', 'content'} == set(item['attributes'].keys())
        assert len(item['attributes']) == 0
        assert {'author'} == set(item['relationships'].keys())
