from uuid import uuid4


class BaseError(Exception):
    @property
    def data(self):
        return {
            'errors': [{
                'id': uuid4(),
                'code': self.code,
                'status': self.status_code,
                'title': self.title,
                'detail': self.detail
            }]
        }


class BadRequestError(BaseError):
    title = 'Bad Request'
    status_code = 400
    code = 'bad_request'

    def __init__(self, detail):
        self.detail = detail


class NotAnAttributeError(BaseError):
    status_code = 409
    code = 'not_an_attribute'
    title = 'Not An Attribute'

    def __init__(self, model, key):
        tmpl = '{} has no attribute {}'
        self.detail = tmpl.format(model.__jsonapi_type__, key)


class NotSortableError(BaseError):
    title = 'Not Sortable'
    status_code = 409
    code = 'not_sortable'

    def __init__(self, model, attr_name):
        tmpl = 'The requested field {} on type {} is not a sortable field.'
        self.detail = tmpl.format(model.__jsonapi_type__, attr_name)


class PermissionDeniedError(BaseError):
    status_code = 403
    code = 'permission_denied'
    title = 'Permission Denied'

    def __init__(self, permission, model, instance=None, field=None):
        tmpl = '{} denied on {}'
        self.detail = tmpl.format(permission.name, model.__jsonapi_type__)
        if instance is not None:
            self.detail += '.' + str(instance.id)
        if field is not None:
            self.detail += '.' + field


class InvalidTypeForEndpointError(BaseError):
    status_code = 409
    code = 'invalid_type_for_endpoint'
    title = 'Invalid Type For Endpoint'

    def __init__(self, expected, got):
        self.detail = 'Expected {}, got {}'.format(expected, got)


class MissingTypeError(BaseError):
    status_code = 409
    code = 'missing_type'
    title = 'Missing Type'
    detail = 'Missing /data/type key in request body'


class MissingContentTypeError(BaseError):
    status_code = 409
    code = 'invalid_conent_type'
    title = 'Missing/Invalid Content-Type Header'
    detail = 'Content-Type must be application/vnd.api+json'


class ValidationError(BaseError):
    status_code = 409
    code = 'validation_error'
    title = 'Validation Failed'

    def __init__(self, detail):
        self.detail = detail


class ResourceNotFoundError(BaseError):
    status_code = 404
    code = 'resource_not_found'
    title = 'Resource Not Found'

    def __init__(self, model, instance):
        self.detail = '{}.{} not found'.format(model, instance)


class RelatedResourceNotFoundError(BaseError):
    status_code = 404
    code = 'related_resource_not_found'
    title = 'Related Resource Not Found'

    def __init__(self, api_type, obj_id):
        tmpl = 'Related resource {}.{} not found'
        self.detail = tmpl.format(api_type, obj_id)


class RelationshipNotFoundError(BaseError):
    status_code = 404
    code = 'relationship_not_found'
    title = 'Relationsip Not Found'

    def __init__(self, model, instance, key):
        self.detail = '{}.{}.{} not found'.format(model, instance, key)


class ToManyExpectedError(BaseError):
    status_code = 409
    code = 'to_many_expected'
    title = 'To-Many Expected'

    def __init__(self, model, instance, relationship):
        self.detail = '{}.{}.{} is not a to-many relationship'.format(
            model.__jsonapi_type__, instance.id, relationship.key)


class ResourceTypeNotFoundError(BaseError):
    title = 'Resource Type Not Found'
    status_code = 404
    code = 'resource_type_not_found'

    def __init__(self, api_type):
        tmpl = 'This backend has not been configured to handle resources of '\
            'type {}.'
        self.detail = tmpl.format(api_type)
