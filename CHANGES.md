# SQLAlchemy-JSONAPI Changelog

## 4.0.5

*2016-03-20*

* Fixed missing jsonapi_permissions attribute when patching relationships.

## 4.0.4

*2016-02-27*

* Fixed session being flushed error during POST to collection.

## 4.0.1 - 4.0.3

*2016-01-21*

* Fixed bug where the wrong map was being checked when creating new resource
* Fixed content-length bug when DELETE is provided for resources

## 4.0.0

*2016-01-20*

* BREAKING: Keys and types are now dasherized instead of underscored to fit assumptions of spec implementation
* BREAKING: Relationships are now lazy by default.  Using the include query parameter will trigger an eager load.
* Added links to relationships

## 3.0.2

*2015-10-05*

* Removed hard dependency on Flask, as suggested by @bladams in pull request #10
* Fixed autoflush on collection post as proposed by @emilecaron in issue #13
* Fixed issues when encountering integer IDs #11
* Made API Type Name overridable. #9

## 3.0.1

*2015-09-22*

* Removed an artifact from debugging.  Sorry about that to anybody who was confused!

## 3.0.0

*2015-09-20*

* BREAKING: Implements #8 where `__jsonapi_type__` is replaced with `__jsonapi_type_override__`.  This can break previous configurations where `__jsonapi_type__` was used to override the generated type.  To fix breaks, just change it to `__jsonapi_type_override__` and it should work better.  Thank you, @angelosarto for your contribution on this.

## 2.1.11

*2015-09-20*

* Fixed issue where not providing a relationships key would cause a POST or PATCH request to fail

## 2.1.10

*2015-09-20*

* Fixes compatibility with Sentry when running unit tests.  204 errors still need content.

## 2.1.9

*2015-09-20*

* Fixed issue where incomplete models get committed to multiple relationships before they earn redeeming attributes

## 2.1.8

*2015-09-19*

* Fixed issue where local columns for relationships were still appearing in responses

## 2.1.7

*2015-09-19*

* Fixed reference before assignment error

I apologize for rapid fire updates, but this is being developed alongside another project so it's trying to keep up with the main project.

## 2.1.6

*2015-09-19*

* Fixed error when TypeError is raised in descriptors

## 2.1.5

*2015-09-19*

* Permissions and actions can now be provided as sets.
* Fixed problem where users think libraries don't update often enough by pushing out 4th update on a single date

## 2.1.4

*2015-09-19*

* JSONAPIEncoder is now replaceable in the flask extension

## 2.1.3

*2015-09-19*

* Trailing slashes are now optional.  Idea based on change by @emilecaron.

## 2.1.2

*2015-09-19*

* Fixed subset comparison that prevented setting relationships when all relationships were used

## 2.1.1

*2015-09-18*

* Fixed api_key error.  My fault, killed pytest too early.

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
