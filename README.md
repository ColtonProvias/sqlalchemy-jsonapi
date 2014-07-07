# sqlalchemy-jsonapi

JSONAPI implementation for use with SQLAlchemy

WARNING: JSONAPI is currently under active development.  Thus the format of the API may change.

## Basic Usage

```py
from sqlalchemy_jsonapi import JSONAPIMixin

class User(JSONAPIMixin, Base):
    __tablename__ = 'users'
    # ... Model definition here ...

# ...

# Return the JSONAPI data
print(User.collection_to_jsonapi(session.query(User).all()))
```

## Larger example

Please see [example.py](example.py) for a more complete example.