"""Document processing exceptions"""

from .base import BaseServiceException


class DocumentProcessingError(BaseServiceException):
    """Raised when document processing fails"""
    pass


class UnsupportedFormatError(DocumentProcessingError):
    """Raised when document format is not supported"""
    pass


class FileTooLargeError(DocumentProcessingError):
    """Raised when uploaded file exceeds size limit"""
    pass


class MalwareDetectedError(DocumentProcessingError):
    """Raised when malware is detected in uploaded file"""
    pass


class TextExtractionError(DocumentProcessingError):
    """Raised when text extraction from document fails"""
    pass