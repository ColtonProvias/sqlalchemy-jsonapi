"""Test for serializer's get_collection."""

from sqlalchemy_jsonapi.unittests.utils import testcases
from sqlalchemy_jsonapi.unittests import models


class GetCollection(testcases.SqlalchemyJsonapiTestCase):
    """Tests for serializer.get_collection."""

    def test_get_collection_response_with_no_query_args(self):
        """Get collection with no query params returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        comment = models.Comment(
            content='This is a comment', author_id=user.id,
            post_id=blog_post.id, author=user, post=blog_post)
        self.session.add(comment)
        self.session.commit()

        response = models.serializer.get_collection(
            self.session, {}, 'comments')

        expected = {
            'data': [{
                'attributes': {
                    'content': 'This is a comment'
                },
                'type': 'comments',
                'relationships': {
                    'author': {
                        'links': {
                            'related': '/comments/1/author',
                            'self': '/comments/1/relationships/author'
                        }
                    },
                    'post': {
                        'links': {
                            'related': '/comments/1/post',
                            'self': '/comments/1/relationships/post'
                        }
                    }
                },
                'id': 1
            }],
            'jsonapi': {
                'version': '1.0'
            },
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'included': []
        }
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(200, response.status_code)

    @testcases.fragile
    def test_get_collection_response_with_single_include_model(self):
        """Get collection with single included model returns 200.

        This test is fragile.
        """
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        comment = models.Comment(
            content='This is a comment', author_id=user.id,
            post_id=blog_post.id, author=user, post=blog_post)
        self.session.add(comment)
        self.session.commit()

        response = models.serializer.get_collection(
            self.session, {'include': 'author'}, 'comments')

        expected = {
            'data': [{
                'type': 'comments',
                'id': 1,
                'relationships': {
                    'author': {
                        'data': {
                            'type': 'users',
                            'id': 1
                        },
                        'links': {
                            'self': '/comments/1/relationships/author',
                            'related': '/comments/1/author'
                        }
                    },
                    'post': {
                        'links': {
                            'self': '/comments/1/relationships/post',
                            'related': '/comments/1/post'
                        }
                    }
                },
                'attributes': {
                    'content': 'This is a comment'
                }
            }],
            'included': [{
                'type': 'users',
                'id': 1,
                'relationships': {
                    'posts': {
                        'links': {
                            'self': '/users/1/relationships/post',
                            'related': '/users/1/post'
                        }
                    },
                    'comments': {
                        'links': {
                            'self': '/users/1/relationships/comments',
                            'related': '/users/1/comments'
                        }
                    },
                    'logs': {
                        'links': {
                            'self': '/users/1/relationships/logs',
                            'related': '/users/1/logs'
                        }
                    }
                },
                'attributes': {
                    'username': u'SallySmith1',
                    'last': u'Smith',
                    'first': u'Sally'
                }
            }],
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            },
        }
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(200, response.status_code)

    def test_get_collection_asc_sorted_response(self):
        """Get collection with ascending sorted response returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        for x in reversed(range(2)):
            comment = models.Comment(
                content='This is comment {0}'.format(x+1), author_id=user.id,
                post_id=blog_post.id, author=user, post=blog_post)
            self.session.add(comment)
        self.session.commit()

        response = models.serializer.get_collection(
            self.session, {'sort': 'content'}, 'comments')

        expected = {
            'data': [{
                'relationships': {
                    'author': {
                        'links': {
                            'related': '/comments/2/author',
                            'self': '/comments/2/relationships/author'
                        }
                    },
                    'post': {
                        'links': {
                            'related': '/comments/2/post',
                            'self': '/comments/2/relationships/post'
                        }
                    }
                },
                'type': 'comments',
                'attributes': {
                    'content': u'This is comment 1'
                },
                'id': 2
            }, {
                'relationships': {
                    'author': {
                        'links': {
                            'related': '/comments/1/author',
                            'self': '/comments/1/relationships/author'
                        }
                    },
                    'post': {
                        'links': {
                            'related': '/comments/1/post',
                            'self': '/comments/1/relationships/post'
                        }
                    }
                },
                'type': 'comments',
                'attributes': {
                    'content': u'This is comment 2'
                },
                'id': 1
            }],
            'jsonapi': {
                'version': '1.0'
            },
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'included': []
        }
        actual = response.data
        self.assertEquals(expected, actual)
        self.assertEquals(200, response.status_code)

    def test_get_collection_desc_sorted_response(self):
        """Get collection with descending sorted response returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        for x in range(2):
            comment = models.Comment(
                content='This is comment {0}'.format(x+1), author_id=user.id,
                post_id=blog_post.id, author=user, post=blog_post)
            self.session.add(comment)
        self.session.commit()

        response = models.serializer.get_collection(
            self.session, {'sort': '-content'}, 'comments')

        expected = {
            'data': [{
                'relationships': {
                    'author': {
                        'links': {
                            'related': '/comments/2/author',
                            'self': '/comments/2/relationships/author'
                        }
                    },
                    'post': {
                        'links': {
                            'related': '/comments/2/post',
                            'self': '/comments/2/relationships/post'
                        }
                    }
                },
                'type': 'comments',
                'attributes': {
                    'content': u'This is comment 2'
                },
                'id': 2
            }, {
                'relationships': {
                    'author': {
                        'links': {
                            'related': '/comments/1/author',
                            'self': '/comments/1/relationships/author'
                        }
                    },
                    'post': {
                        'links': {
                            'related': '/comments/1/post',
                            'self': '/comments/1/relationships/post'
                        }
                    }
                },
                'type': 'comments',
                'attributes': {
                    'content': u'This is comment 1'
                },
                'id': 1
            }],
            'jsonapi': {
                'version': '1.0'
            },
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'included': []
        }
        actual = response.data
        self.assertEquals(expected, actual)
        self.assertEquals(200, response.status_code)

    def test_get_collection_response_with_relationship_for_sorting(self):
        """Get collection with relationship for sorting results in 409.

        A NotSortableError is returned.
        """
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='Thfsessis Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        self.session.commit()

        response = models.serializer.get_collection(
            self.session, {'sort': 'author'}, 'posts')

        self.assertEquals(409, response.status_code)

    def test_get_collection_response_given_invalid_sort_field(self):
        """Get collection given an invalid sort field results in 409.

        A NotSortableError is returned.
        """
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        self.session.commit()

        response = models.serializer.get_collection(
            self.session, {'sort': 'invalid_field'}, 'posts')

        expected = 'The requested field posts on type invalid_field is not a sortable field.'
        self.assertEquals(expected, response.detail)
        self.assertEquals(409, response.status_code)

    def test_get_collection_access_denied(self):
        """Get collection with access denied results in 200.

        The response data should be empty list.
        """
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        log = models.Log(user=user, user_id=user.id)
        self.session.add(log)
        self.session.commit()

        response = models.serializer.get_collection(self.session, {}, 'logs')

        expected = {
            'data': [],
            'included': [],
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        actual = response.data
        self.assertEquals(expected, actual)
        self.assertEquals(200, response.status_code)

    def test_get_collection_paginated_response_by_page(self):
        """Get collection with pagination by page returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        for x in range(20):
            comment = models.Comment(
                content='This is comment {0}'.format(x+1), author_id=user.id,
                post_id=blog_post.id, author=user, post=blog_post)
            self.session.add(comment)
        self.session.commit()

        response = models.serializer.get_collection(
            self.session,
            {'page[number]': u'1', 'page[size]': u'2'}, 'comments')

        expected = {
            'data': [{
                'id': 3,
                'attributes': {
                    'content': u'This is comment 3'
                },
                'type': 'comments',
                'relationships': {
                    'author': {
                        'links': {
                            'self': '/comments/3/relationships/author',
                            'related': '/comments/3/author'
                        }
                    },
                    'post': {
                        'links': {
                            'self': '/comments/3/relationships/post',
                            'related': '/comments/3/post'
                        }
                    }
                }
            }, {
                'id': 4,
                'attributes': {
                    'content': u'This is comment 4'
                },
                'type': 'comments',
                'relationships': {
                    'author': {
                        'links': {
                            'self': '/comments/4/relationships/author',
                            'related': '/comments/4/author'
                        }
                    },
                    'post': {
                        'links': {
                            'self': '/comments/4/relationships/post',
                            'related': '/comments/4/post'
                        }
                    }
                }
            }],
            'included': [],
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        actual = response.data
        self.assertEquals(expected, actual)
        self.assertEquals(200, response.status_code)
