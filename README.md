# sqlalchemy-jsonapi

[JSON API](http://jsonapi.org/) implementation for use with [SQLAlchemy](http://www.sqlalchemy.org/).

WARNING: JSON API is currently under active development.  Thus the format of the API and this module may change drastically.

# Installation

Just install the package via pip.

```
pip install sqlalchemy-jsonapi
```

# Basic Usage

First, define your model using `JSONAPIMixin`.

```py
from sqlalchemy_jsonapi import JSONAPIMixin, JSONAPI

class User(JSONAPIMixin, Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    # ...
```

Now, to serialize your model data, create a serializer object from `JSONAPI`:

```py
user_serializer = JSONAPI(User)
query = session.query(User)
print(user_serializer.serialize(query))
```

And for individual resources:

```py
user_serializer = JSONAPI(User)
my_user = session.query(User).get(1)
print(user_serializer.serialize(my_user))
```

# Querying

## Sparse Fieldsets

To change the fieldset return, just include the `fields=` parameter when calling `serialize`.

```py
user_serializer.serialize(my_user, fields=['id', 'username', 'is_admin'])

# Or for fieldsets across models:

user_serializer.serialze(my_user, fields={'users': ['username', 'is_admin'],
                                          'posts': ['title', 'created_at']})
```

## Sorting

Sorting is very similar to the implementation of sparse fieldsets above.  Descending sorts are prefix with a `-`.

```py
user_serializer.serialize(my_user, sort=['username'])

# For across models:

user_serializer.serialize(my_user, sort={'users': ['username'],
                                         'posts': ['-created_at']})
```

Note: Sorting only works on relationships that return an `sqlalchemy.orm.dynamic.AppenderQuery` at this time.  This is expected to be fixed soon as soon as I figure out the best way to implement it that isn't too hackish.

## Includes

The JSON API spec specifies a method to include resources to be sideloaded.  By default, SQLAlchemy-JSONAPI will include all available relationships.  However, if list is passed to `JSONAPI.serialize` via the `include` argument, it will override the default.

For example, let's assume you received a request at `/users?include=comments,posts.tags`.  To handle this, it becomes very easy:

```py
# Split the string into a list
parsed_include = request.args.get('include', '').split(',')

user_serializer.serialize(user_query, include=parsed_include)
```

Just like sparse fieldsets above, this will only be able to access resources that it would otherwise have access to.  Thus if you have a model that has `jsonapi_relationships_exclude` set to `['government_secret']`, having `include=['government_secrets']` will not return that relationship.

# Advanced Usage

To exclude columns or relationships, list them in the `jsonapi_columns_exclude` and `jsonapi_relationships_exclude` lists in your model:

```py
class User(JSONAPIMixin, Base):
    __tablename__ = 'users'
    jsonapi_columns_exclude = ['password', 'social_security_number']
    jsonapi_relationships_exclude = ['credit_cards', 'php_test_fails']
    # ...
```

To include properties or generated relationships, use the `jsonapi_columns_include` and `jsonapi_relationships_include` lists:

```py
from sqlalchemy_jsonapi import as_relationship

class User(JSONAPIMixin, Base):
    __tablename__ = 'users'
    jsonapi_columns_include = ['lines_coded']
    jsonapi_relationships_include = ['favorite_language']
    # ...

    @property
    def lines_coded(self):
        return self.lines.count()

    @as_relationship()
    def favorite_language(self):
        return self.languages.filter_by(is_favorite=True).first()
```

To override a property or relationship, you can simply exclude and then include.  Or you can do a shortcut:

```py
class User(JSONAPIMixin, Base):
    __tablename__ = 'users'
    jsonapi_columns_override = {'id': lambda x: str(x.id)}
    jsonapi_relationships_override = {'is_admin': lambda x: x.roles.is_admin}
```

To add converters, simply subclass `JSONAPI` and use the converters property.  Setting a type to `None` will prevent it from being serialized.  For example:

```py
class MySerializer(JSONAPI):
    converters = {'UUID': str,
                  'Password': None}
```

And finally, if you need your keys to be in a different format, override the inflector.

```py
class MySerializer(JSONAPI):
    def inflector(self, to_inflect):
        return to_inflect.upper()
```

## On the topic of IDs

In the JSON API spec, the `id` key is a reserved keyword for unique IDs for each object.  Of course not all databases conform to this standard and it can get quite frustrating.  However, having an issue such as compound primary keys can be remedied easily.  Here's the quick and easy way to do it:

```py
class Video(JSONAPIMixin, Base):
    __tablename__ = 'videos'
    server_id = Column(Integer, primary_key=True)
    video_id = Column(Integer, primary_key=True)

    # Tell SQLAlchemy-JSONAPI that we are adding an extra column called `id`
    jsonapi_columns_include = ['id']

    @property
    def id(self):
        # Acts as a column, returning a concatenated string of the two IDs.
        # You can choose whatever format you want, but the returned value
        # SHOULD be a string as per JSON API spec.
        return str(self.server_id) + ':' + str(self.video_id)
```