from sqlalchemy_jsonapi.errors import (
    BadRequestError, NotAFieldError, NotAnAttributeError,
    NotARelationshipError, NotSortableError, OutOfBoundsError)


def test_200_with_no_querystring(bunch_of_posts, client):
    response = client.get('/api/posts/').validate(200)
    assert response.json_data['data'][0]['type'] == 'posts'
    assert response.json_data['data'][0]['id']


def test_200_with_single_included_model(bunch_of_posts, client):
    response = client.get('/api/posts/?include=author').validate(200)
    assert response.json_data['data'][0]['type'] == 'posts'
    assert response.json_data['included'][0]['type'] == 'users'


def test_200_with_including_model_and_including_inbetween(bunch_of_posts,
                                                          client):
    response = client.get('/api/comments/?include=post.author').validate(200)
    assert response.json_data['data'][0]['type'] == 'comments'
    for data in response.json_data['included']:
        assert data['type'] in ['posts', 'users']


def test_200_with_multiple_includes(bunch_of_posts, client):
    response = client.get('/api/posts/?include=comments,author').validate(200)
    assert response.json_data['data'][0]['type'] == 'posts'
    for data in response.json_data['included']:
        assert data['type'] in ['comments', 'users']


def test_200_with_single_field(bunch_of_posts, client):
    response = client.get('/api/posts/?fields[posts]=title').validate(200)
    for item in response.json_data['data']:
        assert {'title'} == set(item['attributes'].keys())
        assert len(item['relationships']) == 0


def test_200_with_multiple_fields(bunch_of_posts, client):
    response = client.get('/api/posts/?fields[posts]=title,content').validate(
        200)
    for item in response.json_data['data']:
        assert {'title', 'content'} == set(item['attributes'].keys())
        assert len(item['relationships']) == 0


def test_200_with_single_field_across_a_relationship(bunch_of_posts, client):
    response = client.get(
        '/api/posts/?fields[posts]=title,content&fields[comments]=author&include=comments').validate(
            200)
    for item in response.json_data['data']:
        assert {'title', 'content'} == set(item['attributes'].keys())
        assert len(item['relationships']) == 0
    for item in response.json_data['included']:
        assert len(item['attributes'].keys()) == 0
        assert len(item['attributes']) == 0
        assert {'author'} == set(item['relationships'].keys())


def test_200_sorted_response(bunch_of_posts, client):
    response = client.get('/api/posts/?sort=title').validate(200)
    title_list = [x['attributes']['title'] for x in response.json_data['data']]
    assert sorted(title_list) == title_list


def test_200_descending_sorted_response(bunch_of_posts, client):
    response = client.get('/api/posts/?sort=-title').validate(200)
    title_list = [x['attributes']['title'] for x in response.json_data['data']]
    assert sorted(title_list, key=None, reverse=True) == title_list


def test_200_sorted_response_with_multiple_criteria(bunch_of_posts, client):
    response = client.get('/api/posts/?sort=title,-created').validate(200)
    title_list = [x['attributes']['title'] for x in response.json_data['data']]
    assert sorted(title_list, key=None, reverse=False) == title_list


def test_409_when_given_relationship_for_sorting(bunch_of_posts, client):
    client.get('/api/posts/?sort=author').validate(409, NotSortableError)


def test_409_when_given_a_missing_field_for_sorting(bunch_of_posts, client):
    client.get('/api/posts/?sort=never_gonna_give_you_up').validate(
        409, NotSortableError)


def test_200_paginated_response_by_page(bunch_of_posts, client):
    response = client.get('/api/posts/?page[number]=2&page[size]=5').validate(
        200)
    assert len(response.json_data['data']) == 5


def test_200_paginated_response_by_offset(bunch_of_posts, client):
    response = client.get('/api/posts/?page[offset]=5&page[limit]=5').validate(
        200)
    assert len(response.json_data['data']) == 5


def test_200_when_pagination_is_out_of_range(bunch_of_posts, client):
    client.get('/api/posts/?page[offset]=999999&page[limit]=5').validate(200)


def test_400_when_provided_crap_data_for_pagination(bunch_of_posts, client):
    client.get('/api/posts/?page[offset]=5&page[limit]=crap').validate(
        400, BadRequestError)
