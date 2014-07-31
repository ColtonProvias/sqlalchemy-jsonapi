"""
SQLAlchemy-JSONAPI Serializer.

Colton J. Provias - cj@coltonprovias.com
http://github.com/coltonprovias/sqlalchemy-jsonapi
Licensed with MIT License
"""


from functools import wraps
from sqlalchemy.orm.base import MANYTOONE, ONETOMANY


def as_relationship(to_many=False, linked_key=None, link_key=None,
                    columns=[]):
    """
    Turn a method into a pseudo-relationship for serialization.

    Arguments:
    - to_many: Whether the relationship is to-many or to-one.
    - linked_key: The key used in the linked section of the serialized data
    - link_key: The key used in the link section in the model's serialization
    - columns: Columns tied to this relationship
    """
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)
        if to_many:
            wrapped.direction = ONETOMANY
        else:
            wrapped.direction = MANYTOONE

        wrapped.key = link_key or wrapped.__name__
        wrapped.linked_key = linked_key or wrapped.key
        wrapped.local_columns = columns

        return wrapped
    return wrapper


class JSONAPIMixin:

    """ Mixin that enables serialization of a model. """

    # Columns to be excluded from serialization
    jsonapi_columns_exclude = []

    # Extra columns to be included with serialization
    jsonapi_columns_include = []

    # Hook for overriding column data
    jsonapi_columns_override = {}

    # Relationships to be excluded from serialization
    jsonapi_relationships_exclude = []

    # Extra relationships to be included with serialization
    jsonapi_relationships_include = []

    # Hook for overriding relationships
    jsonapi_relationships_override = {}

    def id(self):
        """ JSON API recommends having an id for each resource. """
        raise NotImplemented

    def jsonapi_can_view(self):
        """ Return True if this model can be serialized. """
        return True


class SkipType(object):

    """ Used for skipping types during conversion. """

    pass


class JSONAPI:

    """ The main JSONAPI serializer class. """

    # A dictionary of converters for serialization
    converters = {}

    def __init__(self, model):
        """
        Create a serializer object.

        Arguments:
        - model: Should be a SQLAlchemy model class.
        """
        self.model = model

    def inflector(self, to_inflect):
        """
        Format text for use in keys in serialization.

        Override this if you need to meet requirements on your front-end.

        Arguments:
        - to_inflect: The string to be inflected

        Returns the altered string.
        """
        return to_inflect

    def convert(self, item, to_convert):
        """
        Convert from Python objects to JSON-friendly values.

        Arguments:
        - item: A SQLAlchemy model instance
        - to_convert: Python object to be converted

        Returns either a string, int, float, bool, or SkipType.
        """
        if to_convert is None:
            return None
        if isinstance(to_convert, (str, int, float, bool)):
            return to_convert
        if callable(to_convert):
            return to_convert(item)
        if self.converters[type(to_convert).__name__] is not None:
            converter = self.converters[type(to_convert).__name__]
            return converter(to_convert)
        return SkipType

    def get_api_key(self, model):
        """
        Generate a key for a model.

        Arguments:
        - model: SQLAlchemy model instance

        Returns an inflected key that is generated from jsonapi_key or from
        __tablename__.
        """
        api_key = getattr(model, 'jsonapi_key', model.__tablename__)
        return self.inflector(api_key)

    def sort_query(self, model, query, sorts):
        """
        Sort a query based upon provided sorts.

        Arguments:
        - model: SQLAlchemy model class
        - query: Instance of Query or AppenderQuery
        - sorts: A dictionary of sorts keyed by the api_key for each model

        Returns a query with appropriate order_by appended.
        """
        if sorts is None:
            return query
        api_key = self.get_api_key(model)
        for sort in sorts[api_key]:
            if sort.startswith('-'):
                sort_by = getattr(model, sort[1:]).desc()
            else:
                sort_by = getattr(model, sort)
            query = query.order_by(sort_by)
        return query

    def parse_include(self, include):
        """
        Parse the include query parameter.

        Arguments:
        - include: A list of resources to be included by link_keys

        Returns a dictionary of the parsed include list.  A None value
        signifies that the resource itself should be dumped.
        """
        ret = {}
        for item in include:
            if '.' in item:
                local, remote = item.split('.', maxsplit=1)
            else:
                local = item
                remote = None
            if local not in ret.keys():
                ret[local] = []
            ret[local].append(remote)
        return ret

    def dump_column_data(self, item, fields):
        """
        Dump the data from the colums of a model instance.

        Arguments:
        - item: An SQLAlchemy model instance
        - fields: A list of requested fields.  If it is None, all available
                  fields will be returned.

        Returns a dictionary representing the instance's data.
        """
        obj = dict()
        columns = list(item.__table__.columns)
        column_data = dict()
        api_key = self.get_api_key(item)

        for column in columns:
            if column.name in item.jsonapi_columns_exclude:
                continue
            column_data[column.name] = getattr(item, column.name)

        for column in item.jsonapi_columns_include:
            column_data[column] = getattr(item, column)

        column_data.update(item.jsonapi_columns_override)

        for name, value in column_data.items():
            key = self.inflector(name)
            if key != 'id' and fields is not None and \
                    api_key in fields.keys() and \
                    key not in fields[api_key]:
                continue
            converted = self.convert(item, value)
            if converted != SkipType:
                obj[key] = converted
        return obj

    def dump_relationship_data(self, item, obj, depth, fields, sort, include):
        """
        Handle relationship dumping for a model.

        Arguments:
        - item: SQLAlchemy model instance
        - obj: Column data for the model post-dump
        - depth: How much deeper into the relationships do we have to go
                 captain?
        - fields: A dictionary of fields to be parsed based on linked_keys.
        - sort: A dictionary of fields to sort by
        - include: A list of resources to be included by link_keys.
        """
        relationships = dict(list(map((lambda x: (x.key, x)),
                                      item.__mapper__.relationships)))

        for key in item.jsonapi_relationships_exclude:
            if key not in relationships.keys():
                continue
            del relationships[key]

        for key in item.jsonapi_relationships_include:
            relationships[key] = getattr(item, key)

        for key, value in item.jsonapi_relationships_override:
            relationships[key] = getattr(item, value)

        if include is not None:
            include = self.parse_include(include)

        obj['links'] = {}
        linked = {}
        for key, relationship in relationships.items():
            dump_this = True
            link_key = self.inflector(key)
            if hasattr(relationship, 'mapper'):
                mapper = relationship.mapper.class_
                linked_key = self.inflector(getattr(mapper, 'jsonapi_key',
                                                    mapper.__tablename__))
            else:
                linked_key = self.inflector(relationship.linked_key)

            if relationship.direction == MANYTOONE:
                for column in relationship.local_columns:
                    if isinstance(column, str):
                        col_name = self.inflector(column)
                    else:
                        col_name = self.inflector(column.name)
                    if col_name in obj.keys():
                        obj['links'][link_key] = self.convert(item,
                                                              obj[col_name])
                        del obj[col_name]

            if include is not None:
                if link_key not in include.keys():
                    continue
                local_include = include[link_key]
                if None in include[link_key]:
                    local_include.remove(None)
                else:
                    dump_this = False
            else:
                local_include = None

            if depth > 0 or (include is not None and
                             local_include is not None):
                if callable(relationship):
                    related = relationship()
                else:
                    related = getattr(item, relationship.key)
                if relationship.direction == MANYTOONE:
                    if isinstance(related, JSONAPIMixin):
                        if not related.jsonapi_can_view():
                            continue
                        if dump_this and linked_key not in linked.keys():
                            linked[linked_key] = {}
                        r_obj, r_lnk = self.dump_object(related, depth - 1,
                                                        fields, sort,
                                                        local_include)
                        linked.update(r_lnk)
                        if dump_this:
                            linked[linked_key][str(r_obj['id'])] = r_obj
                else:
                    if sort is not None and linked_key in sort.keys():
                        related = self.sort_query(mapper, related, sort)
                    if link_key not in obj['links'].keys():
                            obj['links'][link_key] = []
                    for local_item in list(related):
                        if not isinstance(local_item, JSONAPIMixin):
                            continue
                        if not local_item.jsonapi_can_view():
                            continue
                        if dump_this and linked_key not in linked.keys():
                            linked[linked_key] = {}
                        obj['links'][link_key].append(str(local_item.id))
                        r_obj, r_lnk = self.dump_object(local_item, depth - 1,
                                                        fields, sort,
                                                        local_include)
                        linked.update(r_lnk)
                        if dump_this:
                            linked[linked_key][str(r_obj['id'])] = r_obj
        return obj, linked

    def dump_object(self, item, depth, fields, sort, include):
        """
        Quick, simple way of coordinating a dump.

        Arguments:
        - item: Instance of a SQLAlchemy model
        - depth: Integer of how deep relationships should be queried
        - fields: Dictionary of fields to be returned, keyed by linked_keys
        - sort: Dictionary of fields to sory by, keyed by linked_keys
        - include: List of resources to side-load by link_keys.
        """
        obj = self.dump_column_data(item, fields)
        return self.dump_relationship_data(item, obj, depth, fields, sort,
                                           include)

    def serialize(self, to_serialize, depth=1, fields=None, sort=None,
                  include=None):
        """
        Perform the serialization to dictionary in JSON API format.

        Arguments:
        - to_serialize: The query, collection, or instance to serialize.
        - depth: How deep to side-load relationships.  If include is provided,
                 this will be overridden
        - fields: Dictionary of fields to be returned keyed by linked_keys or
                  a list of fields for the current instance
        - sort: Dictionary of fields to sort by keyed by linked_keys or a list
                of fields to sort by for the current instance
        - include: List of resources to side-load by link_keys.
        """
        api_key = self.get_api_key(self.model)

        to_return = {api_key: [], 'linked': {}, 'meta': {}}
        linked = dict()

        if isinstance(to_serialize, JSONAPIMixin):
            is_single = True
            to_serialize = [to_serialize]
        else:
            is_single = False

        if isinstance(fields, list):
            fields = {api_key: fields}

        if isinstance(sort, list):
            sort = {api_key: sort}

        if not is_single:
            to_serialize = self.sort_query(self.model, to_serialize, sort)

        for item in to_serialize:
            if not item.jsonapi_can_view():
                continue
            dumped = self.dump_object(item, depth, fields, sort, include)
            if dumped is None:
                continue

            obj, new_linked = dumped
            to_return[api_key].append(obj)

            for key in new_linked.keys():
                if key not in linked.keys():
                    linked[key] = dict()
                linked[key].update(new_linked[key])

        for key in linked.keys():
            to_return['linked'][key] = list(linked[key].values())

        if is_single:
            to_return[api_key] = to_return[api_key][0]

        return to_return
