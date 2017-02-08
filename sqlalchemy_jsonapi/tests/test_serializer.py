from app import api
import uuid


def test_include_different_types_same_id(session, comment):
    new_id = uuid.uuid4()
    comment.post.id = comment.author.id = comment.post_id = comment.author_id = new_id
    session.commit()

    r = api.serializer.get_resource(session, {'include': 'post,author'}, 'blog-comments', comment.id)
    assert len(r.data['included']) == 2
