class BaseError(Exception):
    pass


class BadRequestError(BaseError):
    pass


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
    pass


class IDAlreadyExistsError(BaseError):

    pass


class InvalidTypeForEndpointError(BaseError):

    pass


class MissingTypeError(BaseError):

    pass


class ValidationError(BaseError):

    pass


class ResourceNotFoundError(BaseError):

    pass


class RelationshipNotFoundError(BaseError):

    pass


class ToManyExpectedError(BaseError):
    pass
