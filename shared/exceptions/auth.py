"""Authentication and authorization exceptions"""

from .base import BaseServiceException


class AuthenticationError(BaseServiceException):
    """Raised when authentication fails"""


class AuthorizationError(BaseServiceException):
    """Raised when user lacks required permissions"""


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired"""


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid"""


class UserNotFoundError(AuthenticationError):
    """Raised when user is not found during authentication"""
