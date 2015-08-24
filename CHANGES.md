# SQLAlchemy-JSONAPI Changelog

## 1.0.0 - Start of 1.0 Compatibility

*In Development*

* BREAKING Complete rewrite for JSON API 1.0 compatibility
* Switching to Semantic Versioning

## 0.2 - Querying and View Permissions

*2014-07-31*

* Changed `to_serialize` in `JSONAPI.serialize` from expecting a list or collection to also expecting a query.
* Added `get_api_key` in `JSONAPI` that generates the key for the main requested resource.
* Added `fields`, `sort`, and `include` to `JSONAPI.serialize`.
* BREAKING Changed `jsonapi_*` properties to have more uniform names.
* Fixed `as_relationship` where columns weren't being set as local_columns due to SQLAlchemy-JSONAPI's developer's mistake.
* Fixed converters where it would return a KeyError.
* Added `jsonapi_can_view()` to `JSONAPIMixin`.

## 0.1 - Initial

*2014-07-20*

* Added `JSONAPI`, `JSONAPIMixin`, and `as_relationship`
