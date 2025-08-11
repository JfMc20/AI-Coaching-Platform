"""Base exception classes"""

from typing import Optional, Dict, Any


class BaseServiceException(Exception):
    """Base exception for all service errors"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseServiceException):
    """Raised when data validation fails"""
    pass


class NotFoundError(BaseServiceException):
    """Raised when a requested resource is not found"""
    pass


class UnauthorizedError(BaseServiceException):
    """Raised when user is not authorized to perform an action"""
    pass


class ConfigurationError(BaseServiceException):
    """Raised when there's a configuration error"""
    pass


class ExternalServiceError(BaseServiceException):
    """Raised when an external service fails"""
    pass