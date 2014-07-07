# sqlalchemy-jsonapi

[JSON API](http://jsonapi.org/) implementation for use with [SQLAlchemy](http://www.sqlalchemy.org/).

WARNING: JSONAPI is currently under active development.  Thus the format of the API may change.

## Basic Usage

```py
from sqlalchemy_jsonapi import JSONAPIMixin

class User(JSONAPIMixin, Base):
    __tablename__ = 'users'
    # ... Model definition here ...

# ...

# Return the JSON API data
print(User.collection_to_jsonapi(session.query(User).all()))
```

## Larger example

Please see [example.py](example.py) for a more complete example.

## API

### sqlalchemy_jsonapi.JSONAPIMixin

#### jsonapi_converters

A dictionary of additional converters to serialize data with.  For example, if you have a `UUID` and wish to convert it into a string:

```py
jsonapi_converters = {'UUID': str}
```

If you wish to make sure a type is never included, set it to `None`:

```py
jsonapi_converters = {'Password': None}
```

#### jsonapi_exclude_columns

A list of column names to be excluded from this model's JSON API serialization.  This can even be made dynamic, as such:

```py
@property
def jsonapi_exclude_columns(self):
    if current_user.id != self.id:
        return ['email']
    return []
```

#### jsonapi_extra_columns

If you have any extra properties, this is a quick shortcut to include them with.

```py
jsonapi_extra_columns = ['full_name']

@property
def full_name(self):
    return self.first_name + ' ' + self.last_name
```

#### jsonapi_column_data_overrides

A more advanced feature for when you need to override data before it is sent out.  Any callable will be executed with `self` as the argument.

```py
jsonapi_column_data_overrides = {
    'id': lambda self: str(self.id),
}
```
    
#### jsonapi_inflector(self, to_inflect)

Gives you an opportunity to normalize the keys.  For example, [ember-json-api](https://github.com/daliwali/ember-json-api) prefers camelCase keys:

```py
# Using the inflection library
from inflection import camelize

def jsonapi_inflector(self, to_inflect):
    return camelize(to_inflect)
```

#### jsonapi_prepare(self, depth)

Returns a tuple of `(object, linked)`.  This should rarely be called directly.

```py
user = User.query.first()
user.jsonapi_prepare(100)  # 100 is great for those cold winter days
```

#### collection_to_jsonapi(self, collection, depth=1)

Returns a dictionary representation of a JSON API serialized collection.

```py
# For a collection
users = User.query.all()
User.collection_to_jsonapi(users)

# For an individual resource
user = User.query.first()
User.collection_to_jsonapi([user])
```
