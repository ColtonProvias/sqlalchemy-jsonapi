"""
SQLAlchemy-JSONAPI
Colton J. Provias - cj@coltonprovias.com
http://github.com/coltonprovias/sqlalchemy-jsonapi
"""


from sqlalchemy.orm.base import MANYTOONE


class JSONAPIMixin:
    """
    Add this mixin to the models that you want to be accessible via your API.
    """
    _jsonapi_converters = {}
    _jsonapi_exclude_columns = []
    _jsonapi_extra_columns = []
    _jsonapi_column_data_overrides = {}
    

    def _inflector(self, to_inflect):
        """
        Override this to change the formatting of the keys in the generated
        dict.
        """
        return to_inflect

    def jsonapi_prepare(self, depth):
        """
        Returns a tuple of obj, linked that is almost ready for the final
        serialization to JSON API format.
        """
        obj = {}
        linked = {}

        columns = list(self.__table__.columns)

        column_data = {}
        for column in columns:
            if column.name in self._jsonapi_exclude_columns:
                continue
            column_data[column.name] = getattr(self, column.name)

        for column in self._jsonapi_extra_columns:
            column_data[column] = getattr(self, column)

        column_data.update(self._jsonapi_column_data_overrides)

        for name, value in column_data.items():
            key = self._inflector(name)
            if value is None:
                obj[key] = None
            elif isinstance(value, (str, int, float, bool)):
                obj[key] = value
            elif callable(value):
                obj[key] = value(self)
            else:
                obj[key] = self._jsonapi_converters[type(value).__name__](value)

        # Serialize the relationships
        obj['links'] = {}
        for relationship in self.__mapper__.relationships:
            rel_key = getattr(relationship.mapper.class_, '_jsonapi_key', relationship.mapper.class_.__tablename__)
            if rel_key not in linked.keys():
                    linked[self._inflector(rel_key)] = {}
            if relationship.direction == MANYTOONE:
                for column in relationship.local_columns:
                    if self._inflector(column) in obj.keys():
                        obj['links'][self._inflector(relationship.key)] = str(obj[self._inflector(column)])
                        del obj[self._inflector(column)]
                if depth > 0:
                    related_obj = getattr(self, relationship.key)
                    if isinstance(related_obj, JSONAPIMixin):
                        related_obj, related_linked = related_obj.jsonapi_prepare(depth - 1)
                        linked.update(related_linked)
                        linked[self._inflector(rel_key)][str(related_obj['id'])] = related_obj
            elif depth > 0:
                obj['links'][self._inflector(relationship.key)] = []
                related_objs = getattr(self, relationship.key)
                for item in related_objs.all():
                    if not isinstance(item, JSONAPIMixin):
                        continue
                    obj['links'][self._inflector(relationship.key)].append(str(item.id))
                    new_obj, new_linked = item.jsonapi_prepare(depth - 1)
                    linked.update(new_linked)
                    linked[self._inflector(rel_key)][str(new_obj['id'])] = new_obj
        return obj, linked

    @classmethod
    def collection_to_jsonapi(cls, collection, depth=1):
        """
        For serializing a collection of resources
        """
        main_key = cls._inflector(cls, getattr(cls, '_jsonapi_key', cls.__tablename__))
        to_return = {main_key: [], 'linked': {}, 'meta': {}}
        linked = {}
        for item in collection:
            serialized = item.jsonapi_prepare(depth)
            if serialized is None:
                continue
            obj, new_linked = serialized
            to_return[main_key].append(obj)
            for key in new_linked.keys():
                if key not in linked.keys():
                    linked[key] = {}
                linked[key].update(new_linked[key])
        for key in linked.keys():
            to_return['linked'][key] = list(linked[key].values())
        return to_return
