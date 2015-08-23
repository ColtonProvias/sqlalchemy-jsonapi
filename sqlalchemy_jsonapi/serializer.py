"""
SQLAlchemy-JSONAPI
Serializer
Colton J. Provias
MIT License
"""


import inspect

from enum import Enum
from inflection import pluralize, underscore
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.interfaces import MANYTOONE, ONETOMANY
from sqlalchemy.util.langhelpers import iterate_attributes

from .errors import (BadRequestError, InvalidTypeForEndpointError,
                     MissingTypeError, NotAnAttributeError, NotSortableError,
                     PermissionDeniedError, RelatedResourceNotFoundError,
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
    REPLACE = 12
    DELETE = 13


class Permissions(Enum):
    """ The permissions that can be set. """

    VIEW = 100
    CREATE = 101
    EDIT = 102
    DELETE = 103


def attr_descriptor(action, *names):
    """
    Wrap a function that allows for getting or setting of an attribute.  This
    allows for specific handling of an attribute when it comes to serializing
    and deserializing.

    :param action: The AttributeActions that this descriptor performs
    :param names: A list of names of the attributes this references
    """

    def wrapped(fn):
        fn.__jsonapi_desc_for_attrs__ = names
        fn.__jsonapi_action__ = action
        return fn

    return wrapped


def relationship_descriptor(action, *names):
    """
    Wrap a function for modification of a relationship.  This allows for
    specific handling for serialization and deserialization.

    :param action: The RelationshipActions that this descriptor performs
    :param names: A list of names of the relationships this references
    """

    def wrapped(fn):
        fn.__jsonapi_desc_for_rels__ = names
        fn.__jsonapi_action__ = action
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
        self.permission = permission
        self.names = names if len(names) > 0 else [None]

    def __call__(self, fn):
        """
        Decorate the function for later processing.

        :param fn: Function to decorate
        """
        fn.__jsonapi_chk_perm_for__ = self.names
        fn.__jsonapi_check_permission__ = self.permission
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
            'meta': {'sqlalchemy_jsonapi_version': '1.0.0'}
        }


def get_permission_test(model, field, permission, instance=None):
    """
    Fetch a permission test for a field and permission.

    :param model: The model or instance
    :param field: Name of the field or None for instance/model-wide
    :param permission: Permission to check for
    """
    perm_field = model.__jsonapi_permissions__.get(field, {})
    return perm_field.get(permission, lambda x: True)


def check_permission(instance, field, permission):
    perm = get_permission_test(instance, field, permission)
    if not perm(instance):
        raise PermissionDeniedError(permission, instance, instance, field)


def inject_model(fn):
    """
    Take the provided type and replace it with the model it refers to.

    :param fn: Function to decorate
    """
    def wrapped(serializer, session, data, params):
        api_type = params.pop('api_type')
        if api_type not in serializer.models.keys():
            raise ResourceTypeNotFoundError(api_type)
        model = serializer.models[api_type]
        if len(inspect.getargspec(fn)[0]) == 4:
            return fn(serializer, session, data, model)
        else:
            return fn(serializer, session, data, model, params)

    return wrapped


def inject_resource(permission):
    """
    Take the provided resource ID and replace it with the actual instance.

    :param permission: Permission to check for
    """
    def wrapper(fn):
        def wrapped(serializer, session, data, model, params):
            obj_id = params.pop('obj_id')
            instance = session.query(model).get(obj_id)
            if not instance:
                raise ResourceNotFoundError(model, obj_id)
            check_permission(instance, None, permission)
            if len(inspect.getargspec(fn)[0]) == 5:
                return fn(serializer, session, data, model, instance)
            else:
                return fn(serializer, session, data, model, instance, params)

        return wrapped

    return wrapper


def inject_relationship(permission):
    """
    Replace the provided relationship key with the relationship itself.

    :param permission: Permission to check for
    """
    def wrapper(fn):
        def wrapped(serializer, session, data, model, instance, params):
            rel_key = params.pop('relationship')
            if rel_key not in model.__mapper__.relationships.keys():
                raise RelationshipNotFoundError(model, instance, rel_key)
            relationship = model.__mapper__.relationships[rel_key]
            check_permission(instance, relationship.key, permission)
            return fn(serializer, session, data, model, instance, relationship)

        return wrapped

    return wrapper


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
            api_type = getattr(model, '__jsonapi_type__', prepped_name)

            model.__jsonapi_attribute_descriptors__ = {}
            model.__jsonapi_rel_desc__ = {}
            model.__jsonapi_permissions__ = {}
            model.__jsonapi_type__ = api_type

            for prop_name, prop_value in iterate_attributes(model):
                if hasattr(prop_value, '__jsonapi_desc_for_attrs__'):
                    defaults = {
                        'get': None,
                        'set': None
                    }
                    descriptors = model.__jsonapi_attribute_descriptors__
                    for attribute in prop_value.__jsonapi_desc_for_attrs__:
                        descriptors.setdefault(attribute, defaults)
                        attr_desc = descriptors[attribute]
                        attr_desc[prop_value.__jsonapi_action__] = prop_value

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
                        rel_desc[prop_value.__jsonapi_action__] = prop_value

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
                        check_perm = prop_value.__jsonapi_check_permission__
                        perm_idv[check_perm] = prop_value
            self.models[model.__jsonapi_type__] = model

    def _check_json_data(self, json_data):
        if not isinstance(json_data, dict):
            raise BadRequestError('Request body should be a JSON hash')
        if 'data' not in json_data.keys():
            raise BadRequestError('Request should contain data key')

    def _fetch_resource(self, session, api_type, obj_id, permission):
        obj = session.query(self.models[api_type]).get(obj_id)
        check_permission(obj, None, permission)

    def _render_short_instance(self, instance):
        check_permission(instance, None, Permissions.VIEW)
        return {
            'type': instance.__jsonapi_type__,
            'id': instance.id
        }

    def _render_full_resource(self, instance, include, fields):
        to_ret = {
            'id': instance.id,
            'type': instance.__jsonapi_type__,
            'attributes': {},
            'relationships': {},
            'included': {}
        }
        attrs_to_ignore = {'__mapper__', 'id'}
        local_fields = fields.get(
            instance.__jsonapi_type__,
            instance.__mapper__.all_orm_descriptors.keys())
        for key, relationship in instance.__mapper__.relationships.items():
            attrs_to_ignore |= set(relationship.local_columns) | {key}
            try:
                check_permission(instance, key, Permissions.VIEW)
            except PermissionDeniedError:
                continue
            related = getattr(instance, key)
            if relationship.direction == MANYTOONE:
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
                        built = self._render_full_resource(
                            related, self._parse_include(include[key]), fields)
                        included = built.pop('included')
                        to_ret['included'].update(included)
                        to_ret['included'][(related.__jsonapi_type__,
                                            related.id)] = built
            else:
                if key in local_fields:
                    to_ret['relationships'][key] = {'data': []}
                for item in related:
                    try:
                        check_permission(item, None, Permissions.VIEW)
                    except PermissionDeniedError:
                        continue
                    if key in local_fields:
                        to_ret['relationships'][key]['data'].append(
                            {'id': item.id,
                             'type': item.__jsonapi_type__})
                    if key in include.keys():
                        built = self._render_full_resource(
                            item, self._parse_include(include[key]), fields)
                        included = built.pop('included')
                        to_ret['included'].update(included)
                        to_ret['included'][(item.__jsonapi_type__, item.id
                                            )] = built
        for key in set(
            instance.__mapper__.all_orm_descriptors.keys()) - attrs_to_ignore:
            try:
                check_permission(instance, key, Permissions.VIEW)
            except PermissionDeniedError:
                continue
            if key in local_fields:
                to_ret['attributes'][key] = getattr(instance, key)
        return to_ret

    def _check_instance_relationships_for_delete(self, instance):
        check_permission(instance, None, Permissions.DELTE)
        for rel_key, rel in instance.__mapper__.relationships.items():
            check_permission(instance, rel_key, Permissions.EDIT)
            if rel.cascade.delete:
                if rel.direction == MANYTOONE:
                    self._check_instance_relationships_for_delete(getattr(instance, rel_key))
                else:
                    instances = getattr(instance, rel_key)
                    for to_check in instances:
                        self._check_instance_relationships_for_delete(to_check)

    def _parse_fields(self, query):
        field_args = {
            k: v
            for k, v in query.items() if k.startswith('fields[')
        }
        fields = {}
        for k, v in field_args.items():
            fields[k[7:-1]] = v
        return fields

    def _parse_include(self, include):
        ret = {}
        for item in include:
            if '.' in item:
                local, remote = item.split('.', maxsplit=1)
            else:
                local = item
                remote = None
            ret.setdefault(local, [])
            if remote:
                ret[local].append(remote)
        return ret

    def _parse_page(self, query):
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

    @inject_model
    @inject_resource(Permissions.EDIT)
    @inject_relationship(Permissions.DELETE)
    def delete_relationship(self, session, data, model, resource,
                            relationship):
        """
        Delete requested items from a to-many relationship.

        :param session: SQLAlchemy session
        :param data: JSON Request body
        :param model: Model
        :param resource: Model instance
        :param relationship: The relationship
        """
        self._check_json_data(data)
        if relationship.direction == MANYTOONE:
            return ToManyExpectedError(model, resource, relationship)
        response = JSONAPIResponse()
        response.data = {'data': []}
        session.add(resource)
        rel = getattr(resource, relationship.key)
        reverse_side = relationship.back_populates
        for item in data['data']:
            item = self._fetch_resource(session, item['type'], item['id'], Permissions.EDIT)
            if reverse_side:
                reverse_rel = getattr(item, reverse_side)
                if reverse_rel.direction == MANYTOONE:
                    permission = Permissions.EDIT
                else:
                    permission = Permissions.DELETE
                check_permission(item, reverse_side, permission)
            rel.remove(item)
        session.commit()
        session.refresh(resource)
        for item in getattr(resource, relationship.key):
            response.data['data'].append(self._render_short_instance(item))
        return response

    @inject_model
    @inject_resource(Permissions.DELETE)
    def delete_resource(self, session, data, model, resource):
        self._check_instance_relationships_for_delete(resource)
        session.delete(resource)
        session.commit()
        response = JSONAPIResponse()
        response.status_code = 204
        return response

    @inject_model
    def get_collection(self, session, query, model):
        include = self._parse_include(query.get('include', '').split(','))
        fields = self._parse_fields(query)
        response = JSONAPIResponse()
        response.data = {'data': []}
        included = {}
        view_perm = get_permission_test(model, None, Permissions.VIEW)
        collection = session.query(model)
        sorts = query.get('sort', '').split(',')
        order_by = []
        for attr in sorts:
            if attr == '':
                break
            attr_name, is_asc = [attr[1:], False] if attr[0] == '-' else [attr,
                                                                          True]
            if attr_name not in model.__mapper__.all_orm_descriptors.keys(
            ) or not hasattr(
                    model,
                    attr_name) or attr_name in model.__mapper__.relationships.keys(
                    ):
                return NotSortableError(model, attr_name)
            attr = getattr(model, attr_name)
            if not hasattr(attr, 'asc'):
                return NotSortableError(model, attr_name)
            order_by.append(attr.asc() if is_asc else attr.desc())
        if len(order_by) > 0:
            collection = collection.order_by(*order_by)
        pos = -1
        start, end = self._parse_page(query)
        for instance in collection:
            if not view_perm(instance):
                continue
            pos += 1
            if end is not None and (pos < start or pos > end):
                continue
            built = self._render_full_resource(instance, include, fields)
            included.update(built.pop('included'))
            response.data['data'].append(built)
        response.data['included'] = list(included.values())
        return response

    @inject_model
    @inject_resource(Permissions.VIEW)
    def get_resource(self, session, query, model, resource):
        include = self._parse_include(query.get('include', '').split(','))
        fields = self._parse_fields(query)
        response = JSONAPIResponse()
        built = self._render_full_resource(resource, include, fields)
        response.data['included'] = list(built.pop('included').values())
        response.data['data'] = built
        return response

    @inject_model
    @inject_resource(Permissions.VIEW)
    @inject_relationship(Permissions.VIEW)
    def get_related(self, session, query, model, resource, relationship):
        response = JSONAPIResponse()
        if relationship.direction == MANYTOONE:
            related = getattr(resource, relationship.key)
            response.data[
                'data'
            ] = {'type': related.__jsonapi_type__,
                 'id': related.id}
        else:
            response.data['data'] = []
            for related in getattr(resource, relationship.key):
                response.data['data'].append(
                    {'type': related.__jsonapi_type__,
                     'id': related.id})
        return response

    @inject_model
    @inject_resource(Permissions.VIEW)
    @inject_relationship(Permissions.VIEW)
    def get_relationship(self, session, query, model, resource, relationship):
        response = JSONAPIResponse()
        if relationship.direction == MANYTOONE:
            related = getattr(resource, relationship.key)
            perm = get_permission_test(related, None, Permissions.VIEW)
            if not perm(related):
                return PermissionDeniedError()
            response.data = {
                'data': {
                    'id': related.id,
                    'type': related.__jsonapi_type__
                }
            }
        else:
            related = getattr(resource, relationship.key)
            response.data = {'data': []}
            for item in related:
                perm = get_permission_test(item, None, Permissions.VIEW)
                if not perm(item):
                    return PermissionDeniedError()
                response.data['data'].append({
                    'id': item.id,
                    'type': item.__jsonapi_type__
                })
        return response

    @inject_model
    @inject_resource(Permissions.EDIT)
    @inject_relationship(Permissions.EDIT)
    def patch_relationship(self, session, json_data, model, resource,
                           relationship):
        response = JSONAPIResponse()
        session.add(resource)
        try:
            if relationship.direction == MANYTOONE:
                if not isinstance(json_data['data'],
                                      dict) and json_data['data'] != None:
                    raise ValidationError('Provided data must be a hash.')
                if json_data['data'] == None:
                    setattr(resource, relationship.key, None)
                else:
                    to_relate = session.query(
                        self.models[json_data['data']['type']]).get(
                            json_data['data']['id'])
                    setattr(resource, relationship.key, to_relate)
            else:
                if not isinstance(json_data['data'], list):
                    raise ValidationError('Provided data must be an array.')
                rel = getattr(resource, relationship.key)
                for item in rel:
                    rel.remove(item)
                for item in json_data['data']:
                    to_relate = session.query(self.models[item['type']]).get(
                        item['id'])
                    if not to_relate:
                        raise ResourceNotFoundError(self.models[item['type']],
                                                    item['id'])
                    rel.append(to_relate)
            session.commit()
        except KeyError:
            raise ValidationError('Incompatible Type')
        if relationship.direction == MANYTOONE:
            related = getattr(resource, relationship.key)
            if related is None:
                response.data = {'data': None}
            else:
                response.data = {
                    'data': {
                        'id': related.id,
                        'type': related.__jsonapi_type__
                    }
                }
        else:
            related = getattr(resource, relationship.key)
            response.data = {'data': []}
            for item in related:
                response.data['data'].append({
                    'id': item.id,
                    'type': item.__jsonapi_type__
                })
        return response

    @inject_model
    @inject_resource(Permissions.EDIT)
    def patch_resource(self, session, json_data, model, resource):
        if 'data' not in json_data.keys() or not ({'type', 'id'} < set(
                json_data['data'].keys())):
            raise BadRequestError('Invalid request')
        try:
            if 'id' in json_data['data'].keys():
                resource.id = json_data['data']['id']

            if 'attributes' in json_data['data'].keys():
                for key, value in json_data['data']['attributes'].items():
                    if key not in model.__mapper__.all_orm_descriptors.keys():
                        raise NotAnAttributeError(model, key)
                    setattr(resource, key, value)

            if 'relationships' in json_data['data'].keys():
                for key, value in json_data['data']['relationships'].items():
                    if key not in resource.__mapper__.relationships.keys():
                        raise RelationshipNotFoundError(model, resource, key)
                    if isinstance(value['data'], list):
                        for related in value['data']:
                            related = session.query(
                                self.models[related['type']]).get(
                                    related['id'])
                            if not related:
                                raise RelatedResourceNotFoundError(
                                    related['type'], related['id'])
                            getattr(resource, key).append(related)
                    else:
                        related = session.query(
                            self.models[value['data']['type']]).get(
                                value['data']['id'])
                        if not related:
                            raise RelatedResourceNotFoundError(
                                value['data']['type'], value['data']['id'])
                        setattr(resource, key, related)

            session.add(resource)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise ValidationError(str(e.orig))
        except AssertionError as e:
            raise ValidationError(e.msg)
        session.refresh(resource)
        response = JSONAPIResponse()
        built = self._render_full_resource(resource, {}, {})
        built.pop('included')
        response.data['data'] = built
        return response

    @inject_model
    def post_collection(self, session, data, model):
        if 'data' not in data.keys():
            raise BadRequestError('Must have a top-level data key')
        if 'type' not in data['data'].keys():
            raise MissingTypeError()
        if data['data']['type'] != model.__jsonapi_type__:
            raise InvalidTypeForEndpointError(model.__jsonapi_type__,
                                              data['data']['type'])
        perm = get_permission_test(model, None, Permissions.CREATE)
        if not perm(model):
            return PermissionDeniedError(Permissions.CREATE, model)
        instance = model()
        try:
            if 'id' in data['data'].keys():
                instance.id = data['data']['id']

            if 'attributes' in data['data'].keys():
                for key, value in data['data']['attributes'].items():
                    if key not in model.__mapper__.all_orm_descriptors.keys():
                        raise NotAnAttributeError(model, key)
                    setattr(instance, key, value)

            if 'relationships' in data['data'].keys():
                for key, value in data['data']['relationships'].items():
                    if isinstance(value['data'], list):
                        for related in value['data']:
                            related = session.query(
                                self.models[related['type']]).get(
                                    related['id'])
                            getattr(instance, key).append(related)
                    else:
                        related = session.query(
                            self.models[value['data']['type']]).get(
                                value['data']['id'])
                        setattr(instance, key, related)

            session.add(instance)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise ValidationError(str(e.orig))
        except AssertionError as e:
            raise ValidationError(e.msg)
        response = JSONAPIResponse()
        built = self._render_full_resource(instance, {}, {})
        built.pop('included')
        response.data['data'] = built
        response.status_code = 201
        return response

    @inject_model
    @inject_resource(Permissions.EDIT)
    @inject_relationship(Permissions.CREATE)
    def post_relationship(self, session, json_data, model, resource,
                          relationship):
        if relationship.direction == MANYTOONE:
            raise ValidationError('Cannot post to many-to-many relationship')
        if not isinstance(json_data['data'], list):
            raise ValidationError('/data must be an array')
        response = JSONAPIResponse()
        rel = getattr(resource, relationship.key)
        session.add(resource)
        try:
            for item in json_data['data']:
                to_add = session.query(self.models[item['type']]).get(
                    item['id'])
                rel.append(to_add)
        except KeyError:
            raise ValidationError('Incompatible type provided')
        session.commit()
        session.refresh(resource)
        related = getattr(resource, relationship.key)
        response.data = {'data': []}
        for item in related:
            response.data['data'].append({
                'id': item.id,
                'type': item.__jsonapi_type__
            })
        return response
