"""Widget configuration exceptions"""

from .base import BaseServiceException


class WidgetConfigError(BaseServiceException):
    """Raised when widget configuration is invalid"""


class DomainNotAllowedError(WidgetConfigError):
    """Raised when request comes from non-allowed domain"""


class WidgetNotFoundError(WidgetConfigError):
    """Raised when widget is not found"""


class WidgetInactiveError(WidgetConfigError):
    """Raised when trying to use an inactive widget"""
