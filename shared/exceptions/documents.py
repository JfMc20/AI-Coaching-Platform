"""Document processing exceptions"""

from .base import BaseServiceException


class DocumentProcessingError(BaseServiceException):
    """Raised when document processing fails"""


class UnsupportedFormatError(DocumentProcessingError):
    """Raised when document format is not supported"""


class FileTooLargeError(DocumentProcessingError):
    """Raised when uploaded file exceeds size limit"""


class MalwareDetectedError(DocumentProcessingError):
    """Raised when malware is detected in uploaded file"""


class TextExtractionError(DocumentProcessingError):
    """Raised when text extraction from document fails"""
