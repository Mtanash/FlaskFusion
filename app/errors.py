class BaseError(Exception):
    """Base class for custom exceptions."""

    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ValidationError(BaseError):
    """Exception raised for validation errors."""

    def __init__(self, message):
        super().__init__(message, 400)


class NotFoundError(BaseError):
    """Exception raised when an item is not found."""

    def __init__(self, message):
        super().__init__(message, 404)


class DatabaseError(BaseError):
    """Exception raised for database-related errors."""

    def __init__(self, message):
        super().__init__(message, 500)
