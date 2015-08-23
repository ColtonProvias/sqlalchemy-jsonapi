import inspect

from enum import Enum
from inflection import pluralize, underscore
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.interfaces import MANYTOONE
from sqlalchemy.util.langhelpers import iterate_attributes

from .errors import (BadRequestError, InvalidTypeForEndpointError,
                     MissingTypeError, NotAnAttributeError, NotSortableError,
                     PermissionDeniedError, RelatedResourceNotFoundError,
                     RelationshipNotFoundError, ResourceNotFoundError,
                     ResourceTypeNotFoundError, ToManyExpectedError,
                     ValidationError)


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
        self.data = {
            'jsonapi': {'version': '1.0'},
            'meta': {'sqlalchemy_jsonapi_version': '1.0.0'}
        }


def get_permission_test(model, field, permission):
    return model.__jsonapi_permissions__.get(field, {}).get(permission,
                                                            lambda x: True)


def inject_model(fn):
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
    def wrapper(fn):
        def wrapped(serializer, session, data, model, params):
            obj_id = params.pop('obj_id')
            instance = session.query(model).get(obj_id)
            if not instance:
                raise ResourceNotFoundError(model, obj_id)
            test = get_permission_test(model, None, permission)
            if not test(instance):
                raise PermissionDeniedError(permission, instance)
            if len(inspect.getargspec(fn)[0]) == 5:
                return fn(serializer, session, data, model, instance)
            else:
                return fn(serializer, session, data, model, instance, params)

        return wrapped

    return wrapper


def inject_relationship(permission):
    def wrapper(fn):
        def wrapped(serializer, session, data, model, instance, params):
            rel_key = params.pop('relationship')
            if rel_key not in model.__mapper__.relationships.keys():
                raise RelationshipNotFoundError(model, instance, rel_key)
            relationship = model.__mapper__.relationships[rel_key]
            perm = get_permission_test(model, rel_key, permission)
            if not perm(instance):
                raise PermissionDeniedError(permission, relationship)
            return fn(serializer, session, data, model, instance, relationship)

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
    def delete_relationship(self, session, json_data, model, resource,
                            relationship):
        if relationship.direction == MANYTOONE:
            return ToManyExpectedError(model, resource, relationship)
        response = JSONAPIResponse()
        response.data = {'data': []}
        session.add(resource)
        rel = getattr(resource, relationship.key)
        for item in json_data['data']:
            item = session.query(self.models[item['type']]).get(item['id'])
            rel.remove(item)
        session.commit()
        session.refresh(resource)
        for item in getattr(resource, relationship.key):
            response.data['data'].append(
                {'type': item.__jsonapi_type__,
                 'id': item.id})
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
    def delete_resource(self, session, data, model, resource):
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

    def _build_full_resource(self, instance, include, fields):
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
            if not get_permission_test(instance, key,
                                           Permissions.VIEW)(instance):
                continue
            related = getattr(instance, key)
            if relationship.direction == MANYTOONE:
                if related == None or not get_permission_test(
                        related, None, Permissions.VIEW)(related):
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
            built = self._build_full_resource(instance, include, fields)
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
        built = self._build_full_resource(resource, include, fields)
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
        built = self._build_full_resource(resource, {}, {})
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
        built = self._build_full_resource(instance, {}, {})
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
