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

# Advanced Usage

To exclude columns or relationships, list them in the `jsonapi_exclude_columns` and `jsonapi_exclude_relationships` lists in your model:

```py
class User(JSONAPIMixin, Base):
    __tablename__ = 'users'
    jsonapi_exclude_columns = ['password', 'social_security_number']
    jsonapi_exclude_relationships = ['credit_cards', 'php_test_fails']
    # ...
```

To include properties or generated relationships, use the `jsonapi_extra_columns` and `jsonapi_extra_relationships` lists:

```py
from sqlalchemy_jsonapi import as_relationship

class User(JSONAPIMixin, Base):
    __tablename__ = 'users'
    jsonapi_extra_columns = ['lines_coded']
    jsonapi_extra_relationships = ['favorite_language']
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
    jsonapi_column_data_overrides = {'id': lambda x: str(x.id)}
    jsonapi_override_relationships = {'is_admin': lambda x: x.roles.is_admin}
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