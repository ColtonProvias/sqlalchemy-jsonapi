# sqlalchemy-jsonapi

[JSON API](http://jsonapi.org/) implementation for use with [SQLAlchemy](http://www.sqlalchemy.org/).

WARNING: JSON API is currently under active development.  Thus the format of the API and this module may change drastically.

# Basic Usage

First, define your model using `JSONAPIMixin`.

```py
from sqlalchemy_jsonapi import JSONAPIMixin

class User(JSONAPIMixin, Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    # ...
```

Now, to serialize your model data, create a serializer object from `JSONAPI`:

```py
user_serializer = JSONAPI(User)
collection = session.query(User).all()
print(user_serializer.serialize(collection))
```

# Advanced Usage

TODO