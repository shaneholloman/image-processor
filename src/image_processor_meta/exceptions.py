"""
Custom exceptions for image meta processor.
"""


class ImageProcessorError(Exception):
    """Base exception for all image processor errors."""

    pass


class ConfigurationError(ImageProcessorError):
    """Raised when configuration is invalid or missing."""

    pass


class DatabaseError(ImageProcessorError):
    """Base exception for database-related errors."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


class DatabaseOperationError(DatabaseError):
    """Raised when database operation fails."""

    pass


class ImageProcessingError(ImageProcessorError):
    """Base exception for image processing errors."""

    pass


class UnsupportedImageFormat(ImageProcessingError):
    """Raised when image format is not supported."""

    pass


class ImageCorrupted(ImageProcessingError):
    """Raised when image file is corrupted or unreadable."""

    pass


class MetadataError(ImageProcessorError):
    """Base exception for metadata-related errors."""

    pass


class MetadataReadError(MetadataError):
    """Raised when reading metadata fails."""

    pass


class MetadataWriteError(MetadataError):
    """Raised when writing metadata fails."""

    pass


class OllamaError(ImageProcessorError):
    """Base exception for Ollama API errors."""

    pass


class OllamaConnectionError(OllamaError):
    """Raised when connection to Ollama fails."""

    pass


class OllamaTimeoutError(OllamaError):
    """Raised when Ollama request times out."""

    pass


class OllamaResponseError(OllamaError):
    """Raised when Ollama returns invalid response."""

    pass


class FileSystemError(ImageProcessorError):
    """Base exception for file system errors."""

    pass


class FilePermissionError(FileSystemError):
    """Raised when file permissions are insufficient."""

    pass


class FileNotFoundError(FileSystemError):
    """Raised when required file is not found."""

    pass
