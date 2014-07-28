#SQLAlchemy-JSONAPI Changelog

## Version 0.2

*Release to be disclosed soon*

* Changed `to_serialize` in `JSONAPI.serialize` from expecting a list or collection to also expecting a query.
* Added `get_api_key` in `JSONAPI` that generates the key for the main requested resource.
* Added `fields=` and `sort=` arguments to `serialize`, `dump_object`, `dump_column_data`, and `dump_relationship_data` in `JSONAPI`

## Version 0.1

*2014-07-20*

* Added `JSONAPI`, `JSONAPIMixin`, and `as_relationship`
