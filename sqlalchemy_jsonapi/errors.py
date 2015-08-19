from uuid import uuid4


class BaseError(Exception):
    @property
    def data(self):
        return {
            'errors': [{
                'id': uuid4(),
                'code': self.code,
                'status': self.status_code
            }]
        }


class BadRequestError(BaseError):
    status_code = 400
    code = 'bad_request'


class NotAFieldError(BaseError):
    pass


class NotARelationshipError(BaseError):
    pass


class NotAnAttributeError(BaseError):
    pass


class NotSortableError(BaseError):
    pass


class OutOfBoundsError(BaseError):
    pass


class PermissionDeniedError(BaseError):
    status_code = 403
    code = 'permission_denied'


class IDAlreadyExistsError(BaseError):

    pass


class InvalidTypeForEndpointError(BaseError):
    status_code = 400
    code = 'invalid_type_for_endpoint'


class MissingTypeError(BaseError):

    pass


class ValidationError(BaseError):

    pass


class ResourceNotFoundError(BaseError):
    status_code = 404
    code = 'resource_not_found'


class RelationshipNotFoundError(BaseError):
    status_code = 404
    code = 'relationship_not_found'


class ToManyExpectedError(BaseError):
    status_code = 409
    code = 'to_many_expected'


class ResourceTypeNotFoundError(BaseError):
    status_code = 404
    code = 'resource_type_not_found'
