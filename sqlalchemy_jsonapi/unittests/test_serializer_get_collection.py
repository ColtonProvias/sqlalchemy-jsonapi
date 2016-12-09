"""Test for serializer's get_collection."""

from sqlalchemy_jsonapi import errors

from sqlalchemy_jsonapi.unittests.utils import testcases
from sqlalchemy_jsonapi.unittests import models
from sqlalchemy_jsonapi import __version__


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
                'sqlalchemy_jsonapi_version': __version__
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
                    'content': u'This is a comment'
                }
            }],
            'included': [{
                'type': 'users',
                'id': 1,
                'relationships': {
                    'posts': {
                        'links': {
                            'self': '/users/1/relationships/posts',
                            'related': '/users/1/posts'
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
                'sqlalchemy_jsonapi_version': __version__
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
                'sqlalchemy_jsonapi_version': __version__
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
                'sqlalchemy_jsonapi_version': __version__
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
                'sqlalchemy_jsonapi_version': __version__
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
                'sqlalchemy_jsonapi_version': __version__
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        actual = response.data
        self.assertEquals(expected, actual)
        self.assertEquals(200, response.status_code)

    def test_get_collection_with_single_field(self):
        """Get collection with specific field returns 200.

        The response will only contain attributes specific in field dictionary.
        """
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        log = models.Log(user_id=user.id, user=user)
        self.session.add(log)
        self.session.commit()

        response = models.serializer.get_collection(
            self.session, {'fields[users]': 'first'}, 'users')

        expected = {
            'data': [{
                'relationships': {},
                'id': 1,
                'type': 'users',
                'attributes': {
                    'first': u'Sally'
                }
            }],
            'included': [],
            'jsonapi': {
                'version': '1.0'
            },
            'meta': {
                'sqlalchemy_jsonapi_version': __version__
            }
        }
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(200, response.status_code)

    @testcases.fragile
    def test_get_collection_when_including_model_and_its_attribute(self):
        """Get collection when including the model and its attribute returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        comment = models.Comment(
            content='This is comment 1', author_id=user.id,
            post_id=blog_post.id, author=user, post=blog_post)
        self.session.add(comment)
        self.session.commit()

        response = models.serializer.get_collection(
            self.session, {'include': 'post.author'}, 'comments')

        expected = {
            'included': [{
                'id': 1,
                'type': 'users',
                'relationships': {
                    'posts': {
                        'links': {
                            'self': '/users/1/relationships/posts',
                            'related': '/users/1/posts'
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
                    'first': u'Sally',
                    'last': u'Smith'
                }
            }, {
                'id': 1,
                'type': 'posts',
                'relationships': {
                    'author': {
                        'data': {
                            'id': 1,
                            'type': 'users'
                        },
                        'links': {
                            'self': '/posts/1/relationships/author',
                            'related': '/posts/1/author'
                        }
                    },
                    'comments': {
                        'links': {
                            'self': '/posts/1/relationships/comments',
                            'related': '/posts/1/comments'
                        }
                    }
                },
                'attributes': {
                    'content': u'This is the content',
                    'title': u'This Is A Title'
                }
            }],
            'meta': {
                'sqlalchemy_jsonapi_version': __version__
            },
            'data': [{
                'id': 1,
                'type': 'comments',
                'relationships': {
                    'post': {
                        'data': {
                            'id': 1,
                            'type': 'posts'
                        },
                        'links': {
                            'self': '/comments/1/relationships/post',
                            'related': '/comments/1/post'
                        }
                    },
                    'author': {
                        'links': {
                            'self': '/comments/1/relationships/author',
                            'related': '/comments/1/author'
                        }
                    }
                },
                'attributes': {
                    'content': u'This is comment 1'
                }
            }],
            'jsonapi': {
                'version': '1.0'
            }
        }
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(200, response.status_code)

    @testcases.fragile
    def test_get_collection_given_an_included_model_that_is_null(self):
        """Get collection when given a included model that is null returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content')
        self.session.add(blog_post)
        self.session.commit()

        response = models.serializer.get_collection(
            self.session, {'include': 'author'}, 'posts')

        expected = {
            'jsonapi': {
                'version': '1.0'
            },
            'data': [{
                'id': 1,
                'type': 'posts',
                'attributes': {
                    'title': u'This Is A Title',
                    'content': u'This is the content'
                },
                'relationships': {
                    'author': {
                        'links': {
                            'related': '/posts/1/author',
                            'self': '/posts/1/relationships/author'
                        },
                        'data': None
                    },
                    'comments': {
                        'links': {
                            'related': '/posts/1/comments',
                            'self': '/posts/1/relationships/comments'
                        }
                    }
                }
            }],
            'meta': {
                'sqlalchemy_jsonapi_version': __version__
            },
            'included': []
        }
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(200, response.status_code)

    @testcases.fragile
    def test_get_collection_with_multiple_included_models(self):
        """Get collection with multiple included models returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        comment = models.Comment(
            content='This is comment 1', author_id=user.id,
            post_id=blog_post.id, author=user, post=blog_post)
        self.session.add(comment)
        self.session.commit()

        response = models.serializer.get_collection(
            self.session, {'include': 'comments,author'}, 'posts')

        expected = {
            'data': [{
                'type': 'posts',
                'id': 1,
                'relationships': {
                    'comments': {
                        'data': [{
                            'type': 'comments',
                            'id': 1
                        }],
                        'links': {
                            'related': '/posts/1/comments',
                            'self': '/posts/1/relationships/comments'
                        }
                    },
                    'author': {
                        'data': {
                            'type': 'users',
                            'id': 1
                        },
                        'links': {
                            'related': '/posts/1/author',
                            'self': '/posts/1/relationships/author'
                        }
                    }
                },
                'attributes': {
                    'title': u'This Is A Title',
                    'content': u'This is the content'
                }
            }],
            'jsonapi': {
                'version': '1.0'
            },
            'included': [{
                'type': 'users',
                'id': 1,
                'relationships': {
                    'comments': {
                        'links': {
                            'related': '/users/1/comments',
                            'self': '/users/1/relationships/comments'
                        }
                    },
                    'logs': {
                        'links': {
                            'related': '/users/1/logs',
                            'self': '/users/1/relationships/logs'
                        }
                    },
                    'posts': {
                        'links': {
                            'related': '/users/1/posts',
                            'self': '/users/1/relationships/posts'
                        }
                    }
                },
                'attributes': {
                    'last': u'Smith',
                    'first': u'Sally',
                    'username': u'SallySmith1'
                }
            }, {
                'type': 'comments',
                'id': 1,
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
                'attributes': {
                    'content': u'This is comment 1'
                }
            }],
            'meta': {
                'sqlalchemy_jsonapi_version': __version__
            }
        }
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(200, response.status_code)

    def test_get_collection_given_pagination_with_offset(self):
        """Get collection given pagination with offset 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        for x in range(10):
            comment = models.Comment(
                content='This is comment {0}'.format(x+1), author_id=user.id,
                post_id=blog_post.id, author=user, post=blog_post)
            self.session.add(comment)
        self.session.commit()

        response = models.serializer.get_collection(
            self.session,
            {'page[offset]': u'5', 'page[limit]': u'2'}, 'comments')

        expected = {
            'jsonapi': {
                'version': '1.0'
            },
            'meta': {
                'sqlalchemy_jsonapi_version': __version__
            },
            'included': [],
            'data': [{
                'relationships': {
                    'author': {
                        'links': {
                            'related': '/comments/6/author',
                            'self': '/comments/6/relationships/author'
                        }
                    },
                    'post': {
                        'links': {
                            'related': '/comments/6/post',
                            'self': '/comments/6/relationships/post'
                        }
                    }
                },
                'attributes': {
                    'content': u'This is comment 6'
                },
                'id': 6,
                'type': 'comments'
            }, {
                'relationships': {
                    'author': {
                        'links': {
                            'related': '/comments/7/author',
                            'self': '/comments/7/relationships/author'
                        }
                    },
                    'post': {
                        'links': {
                            'related': '/comments/7/post',
                            'self': '/comments/7/relationships/post'
                        }
                    }
                },
                'attributes': {
                    'content': u'This is comment 7'
                },
                'id': 7,
                'type': 'comments'
            }]
        }
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(200, response.status_code)

    def test_get_collection_given_invalid_size_for_pagination(self):
        """Get collection given invalid size for pagination returns 400.

        A BadRequestError is raised.
        """
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        for x in range(10):
            comment = models.Comment(
                content='This is comment {0}'.format(x+1), author_id=user.id,
                post_id=blog_post.id, author=user, post=blog_post)
            self.session.add(comment)
        self.session.commit()

        with self.assertRaises(errors.BadRequestError) as error:
            models.serializer.get_collection(
                self.session,
                {'page[number]': u'foo', 'page[size]': u'2'}, 'comments')

        expected_detail = 'Page query parameters must be integers'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 400)

    def test_get_collection_given_invalid_limit_for_pagination(self):
        """Get collection given invalid limit for pagination returns 400.

        A BadRequestError is raised.
        """
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        for x in range(10):
            comment = models.Comment(
                content='This is comment {0}'.format(x+1), author_id=user.id,
                post_id=blog_post.id, author=user, post=blog_post)
            self.session.add(comment)
        self.session.commit()

        with self.assertRaises(errors.BadRequestError) as error:
            models.serializer.get_collection(
                self.session,
                {'page[offset]': u'5', 'page[limit]': u'foo'}, 'comments')

        expected_detail = 'Page query parameters must be integers'
        self.assertEqual(error.exception.detail, expected_detail)
        self.assertEqual(error.exception.status_code, 400)

    def test_get_collection_when_pagnation_is_out_of_range(self):
        """Get collection when pagination is out of range returns 200."""
        user = models.User(
            first='Sally', last='Smith',
            password='password', username='SallySmith1')
        self.session.add(user)
        blog_post = models.Post(
            title='This Is A Title', content='This is the content',
            author_id=user.id, author=user)
        self.session.add(blog_post)
        for x in range(10):
            comment = models.Comment(
                content='This is comment {0}'.format(x+1), author_id=user.id,
                post_id=blog_post.id, author=user, post=blog_post)
            self.session.add(comment)
        self.session.commit()

        response = models.serializer.get_collection(
            self.session,
            {'page[offset]': u'999999', 'page[limit]': u'2'}, 'comments')

        expected = {
            'data': [],
            'included': [],
            'meta': {
                'sqlalchemy_jsonapi_version': __version__
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        actual = response.data
        self.assertEqual(expected, actual)
        self.assertEqual(200, response.status_code)
