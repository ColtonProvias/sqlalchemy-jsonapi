from enum import Enum
from inflection import pluralize, underscore
from sqlalchemy.orm.interfaces import MANYTOONE
from sqlalchemy.util.langhelpers import iterate_attributes

from .errors import (PermissionDeniedError, RelationshipNotFoundError,
                     ResourceNotFoundError, ResourceTypeNotFoundError,
                     ToManyExpectedError)


class AttributeActions(Enum):
    GET = 0
    SET = 1


class RelationshipActions(Enum):
    GET = 10
    APPEND = 11
    REPLACE = 12
    DELETE = 13


class Permissions(Enum):
    VIEW = 100
    CREATE = 101
    EDIT = 102
    DELETE = 103


def attr_descriptor(action, *names):
    def wrapped(fn):
        fn.__jsonapi_descriptor_for_attributes__ = names
        fn.__jsonapi_action__ = action
        return fn

    return wrapped


def relationship_descriptor(action, *names):
    def wrapped(fn):
        fn.__jsonapi_descriptor_for_relationships__ = names
        fn.__jsonapi_action__ = action
        return fn

    return wrapped


class PermissionTest(object):
    def __init__(self, permission, *names):
        self.permission = permission
        self.names = names if len(names) > 0 else [None]

    def __call__(self, fn):
        fn.__jsonapi_check_permission_for__ = self.names
        fn.__jsonapi_check_permission__ = self.permission
        return fn


permission_test = PermissionTest


class JSONAPIResponse(object):
    def __init__(self):
        self.status_code = 200
        self.data = {}


def get_permission_test(model, field, permission):
    return model.__jsonapi_permissions__.get(field, {}).get(permission,
                                                            lambda x: True)


def inject_model(fn):
    def wrapped(*args, **kwargs):
        if args[2] not in args[0].models.keys():
            return ResourceTypeNotFoundError()
        args = list(args)
        args[2] = args[0].models[args[2]]
        return fn(*args, **kwargs)

    return wrapped


def inject_resource(permission):
    def wrapper(fn):
        def wrapped(*args, **kwargs):
            instance = args[1].query(args[2]).get(args[3])
            if not instance:
                return ResourceNotFoundError()
            test = get_permission_test(args[2], None, permission)
            if not test(instance):
                return PermissionDeniedError()
            args = list(args)
            args[3] = instance
            return fn(*args, **kwargs)

        return wrapped

    return wrapper


def inject_relationship(permission):
    def wrapper(fn):
        def wrapped(*args, **kwargs):
            if args[4] not in args[2].__mapper__.relationships.keys():
                return RelationshipNotFoundError()
            relationship = args[2].__mapper__.relationships[args[4]]
            perm = get_permission_test(args[2], args[4], permission)
            if not perm(args[3]):
                return PermissionDeniedError()
            args = list(args)
            args[4] = relationship
            return fn(*args, **kwargs)

        return wrapped

    return wrapper


class JSONAPI(object):
    def __init__(self, base):
        self.base = base
        self.models = {}
        for name, model in base._decl_class_registry.items():
            if name.startswith('_'):
                continue
            model.__jsonapi_attribute_descriptors__ = {}
            model.__jsonapi_relationship_descriptors__ = {}
            model.__jsonapi_permissions__ = {}
            model.__jsonapi_type__ = getattr(model, '__jsonapi_type__',
                                             underscore(
                                                 pluralize(name)))
            for prop_name, prop_value in iterate_attributes(model):
                if hasattr(prop_value,
                           '__jsonapi_descriptor_for_attributes__'):
                    for attribute in prop_value.__jsonapi_descriptor_for_attributes__:
                        model.__jsonapi_attribute_descriptors__.setdefault(
                            attribute, {'get': None,
                                        'set': None})
                        model.__jsonapi_attribute_descriptors__[attribute][
                            prop_value.__jsonapi_action__
                        ] = prop_value
                if hasattr(prop_value,
                           '__jsonapi_descriptor_for_relationships__'):
                    for relationship in prop_value.__jsonapi_descriptor_for_relationships__:
                        model.__jsonapi_relationship_descriptors__.setdefault(
                            attribute, {
                                'get': None,
                                'set': None,
                                'append': None,
                                'remove': None
                            })
                        model.__jsonapi_relationship_descriptors__[relationship][
                            prop_value.__jsonapi_action__
                        ] = prop_value
                if hasattr(prop_value, '__jsonapi_check_permission__'):
                    for check_for in prop_value.__jsonapi_check_permission_for__:
                        model.__jsonapi_permissions__.setdefault(check_for, {
                            'view': [],
                            'create': [],
                            'edit': [],
                            'delete': [],
                            'remove': [],
                            'append': []
                        })
                        model.__jsonapi_permissions__[check_for][
                            prop_value.__jsonapi_check_permission__
                        ] = prop_value
            self.models[model.__jsonapi_type__] = model

    @inject_model
    @inject_resource(Permissions.EDIT)
    @inject_relationship(Permissions.DELETE)
    def delete_relationship(self, session, model, resource, relationship,
                            json_data):
        if relationship.direction == MANYTOONE:
            return ToManyExpectedError()
        response = JSONAPIResponse()
        return response

    def _check_instance_relationships_for_delete(self, instance):
        perm = get_permission_test(instance, None, Permissions.DELETE)
        if not perm(instance):
            raise PermissionDeniedError()
        for relationship_key, relationship in instance.__mapper__.relationships.items(
        ):
            perm = get_permission_test(instance, relationship_key,
                                       Permissions.EDIT)
            if not perm(instance):
                raise PermissionDeniedError()
            if relationship.cascade.delete:
                if relationship.direction == MANYTOONE:
                    self._check_instance_relationships_for_delete(getattr(
                        instance, relationship_key))
                else:
                    instances = getattr(instance, relationship_key)
                    for to_check in instances:
                        self._check_instance_relationships_for_delete(to_check)

    @inject_model
    @inject_resource(Permissions.DELETE)
    def delete_resource(self, session, model, resource):
        try:
            self._check_instance_relationships_for_delete(resource)
        except PermissionDeniedError as e:
            return e
        session.delete(resource)
        session.commit()
        response = JSONAPIResponse()
        response.status_code = 204
        return response

    def _parse_fields(self, query):
        field_args = {k: v for k, v in query.items() if k.startswith('fields[')}
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

    def _build_full_resource(self, instance, include, fields):
        to_ret = {
            'id': instance.id,
            'type': instance.__jsonapi_type__,
            'attributes': {},
            'relationships': {},
            'included': {}
        }
        attrs_to_ignore = {'__mapper__', 'id'}
        local_fields = fields.get(instance.__jsonapi_type__, instance.__mapper__.all_orm_descriptors.keys())
        for key, relationship in instance.__mapper__.relationships.items():
            attrs_to_ignore |= set(relationship.local_columns) | {key}
            if not get_permission_test(instance, key,
                                           Permissions.VIEW)(instance):
                continue
            related = getattr(instance, key)
            if relationship.direction == MANYTOONE:
                if not get_permission_test(
                        related, None,
                        Permissions.VIEW)(related) or related == None:
                    if key in local_fields:
                        to_ret['relationships'][key] = {'data': None}
                else:
                    if key in local_fields:
                        to_ret['relationships'][key] = {
                            'data':
                            {'id': related.id,
                             'type': related.__jsonapi_type__}
                        }
                    if key in include.keys():
                        built = self._build_full_resource(
                            related, self._parse_include(include[key]), fields)
                        included = built.pop('included')
                        to_ret['included'].update(included)
                        to_ret['included'][(related.__jsonapi_type__,
                                            related.id)] = built
            else:
                if key in local_fields:
                    to_ret['relationships'][key] = {'data': []}
                for item in related:
                    if not get_permission_test(item, None,
                                                   Permissions.VIEW)(item):
                        continue
                    if key in local_fields:
                        to_ret['relationships'][key]['data'].append(
                            {'id': item.id,
                             'type': item.__jsonapi_type__})
                    if key in include.keys():
                        built = self._build_full_resource(
                            item, self._parse_include(include[key]), fields)
                        included = built.pop('included')
                        to_ret['included'].update(included)
                        to_ret['included'][(item.__jsonapi_type__, item.id
                                            )] = built
        for key in set(
            instance.__mapper__.all_orm_descriptors.keys()) - attrs_to_ignore:
            if not get_permission_test(instance, key,
                                           Permissions.VIEW)(instance):
                continue
            if key in local_fields:
                to_ret['attributes'][key] = getattr(instance, key)
        return to_ret

    @inject_model
    def get_collection(self, session, model, query):
        include = self._parse_include(query.get('include', '').split(','))
        fields = self._parse_fields(query)
        response = JSONAPIResponse()
        response.data = {'data': []}
        included = {}
        view_perm = get_permission_test(model, None, Permissions.VIEW)
        collection = session.query(model)
        for instance in collection:
            if not view_perm(instance):
                continue
            built = self._build_full_resource(instance, include, fields)
            included.update(built.pop('included'))
            response.data['data'].append(built)
        response.data['included'] = list(included.values())
        return response

    @inject_model
    @inject_resource(Permissions.VIEW)
    def get_resource(self, session, model, resource, query):
        include = self._parse_include(query.get('include', '').split(','))
        fields = self._parse_fields(query)
        response = JSONAPIResponse()
        built = self._build_full_resource(resource, include, fields)
        response.data['included'] = list(built.pop('built').values())
        response.data['data'] = built
        return response

    @inject_model
    @inject_resource(Permissions.VIEW)
    @inject_relationship(Permissions.VIEW)
    def get_related(self, session, model, resource, relationship_key, query):
        response = JSONAPIResponse()
        return response

    @inject_model
    @inject_resource(Permissions.VIEW)
    @inject_relationship(Permissions.VIEW)
    def get_relationship(self, session, model, resource, relationship, query):
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
    def patch_relationship(self, session, model, resource, relationship_key,
                           json_data):
        response = JSONAPIResponse()
        return response

    @inject_model
    @inject_resource(Permissions.EDIT)
    def patch_resource(self, session, model, resource, json_data):
        response = JSONAPIResponse()
        return response

    @inject_model
    def post_collection(self, session, model, query_string):
        perm = get_permission_test(model, None, Permissions.CREATE)
        if not perm(model):
            return PermissionDeniedError()
        response = JSONAPIResponse()
        response.status_code = 201
        return response

    @inject_model
    @inject_resource(Permissions.EDIT)
    @inject_relationship(Permissions.CREATE)
    def post_relationship(self, session, model, resource, relationship_key,
                          json_data):
        response = JSONAPIResponse()
        return response
