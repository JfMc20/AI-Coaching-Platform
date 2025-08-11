"""Authentication and authorization exceptions"""

from .base import BaseServiceException


class AuthenticationError(BaseServiceException):
    """Raised when authentication fails"""
    pass


class AuthorizationError(BaseServiceException):
    """Raised when user lacks required permissions"""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired"""
    pass


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid"""
    pass


class UserNotFoundError(AuthenticationError):
    """Raised when user is not found during authentication"""
    pass