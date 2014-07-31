#SQLAlchemy-JSONAPI Changelog

## Version 0.2

*Release to be disclosed soon*

* Changed `to_serialize` in `JSONAPI.serialize` from expecting a list or collection to also expecting a query.
* Added `get_api_key` in `JSONAPI` that generates the key for the main requested resource.
* Added `fields`, `sort`, and `include` to `JSONAPI.serialize`.
* BREAKING Changed `jsonapi_*` properties to have more uniform names.
* Fixed `as_relationship` where columns weren't being set as local_columns due to SQLAlchemy-JSONAPI's developer's mistake.
* Fixed converters where it would return a KeyError.

## Version 0.1

*2014-07-20*

* Added `JSONAPI`, `JSONAPIMixin`, and `as_relationship`
