"""
Custom exceptions for image processor name tool.
"""


class ImageProcessorNameError(Exception):
    """Base exception for all image processor name errors."""

    pass


class ConfigurationError(ImageProcessorNameError):
    """Raised when configuration is invalid or missing."""

    pass


class OllamaError(ImageProcessorNameError):
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


class ImageProcessingError(ImageProcessorNameError):
    """Base exception for image processing errors."""

    pass


class UnsupportedImageFormat(ImageProcessingError):
    """Raised when image format is not supported."""

    pass


class ImageCorrupted(ImageProcessingError):
    """Raised when image file is corrupted or unreadable."""

    pass


class FileSystemError(ImageProcessorNameError):
    """Base exception for file system errors."""

    pass


class FilePermissionError(FileSystemError):
    """Raised when file permissions are insufficient."""

    pass


class FileOperationError(FileSystemError):
    """Raised when file operations fail."""

    pass


class WatcherError(ImageProcessorNameError):
    """Base exception for file system watcher errors."""

    pass


class WatcherInitializationError(WatcherError):
    """Raised when file system watcher fails to initialize."""

    pass

