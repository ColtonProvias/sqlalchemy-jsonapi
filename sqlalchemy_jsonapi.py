"""
SQLAlchemy-JSONAPI
Colton J. Provias - cj@coltonprovias.com
http://github.com/coltonprovias/sqlalchemy-jsonapi
"""


from sqlalchemy.orm.base import MANYTOONE


class JSONAPIMixin:
    _jsonapi_converters = {}

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

        # Serialize the columns
        for column in list(self.__table__.columns):
            value = getattr(self, column.name)
            if value is not None and not isinstance(value, (str, int, float, bool)):
                value = self._jsonapi_converters[type(value).__name__](value)
            obj[self._inflector(column.name)] = value

        # Serialize the relationships
        obj['links'] = {}
        for relationship in self.__mapper__.relationships:
            rel_key = getattr(relationship.mapper.class_, '__jsonapi_key__', relationship.mapper.class_.__tablename__)
            if rel_key not in linked.keys():
                    linked[self._inflector(rel_key)] = {}
            if relationship.direction == MANYTOONE:
                for column in relationship.local_columns:
                    if self._inflector(column) in obj.keys():
                        del obj[self._inflector(column)]
                related_obj = getattr(self, relationship.key)
                obj['links'][self._inflector(relationship.key)] = str(related_obj.id)
                if depth > 0 and isinstance(related_obj, JSONAPIMixin):
                    related_obj, related_linked = related_obj.jsonapi_prepare(depth - 1)
                    linked.update(related_linked)
                    linked[self._inflector(rel_key)][str(related_obj['id'])] = related_obj
            else:
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

    def object_to_jsonapi(self, depth=1):
        """
        Serialize individual resources
        """
        obj, linked = self.jsonapi_prepare(depth)
        to_return = {self._inflector(getattr(self, '__jsonapi_key__', self.__tablename__)): [obj],
                     'linked': {},
                     'meta': {}}
        for key in linked.keys():
            to_return['linked'][key] = list(linked[key].values())
        return to_return

    @classmethod
    def collection_to_jsonapi(cls, collection, depth=1):
        """
        For serializing a collection of resources
        """
        main_key = cls._inflector(cls, getattr(cls, '__jsonapi_key__', cls.__tablename__))
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
