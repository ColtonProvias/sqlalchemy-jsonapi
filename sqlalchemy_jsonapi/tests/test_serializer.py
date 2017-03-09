from app import api
from sqlalchemy_jsonapi import JSONAPI
import uuid


def test_include_different_types_same_id(session, comment):
    new_id = uuid.uuid4()
    comment.post.id = comment.author.id = comment.post_id = comment.author_id = new_id
    session.commit()

    r = api.serializer.get_resource(session, {'include': 'post,author'}, 'blog-comments', comment.id)
    assert len(r.data['included']) == 2


def test_no_dasherize(session, comment):
    api.serializer = JSONAPI(api.serializer.base, api.serializer.prefix,
                             options={'dasherize': False})

    r = api.serializer.get_resource(session, {}, 'blog_comments', comment.id)
    assert r.data['data']['type'] == 'blog_comments'

    api.serializer = JSONAPI(api.serializer.base, api.serializer.prefix)
