"""
SQLAlchemy-JSONAPI Example
Colton J. Provias - cj@coltonprovias.com

An example of basic usage of SQLAlchemy-JSONAPI
"""

from pprint import pprint
from sqlalchemy import create_engine, Column, Integer, Unicode, UnicodeText
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_jsonapi import JSONAPIMixin

# Start your engines...and session.
engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()
session = sessionmaker(bind=engine)()


# Extend the JSONAPIMixin so we can convert numerial IDs into strings.
# This is not done automatically so as to be more back-end agnostic
class APIMixin(JSONAPIMixin):
    jsonapi_column_data_overrides = {
        'id': lambda self: str(self.id)
    }


# Model definitions
class User(APIMixin, Base):
    __tablename__ = 'users'

    # We don't want the password to be sent in the response, so we exclude it.
    jsonapi_exclude_columns = ['password']
    id = Column(Integer, primary_key=True)
    username = Column(Unicode(30))
    password = Column(Unicode(30))


class Post(APIMixin, Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(Unicode(100))
    content = Column(UnicodeText)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship('User', lazy='joined',
                        backref=backref('posts', lazy='dynamic'))

class Comment(APIMixin, Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    content = Column(UnicodeText)
    user_id = Column(Integer, ForeignKey('users.id'))
    post_id = Column(Integer, ForeignKey('posts.id'))

    user = relationship('User', lazy='joined',
                        backref=backref('comments', lazy='dynamic'))
    post = relationship('Post', lazy='joined',
                        backref=backref('comments', lazy='dynamic'))

# Initialize the database and fill it with some sample data
Base.metadata.create_all(engine)

user = User(username='sampleuser', password='Secret')
post = Post(title='Sample Post',
            content='Lorem ipsum dolor sit amet fakus latinus',
            user=user)
comment = Comment(content='Sample comment',
                  user=user, post=post)
session.add(user)
session.commit()

# Now to call the SQLAlchemy-JSONAPI serializer.  Just Pass it a collection.
# For individual resources, just wrap them in a list.
collection = session.query(Post).all()
json_api_dict = Post.collection_to_jsonapi(collection)

# Finally, let's see what the output is.
pprint(json_api_dict)

"""
Output from the pprint statement:

{'linked': {'comments': [{'content': 'Sample comment',
                          'id': '1',
                          'links': {'post': '1', 'user': '1'}}],
            'users': [{'id': '1', 'links': {}, 'username': 'sampleuser'}]},
 'meta': {},
 'posts': [{'content': 'Lorem ipsum dolor sit amet fakus latinus',
            'id': '1',
            'links': {'comments': ['1'], 'user': '1'},
            'title': 'Sample Post'}]}
"""