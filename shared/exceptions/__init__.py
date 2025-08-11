"""Shared exception classes for all services"""

from .base import BaseServiceException, ValidationError, NotFoundError, UnauthorizedError
from .auth import AuthenticationError, AuthorizationError, TokenExpiredError
from .documents import DocumentProcessingError, UnsupportedFormatError
from .widgets import WidgetConfigError, DomainNotAllowedError

__all__ = [
    "BaseServiceException",
    "ValidationError", 
    "NotFoundError",
    "UnauthorizedError",
    "AuthenticationError",
    "AuthorizationError",
    "TokenExpiredError",
    "DocumentProcessingError",
    "UnsupportedFormatError",
    "WidgetConfigError",
    "DomainNotAllowedError",
]