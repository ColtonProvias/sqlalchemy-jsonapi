# SQLAlchemy-JSONAPI Changelog

## 2.1.0

*2015-09-18*

* Added wrapping/chaining of handlers via a simple decorator

## 2.0.3

*2015-09-17*

* Merged #7 by @angelosarto.  Fixed type of related items returned in relationships.

## 2.0.2

*2015-09-16*

* Fixes Python 2.7 compatibility

## 2.0.1

*2015-09-16*

* Fixed #6 where flask may conflict with flask package on Python 2.7.

## 2.0.0 - Interface Fix

*2015-08-29*

* BREAKING Replaced dict params with api_type, obj_id, and rel_key

## 1.0.0 - Start of 1.0 Compatibility

*2015-08-24*

* BREAKING Complete rewrite for JSON API 1.0 compatibility
* CHANGED Switching to Semantic Versioning

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
