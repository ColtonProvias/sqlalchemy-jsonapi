"""
SQLAlchemy-JSONAPI
Colton J. Provias - cj@coltonprovias.com
http://github.com/coltonprovias/sqlalchemy-jsonapi
"""


from functools import wraps
from sqlalchemy.orm.base import MANYTOONE, ONETOMANY


def as_relationship(to_many=False, linked_key=None, link_key=None,
                    columns=[]):
    """
    Decorates methods to add on properties needed to make them act like
    relationships.
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
    """
    Add this mixin to the models that you want to be accessible via your API.
    """
    jsonapi_columns_exclude = []
    jsonapi_columns_include = []
    jsonapi_columns_override = {}

    jsonapi_relationships_exclude = []
    jsonapi_relationships_include = []
    jsonapi_relationships_override = {}

    def id(self):
        """ JSON API recommends having an id for each resource """
        raise NotImplemented

    def jsonapi_can_view(self):
        return True


class SkipType(object):
    """
    Just a quick thing to help skip conversions.  It's very useful for
    passwords.
    """
    pass


class JSONAPI:
    """
    The JSONAPI Serializer.  This class can be overridden as necessary.
    """
    converters = {}

    def __init__(self, model):
        """
        Let's get started!  The model must be a class of a SQLAlchemy model.
        """
        self.model = model

    def inflector(self, to_inflect):
        """
        Override this to inflect the keys in your API.  This is useful for
        example with ember-json-api, which prefers camelCase.
        """
        return to_inflect

    def convert(self, item, to_convert):
        """
        Converts from a provided type to something a little nicer for JSON
        serialization
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
        api_key = getattr(model, 'jsonapi_key', model.__tablename__)
        return self.inflector(api_key)

    def sort_query(self, model, query, sorts):
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
        Dumps the data from the columns/properties for a model instance.
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
        Dumps all of the data related to relationships, modifying the dumped
        object as necessary.
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
        Just something to override if you want to change the way data is
        pre-processed prior to the dump.
        """
        obj = self.dump_column_data(item, fields)
        return self.dump_relationship_data(item, obj, depth, fields, sort,
                                           include)

    def serialize(self, to_serialize, depth=1, fields=None, sort=None,
                  include=None):
        """
        Call this to return a dict containing the dumped collection or object.
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
