"""
SQLAlchemy-JSONAPI
Serializer
Colton J. Provias
MIT License
"""

from enum import Enum
from inflection import pluralize, underscore
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.interfaces import MANYTOONE
from sqlalchemy.util.langhelpers import iterate_attributes

from .errors import (BadRequestError, InvalidTypeForEndpointError,
                     MissingTypeError, NotSortableError, PermissionDeniedError,
                     RelationshipNotFoundError, ResourceNotFoundError,
                     ResourceTypeNotFoundError, ToManyExpectedError,
                     ValidationError)


class AttributeActions(Enum):
    """ The actions that can be done to an attribute. """

    GET = 0
    SET = 1


class RelationshipActions(Enum):
    """ The actions that can be performed on a relationship. """

    GET = 10
    APPEND = 11
    SET = 12
    DELETE = 13


class Permissions(Enum):
    """ The permissions that can be set. """

    VIEW = 100
    CREATE = 101
    EDIT = 102
    DELETE = 103


ALL_PERMISSIONS = {
    Permissions.VIEW, Permissions.CREATE, Permissions.EDIT, Permissions.DELETE
}
INTERACTIVE_PERMISSIONS = {
    Permissions.CREATE, Permissions.EDIT, Permissions.DELETE
}


def attr_descriptor(action, *names):
    """
    Wrap a function that allows for getting or setting of an attribute.  This
    allows for specific handling of an attribute when it comes to serializing
    and deserializing.

    :param action: The AttributeActions that this descriptor performs
    :param names: A list of names of the attributes this references
    """
    if isinstance(action, AttributeActions):
        action = [action]

    def wrapped(fn):
        if not hasattr(fn, '__jsonapi_action__'):
            fn.__jsonapi_action__ = set()
            fn.__jsonapi_desc_for_attrs__ = set()
        fn.__jsonapi_desc_for_attrs__ |= set(names)
        fn.__jsonapi_action__ |= set(action)
        return fn

    return wrapped


def relationship_descriptor(action, *names):
    """
    Wrap a function for modification of a relationship.  This allows for
    specific handling for serialization and deserialization.

    :param action: The RelationshipActions that this descriptor performs
    :param names: A list of names of the relationships this references
    """
    if isinstance(action, RelationshipActions):
        action = [action]

    def wrapped(fn):
        if not hasattr(fn, '__jsonapi_action__'):
            fn.__jsonapi_action__ = set()
            fn.__jsonapi_desc_for_rels__ = set()
        fn.__jsonapi_desc_for_rels__ |= set(names)
        fn.__jsonapi_action__ |= set(action)
        return fn

    return wrapped


class PermissionTest(object):
    """ Authorize access to a model, resource, or specific field. """

    def __init__(self, permission, *names):
        """
        Decorates a function that returns a boolean representing if access is
        allowed.

        :param permission: The permission to check for
        :param names: The names to test for.  None represents the model.
        """
        if isinstance(permission, Permissions):
            self.permission = [permission]
        else:
            self.permission = permission
        self.names = names if len(names) > 0 else [None]

    def __call__(self, fn):
        """
        Decorate the function for later processing.

        :param fn: Function to decorate
        """
        if not hasattr(fn, '__jsonapi_chk_perm_for__'):
            fn.__jsonapi_check_permission__ = set()
            fn.__jsonapi_chk_perm_for__ = set()
        fn.__jsonapi_chk_perm_for__ |= set(self.names)
        fn.__jsonapi_check_permission__ |= set(self.permission)
        return fn

#: More consistent name for the decorators
permission_test = PermissionTest


class JSONAPIResponse(object):
    """ Wrapper for JSON API Responses. """

    def __init__(self):
        """ Default the status code and data. """
        self.status_code = 200
        self.data = {
            'jsonapi': {'version': '1.0'},
            'meta': {'sqlalchemy_jsonapi_version': '3.0.1'}
        }


def get_permission_test(model, field, permission, instance=None):
    """
    Fetch a permission test for a field and permission.

    :param model: The model or instance
    :param field: Name of the field or None for instance/model-wide
    :param permission: Permission to check for
    """
    return model.__jsonapi_permissions__\
        .get(field, {})\
        .get(permission, lambda x: True)


def check_permission(instance, field, permission):
    """
    Check a permission for a given instance or field.  Raises an error if
    denied.

    :param instance: The instance to check
    :param field: The field name to check or None for instance
    :param permission: The permission to check
    """
    if not get_permission_test(instance, field, permission)(instance):
        raise PermissionDeniedError(permission, instance, instance, field)


def get_attr_desc(instance, attribute, action):
    """
    Fetch the appropriate descriptor for the attribute.

    :param instance: Model instance
    :param attribute: Name of the attribute
    :param action: AttributeAction
    """
    descs = instance.__jsonapi_attribute_descriptors__.get(attribute, {})
    if action == AttributeActions.GET:
        check_permission(instance, attribute, Permissions.VIEW)
        return descs.get(action, lambda x: getattr(x, attribute))
    check_permission(instance, attribute, Permissions.EDIT)
    return descs.get(action, lambda x, v: setattr(x, attribute, v))


def get_rel_desc(instance, key, action):
    """
    Fetch the appropriate descriptor for the relationship.

    :param instance: Model instance
    :param key: Name of the relationship
    :param action: RelationshipAction
    """
    descs = instance.__jsonapi_rel_desc__.get(key, {})
    if action == RelationshipActions.GET:
        check_permission(instance, key, Permissions.VIEW)
        return descs.get(action, lambda x: getattr(x, key))
    elif action == RelationshipActions.APPEND:
        check_permission(instance, key, Permissions.CREATE)
        return descs.get(action, lambda x, v: getattr(x, key).append(v))
    elif action == RelationshipActions.SET:
        check_permission(instance, key, Permissions.EDIT)
        return descs.get(action, lambda x, v: setattr(x, key, v))
    else:
        check_permission(instance, key, Permissions.DELETE)
        return descs.get(action, lambda x, v: getattr(x, key).remove(v))


class JSONAPI(object):
    """ JSON API Serializer for SQLAlchemy ORM models. """

    def __init__(self, base):
        """
        Initialize the serializer.

        :param base: Declarative base instance
        """
        self.base = base
        self.models = {}
        for name, model in base._decl_class_registry.items():
            if name.startswith('_'):
                continue

            prepped_name = underscore(pluralize(name))
            api_type = getattr(model, '__jsonapi_type_override__', prepped_name)

            model.__jsonapi_attribute_descriptors__ = {}
            model.__jsonapi_rel_desc__ = {}
            model.__jsonapi_permissions__ = {}
            model.__jsonapi_type__ = api_type

            for prop_name, prop_value in iterate_attributes(model):
                if hasattr(prop_value, '__jsonapi_desc_for_attrs__'):
                    defaults = {'get': None, 'set': None}
                    descriptors = model.__jsonapi_attribute_descriptors__
                    for attribute in prop_value.__jsonapi_desc_for_attrs__:
                        descriptors.setdefault(attribute, defaults)
                        attr_desc = descriptors[attribute]
                        for action in prop_value.__jsonapi_action__:
                            attr_desc[action] = prop_value

                if hasattr(prop_value, '__jsonapi_desc_for_rels__'):
                    defaults = {
                        'get': None,
                        'set': None,
                        'append': None,
                        'remove': None
                    }
                    rels_desc = model.__jsonapi_rel_desc__
                    for relationship in prop_value.__jsonapi_desc_for_rels__:
                        rels_desc.setdefault(attribute, defaults)
                        rel_desc = rels_desc[relationship]
                        for action in prop_value.__jsonapi_action__:
                            rel_desc[action] = prop_value

                if hasattr(prop_value, '__jsonapi_check_permission__'):
                    defaults = {
                        'view': [],
                        'create': [],
                        'edit': [],
                        'delete': [],
                        'remove': [],
                        'append': []
                    }
                    perm_obj = model.__jsonapi_permissions__
                    for check_for in prop_value.__jsonapi_chk_perm_for__:
                        perm_obj.setdefault(check_for, defaults)
                        perm_idv = perm_obj[check_for]
                        check_perms = prop_value.__jsonapi_check_permission__
                        for check_perm in check_perms:
                            perm_idv[check_perm] = prop_value
            self.models[model.__jsonapi_type__] = model

    def _fetch_model(self, api_type):
        if api_type not in self.models.keys():
            raise ResourceTypeNotFoundError(api_type)
        return self.models[api_type]

    def _get_relationship(self, resource, rel_key, permission):
        if rel_key not in resource.__mapper__.relationships.keys():
            raise RelationshipNotFoundError(resource, resource, rel_key)
        relationship = resource.__mapper__.relationships[rel_key]
        check_permission(resource, relationship.key, permission)
        return relationship

    def _check_json_data(self, json_data):
        """
        Ensure that the request body is both a hash and has a data key.

        :param json_data: The json data provided with the request
        """
        if not isinstance(json_data, dict):
            raise BadRequestError('Request body should be a JSON hash')
        if 'data' not in json_data.keys():
            raise BadRequestError('Request should contain data key')

    def _fetch_resource(self, session, api_type, obj_id, permission):
        """
        Fetch a resource by type and id, also doing a permission check.

        :param session: SQLAlchemy session
        :param api_type: The type
        :param obj_id: ID for the resource
        :param permission: Permission to check
        """
        if api_type not in self.models.keys():
            raise ResourceTypeNotFoundError(api_type)
        obj = session.query(self.models[api_type]).get(obj_id)
        if obj is None:
            raise ResourceNotFoundError(self.models[api_type], obj_id)
        check_permission(obj, None, permission)
        return obj

    def _render_short_instance(self, instance):
        """
        For those very short versions of resources, we have this.

        :param instance: The instance to render
        """
        check_permission(instance, None, Permissions.VIEW)
        return {'type': instance.__jsonapi_type__, 'id': instance.id}

    def _render_full_resource(self, instance, include, fields):
        """
        Generate a representation of a full resource to match JSON API spec.

        :param instance: The instance to serialize
        :param include: Dictionary of relationships to include
        :param fields: Dictionary of fields to filter
        """
        api_type = instance.__jsonapi_type__
        orm_desc_keys = instance.__mapper__.all_orm_descriptors.keys()
        to_ret = {
            'id': instance.id,
            'type': api_type,
            'attributes': {},
            'relationships': {},
            'included': {}
        }
        attrs_to_ignore = {'__mapper__', 'id'}
        local_fields = fields.get(api_type, orm_desc_keys)

        for key, relationship in instance.__mapper__.relationships.items():
            attrs_to_ignore |= set([c.name for c in relationship.local_columns
                                    ]) | {key}

            try:
                desc = get_rel_desc(instance, key, RelationshipActions.GET)
            except PermissionDeniedError:
                continue
            related = desc(instance)

            if relationship.direction == MANYTOONE:
                if related is not None:
                    perm = get_permission_test(related, None, Permissions.VIEW)

                if related is None or not perm(related):
                    if key in local_fields:
                        to_ret['relationships'][key] = {'data': None}

                else:
                    if key in local_fields:
                        to_ret['relationships'][key] = {
                            'data': {
                                'id': related.id,
                                'type': related.__jsonapi_type__
                            }
                        }

                    if key in include.keys():
                        new_include = self._parse_include(include[key])
                        built = self._render_full_resource(related,
                                                           new_include, fields)
                        included = built.pop('included')
                        to_ret['included'].update(included)
                        to_ret['included'][(related.__jsonapi_type__, related.id)] = built

            else:
                if key in local_fields:
                    to_ret['relationships'][key] = {'data': []}

                for item in related:
                    try:
                        check_permission(item, None, Permissions.VIEW)
                    except PermissionDeniedError:
                        continue

                    if key in local_fields:
                        to_ret['relationships'][key]['data'].append({
                            'id': item.id,
                            'type': item.__jsonapi_type__
                        })

                    if key in include.keys():
                        new_include = self._parse_include(include[key])
                        built = self._render_full_resource(item, new_include,
                                                           fields)
                        included = built.pop('included')
                        to_ret['included'].update(included)
                        to_ret['included'][(item.__jsonapi_type__, item.id)] = built

        for key in set(orm_desc_keys) - attrs_to_ignore:
            try:
                desc = get_attr_desc(instance, key, AttributeActions.GET)
                if key in local_fields:
                    to_ret['attributes'][key] = desc(instance)
            except PermissionDeniedError:
                continue

        return to_ret

    def _check_instance_relationships_for_delete(self, instance):
        """
        Ensure we are authorized to delete this and all cascaded resources.

        :param instance: The instance to check the relationships of.
        """
        check_permission(instance, None, Permissions.DELETE)
        for rel_key, rel in instance.__mapper__.relationships.items():
            check_permission(instance, rel_key, Permissions.EDIT)

            if rel.cascade.delete:

                if rel.direction == MANYTOONE:
                    related = getattr(instance, rel_key)
                    self._check_instance_relationships_for_delete(related)
                else:
                    instances = getattr(instance, rel_key)
                    for to_check in instances:
                        self._check_instance_relationships_for_delete(to_check)

    def _parse_fields(self, query):
        """
        Parse the querystring args for fields.

        :param query: Dict of query args
        """
        field_args = {
            k: v
            for k, v in query.items() if k.startswith('fields[')
        }

        fields = {}

        for k, v in field_args.items():
            fields[k[7:-1]] = v

        return fields

    def _parse_include(self, include):
        """
        Parse the querystring args or parent includes for includes.

        :param include: Dict of query args or includes
        """
        ret = {}
        for item in include:
            if '.' in item:
                local, remote = item.split('.', 1)
            else:
                local = item
                remote = None

            ret.setdefault(local, [])
            if remote:
                ret[local].append(remote)

        return ret

    def _parse_page(self, query):
        """
        Parse the querystring args for pagination.

        :param query: Dict of query args
        """
        args = {k[5:-1]: v for k, v in query.items() if k.startswith('page[')}

        if {'number', 'size'} == set(args.keys()):
            if not args['number'].isdecimal() or not args['size'].isdecimal():
                raise BadRequestError('Page query parameters must be integers')

            number = int(args['number'])
            size = int(args['size'])
            start = number * size

            return start, start + size - 1

        if {'limit', 'offset'} == set(args.keys()):
            if not args['limit'].isdecimal() or not args['offset'].isdecimal():
                raise BadRequestError('Page query parameters must be integers')

            limit = int(args['limit'])
            offset = int(args['offset'])

            return offset, offset + limit - 1

        return 0, None

    def delete_relationship(self, session, data, api_type, obj_id, rel_key):
        """
        Delete a resource or multiple resources from a to-many relationship.

        :param session: SQLAlchemy session
        :param data: JSON data provided with the request
        :param api_type: Type of the resource
        :param obj_id: ID of the resource
        :param rel_key: Key of the relationship to fetch
        """
        model = self._fetch_model(api_type)
        resource = self._fetch_resource(session, api_type, obj_id,
                                        Permissions.EDIT)
        relationship = self._get_relationship(resource, rel_key,
                                              Permissions.DELETE)
        self._check_json_data(data)

        if not isinstance(data['data'], list):
            raise ValidationError('Provided data must be an array.')

        if relationship.direction == MANYTOONE:
            return ToManyExpectedError(model, resource, relationship)

        response = JSONAPIResponse()
        response.data = {'data': []}

        session.add(resource)

        remove = get_rel_desc(resource, relationship.key,
                              RelationshipActions.DELETE)
        reverse_side = relationship.back_populates

        for item in data['data']:
            item = self._fetch_resource(session, item['type'], item['id'],
                                        Permissions.EDIT)

            if reverse_side:
                reverse_rel = item.__mapper__.relationships[reverse_side]

                if reverse_rel.direction == MANYTOONE:
                    permission = Permissions.EDIT
                else:
                    permission = Permissions.DELETE

                check_permission(item, reverse_side, permission)

            remove(resource, item)

        session.commit()
        session.refresh(resource)

        get = get_rel_desc(resource, relationship.key, RelationshipActions.GET)

        for item in get(resource):
            response.data['data'].append(self._render_short_instance(item))

        return response

    def delete_resource(self, session, data, api_type, obj_id):
        """
        Delete a resource.

        :param session: SQLAlchemy session
        :param data: JSON data provided with the request
        :param api_type: Type of the resource
        :param obj_id: ID of the resource
        """
        resource = self._fetch_resource(session, api_type, obj_id,
                                        Permissions.VIEW)
        self._check_instance_relationships_for_delete(resource)

        session.delete(resource)
        session.commit()

        response = JSONAPIResponse()
        response.status_code = 204

        return response

    def get_collection(self, session, query, api_key):
        """
        Fetch a collection of resources of a specified type.

        :param session: SQLAlchemy session
        :param query: Dict of query args
        :param api_type: The type of the model
        """
        model = self._fetch_model(api_key)
        include = self._parse_include(query.get('include', '').split(','))
        fields = self._parse_fields(query)
        included = {}
        sorts = query.get('sort', '').split(',')
        order_by = []

        collection = session.query(model)

        for attr in sorts:
            if attr == '':
                break

            attr_name, is_asc = [attr[1:], False]\
                if attr[0] == '-'\
                else [attr, True]

            if attr_name not in model.__mapper__.all_orm_descriptors.keys()\
                    or not hasattr(model, attr_name)\
                    or attr_name in model.__mapper__.relationships.keys():
                return NotSortableError(model, attr_name)

            attr = getattr(model, attr_name)
            if not hasattr(attr, 'asc'):
                return NotSortableError(model, attr_name)

            check_permission(model, attr_name, Permissions.VIEW)

            order_by.append(attr.asc() if is_asc else attr.desc())

        if len(order_by) > 0:
            collection = collection.order_by(*order_by)

        pos = -1
        start, end = self._parse_page(query)

        response = JSONAPIResponse()
        response.data = {'data': []}

        for instance in collection:
            try:
                check_permission(instance, None, Permissions.VIEW)
            except PermissionDeniedError:
                continue

            pos += 1
            if end is not None and (pos < start or pos > end):
                continue

            built = self._render_full_resource(instance, include, fields)
            included.update(built.pop('included'))
            response.data['data'].append(built)

        response.data['included'] = list(included.values())
        return response

    def get_resource(self, session, query, api_type, obj_id):
        """
        Fetch a resource.

        :param session: SQLAlchemy session
        :param query: Dict of query args
        :param api_type: Type of the resource
        :param obj_id: ID of the resource
        """
        resource = self._fetch_resource(session, api_type, obj_id,
                                        Permissions.VIEW)
        include = self._parse_include(query.get('include', '').split(','))
        fields = self._parse_fields(query)

        response = JSONAPIResponse()

        built = self._render_full_resource(resource, include, fields)

        response.data['included'] = list(built.pop('included').values())
        response.data['data'] = built

        return response

    def get_related(self, session, query, api_type, obj_id, rel_key):
        """
        Fetch a collection of related resources.

        :param session: SQLAlchemy session
        :param query: Dict of query args
        :param api_type: Type of the resource
        :param obj_id: ID of the resource
        :param rel_key: Key of the relationship to fetch
        """
        resource = self._fetch_resource(session, api_type, obj_id,
                                        Permissions.VIEW)
        relationship = self._get_relationship(resource, rel_key,
                                              Permissions.VIEW)
        response = JSONAPIResponse()

        related = get_rel_desc(resource, relationship.key,
                               RelationshipActions.GET)(resource)

        if relationship.direction == MANYTOONE:
            try:
                response.data['data'] = self._render_full_resource(related,
                                                                   {}, {})
            except PermissionDeniedError:
                response.data['data'] = None
        else:
            response.data['data'] = []

            for item in related:
                try:
                    response.data['data'].append(
                        self._render_full_resource(item, {}, {}))
                except PermissionDeniedError:
                    continue

        return response

    def get_relationship(self, session, query, api_type, obj_id, rel_key):
        """
        Fetch a collection of related resource types and ids.

        :param session: SQLAlchemy session
        :param query: Dict of query args
        :param api_type: Type of the resource
        :param obj_id: ID of the resource
        :param rel_key: Key of the relationship to fetch
        """
        resource = self._fetch_resource(session, api_type, obj_id,
                                        Permissions.VIEW)
        relationship = self._get_relationship(resource, rel_key,
                                              Permissions.VIEW)
        response = JSONAPIResponse()

        related = get_rel_desc(resource, relationship.key,
                               RelationshipActions.GET)(resource)

        if relationship.direction == MANYTOONE:
            if related == None:
                response.data['data'] = None
            else:
                try:
                    response.data['data'] = self._render_short_instance(
                        related)
                except PermissionDeniedError:
                    response.data['data'] = None
        else:
            response.data['data'] = []
            for item in related:
                try:
                    response.data['data'].append(
                        self._render_short_instance(item))
                except PermissionDeniedError:
                    continue

        return response

    def patch_relationship(self, session, json_data, api_type, obj_id,
                           rel_key):
        """
        Replacement of relationship values.

        :param session: SQLAlchemy session
        :param json_data: Request JSON Data
        :param api_type: Type of the resource
        :param obj_id: ID of the resource
        :param rel_key: Key of the relationship to fetch
        """
        model = self._fetch_model(api_type)
        resource = self._fetch_resource(session, api_type, obj_id,
                                        Permissions.EDIT)
        relationship = self._get_relationship(resource, rel_key,
                                              Permissions.EDIT)
        self._check_json_data(json_data)

        session.add(resource)
        remote_side = relationship.back_populates
        try:
            if relationship.direction == MANYTOONE:
                if not isinstance(json_data['data'], dict)\
                        and json_data['data'] != None:
                    raise ValidationError('Provided data must be a hash.')

                related = getattr(resource, relationship.key)
                check_permission(related, None, Permissions.EDIT)
                check_permission(related, remote_side, Permissions.EDIT)

                setter = get_rel_desc(resource, relationship.key,
                                      RelationshipActions.SET)

                if json_data['data'] == None:
                    setter(resource, None)
                else:
                    to_relate = self._fetch_resource(
                        session, json_data['data']['type'],
                        json_data['data']['id'], Permissions.EDIT)
                    check_permission(to_relate, remote_side, Permissions.EDIT)
                    setter(resource, to_relate)
            else:
                if not isinstance(json_data['data'], list):
                    raise ValidationError('Provided data must be an array.')

                related = getattr(resource, relationship.key)

                remover = get_rel_desc(resource, relationship.key,
                                       RelationshipActions.DELETE)
                appender = get_rel_desc(resource, relationship.key,
                                        RelationshipActions.APPEND)
                for item in related:
                    check_permission(item, None, Permissions.EDIT)
                    remote = item.__mapper__.relationships[remote_side]
                    if remote.direction == MANYTOONE:
                        check_permission(item, remote_side, Permissions.EDIT)
                    else:
                        check_permission(item, remote_side, Permissions.DELETE)
                    remover(resource, item)

                for item in json_data['data']:
                    to_relate = self._fetch_resource(
                        session, item['type'], item['id'], Permissions.EDIT)
                    remote = to_relate.__mapper__.relationships[remote_side]

                    if remote.direction == MANYTOONE:
                        check_permission(to_relate, remote_side,
                                         Permissions.EDIT)
                    else:
                        check_permission(to_relate, remote_side,
                                         Permissions.CREATE)
                    appender(resource, to_relate)
            session.commit()
        except KeyError:
            raise ValidationError('Incompatible Type')

        return self.get_relationship(session, {}, model.__jsonapi_type__,
                                     resource.id, relationship.key)

    def patch_resource(self, session, json_data, api_type, obj_id):
        """
        Replacement of resource values.

        :param session: SQLAlchemy session
        :param json_data: Request JSON Data
        :param api_type: Type of the resource
        :param obj_id: ID of the resource
        :param rel_key: Key of the relationship to fetch
        """
        model = self._fetch_model(api_type)
        resource = self._fetch_resource(session, api_type, obj_id,
                                        Permissions.EDIT)
        self._check_json_data(json_data)
        orm_desc_keys = resource.__mapper__.all_orm_descriptors.keys()

        if not ({'type', 'id'} <= set(json_data['data'].keys())):
            raise BadRequestError('Missing type or id')

        if json_data['data']['id'] != str(resource.id):
            raise BadRequestError('IDs do not match')

        if json_data['data']['type'] != resource.__jsonapi_type__:
            raise BadRequestError('Type does not match')

        json_data['data'].setdefault('relationships', {})
        json_data['data'].setdefault('attributes', {})

        data_keys = set(json_data['data']['relationships'].keys())
        model_keys = set(resource.__mapper__.relationships.keys())
        if not data_keys <= model_keys:
            raise BadRequestError(
                '{} not relationships for {}.{}'.format(
                    ', '.join(list(data_keys - model_keys)),
                    model.__jsonapi_type__, resource.id))

        attrs_to_ignore = {'__mapper__', 'id'}

        session.add(resource)

        try:
            for key, relationship in resource.__mapper__.relationships.items():
                attrs_to_ignore |= set(relationship.local_columns) | {key}

                if key not in json_data['data']['relationships'].keys():
                    continue

                self.patch_relationship(
                    session, json_data['data']['relationships'][key],
                    model.__jsonapi_type__, resource.id, key)

            data_keys = set(json_data['data']['attributes'].keys())
            model_keys = set(orm_desc_keys) - attrs_to_ignore

            if not data_keys <= model_keys:
                raise BadRequestError(
                    '{} not attributes for {}.{}'.format(
                        ', '.join(list(data_keys - model_keys)),
                        model.__jsonapi_type__, resource.id))

            for key in data_keys & model_keys:
                setter = get_attr_desc(resource, key, AttributeActions.SET)
                setter(resource, json_data['data']['attributes'][key])
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise ValidationError(str(e.orig))
        except AssertionError as e:
            session.rollback()
            raise ValidationError(e.msg)
        except TypeError as e:
            session.rollback()
            raise ValidationError('Incompatible data type')
        return self.get_resource(
            session, {}, model.__jsonapi_type__, resource.id)

    def post_collection(self, session, data, api_type):
        """
        Create a new Resource.

        :param session: SQLAlchemy session
        :param data: Request JSON Data
        :param params: Keyword arguments
        """
        model = self._fetch_model(api_type)
        self._check_json_data(data)

        orm_desc_keys = model.__mapper__.all_orm_descriptors.keys()

        if 'type' not in data['data'].keys():
            raise MissingTypeError()

        if data['data']['type'] != model.__jsonapi_type__:
            raise InvalidTypeForEndpointError(
                model.__jsonapi_type__, data['data']['type'])

        resource = model()
        check_permission(resource, None, Permissions.CREATE)

        data['data'].setdefault('relationships', {})
        data['data'].setdefault('attributes', {})

        data_keys = set(data['data']['relationships'].keys())
        model_keys = set(resource.__mapper__.relationships.keys())
        if not data_keys <= model_keys:
            raise BadRequestError(
                '{} not relationships for {}'.format(
                    ', '.join(list(data_keys -
                                   model_keys)), model.__jsonapi_type__))

        attrs_to_ignore = {'__mapper__', 'id'}

        setters = []

        try:
            if 'id' in data['data'].keys():
                resource.id = data['data']['id']

            for key, relationship in resource.__mapper__.relationships.items():
                attrs_to_ignore |= set(relationship.local_columns) | {key}

                if 'relationships' not in data['data'].keys()\
                        or key not in data['data']['relationships'].keys():
                    continue

                data_rel = data['data']['relationships'][key]
                if 'data' not in data_rel.keys():
                    raise BadRequestError(
                        'Missing data key in relationship {}'.format(key))
                data_rel = data_rel['data']

                remote_side = relationship.back_populates
                if relationship.direction == MANYTOONE:
                    setter = get_rel_desc(resource, key,
                                          RelationshipActions.SET)
                    if data_rel is None:
                        setters.append([setter, None])
                    else:
                        if not isinstance(data_rel, dict):
                            raise BadRequestError(
                                '{} must be a hash'.format(key))
                        if not {'type', 'id'} == set(data_rel.keys()):
                            raise BadRequestError(
                                '{} must have type and id keys'.format(key))
                        to_relate = self._fetch_resource(
                            session, data_rel['type'], data_rel['id'],
                            Permissions.EDIT)
                        rem = to_relate.__mapper__.relationships[remote_side]
                        if rem.direction == MANYTOONE:
                            check_permission(to_relate, remote_side,
                                             Permissions.EDIT)
                        else:
                            check_permission(to_relate, remote_side,
                                             Permissions.CREATE)
                        setters.append([setter, to_relate])
                else:
                    setter = get_rel_desc(resource, key,
                                          RelationshipActions.APPEND)
                    if not isinstance(data_rel, list):
                        raise BadRequestError(
                            '{} must be an array'.format(key))
                    for item in data_rel:
                        if not {'type', 'id'} in set(item.keys()):
                            raise BadRequestError(
                                '{} must have type and id keys'.format(key))
                        to_relate = self._fetch_resource(session, item['type'],
                                                         item['id'],
                                                         Permissions.EDIT)
                        rem = to_relate.__mapper__.relationships[remote_side]
                        if rem.direction == MANYTOONE:
                            check_permission(to_relate, remote_side,
                                             Permissions.EDIT)
                        else:
                            check_permission(to_relate, remote_side,
                                             Permissions.CREATE)
                        setters.append([setter, to_relate])

            data_keys = set(data['data'].get('attributes', {}).keys())
            model_keys = set(orm_desc_keys) - attrs_to_ignore

            if not data_keys <= model_keys:
                raise BadRequestError(
                    '{} not attributes for {}'.format(
                        ', '.join(list(data_keys -
                                       model_keys)), model.__jsonapi_type__))

            for setter, value in setters:
                setter(resource, value)

            for key in data_keys & model_keys:
                setter = get_attr_desc(resource, key, AttributeActions.SET)
                setter(resource, data['data']['attributes'][key])
            session.add(resource)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise ValidationError(str(e.orig))
        except AssertionError as e:
            session.rollback()
            raise ValidationError(e.msg)
        except TypeError as e:
            session.rollback()
            raise ValidationError('Incompatible data type')
        session.refresh(resource)
        response = self.get_resource(
            session, {}, model.__jsonapi_type__, resource.id)
        response.status_code = 201
        return response

    def post_relationship(self, session, json_data, api_type, obj_id, rel_key):
        """
        Append to a relationship.

        :param session: SQLAlchemy session
        :param json_data: Request JSON Data
        :param api_type: Type of the resource
        :param obj_id: ID of the resource
        :param rel_key: Key of the relationship to fetch
        """
        model = self._fetch_model(api_type)
        resource = self._fetch_resource(session, api_type, obj_id,
                                        Permissions.EDIT)
        relationship = self._get_relationship(resource, rel_key,
                                              Permissions.CREATE)
        if relationship.direction == MANYTOONE:
            raise ValidationError('Cannot post to to-one relationship')

        if not isinstance(json_data['data'], list):
            raise ValidationError('/data must be an array')

        remote_side = relationship.back_populates

        try:
            for item in json_data['data']:
                setter = get_rel_desc(resource, relationship.key,
                                      RelationshipActions.APPEND)

                if not isinstance(json_data['data'], list):
                    raise BadRequestError(
                        '{} must be an array'.format(relationship.key))

                for item in json_data['data']:
                    if {'type', 'id'} != set(item.keys()):
                        raise BadRequestError(
                            '{} must have type and id keys'
                            .format(relationship.key))

                    to_relate = self._fetch_resource(
                        session, item['type'], item['id'], Permissions.EDIT)

                    rem = to_relate.__mapper__.relationships[remote_side]

                    if rem.direction == MANYTOONE:
                        check_permission(to_relate, remote_side,
                                         Permissions.EDIT)

                    else:
                        check_permission(to_relate, remote_side,
                                         Permissions.CREATE)

                    setter(resource, to_relate)

            session.add(resource)
            session.commit()

        except KeyError:
            raise ValidationError('Incompatible type provided')

        return self.get_relationship(
            session, {}, model.__jsonapi_type__, resource.id, relationship.key)
