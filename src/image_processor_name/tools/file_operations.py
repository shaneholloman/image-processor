"""
Safe file operation utilities for image processing.
"""

import gc
import shutil
import time
from pathlib import Path

from PIL import Image

from .config_manager import config
from .log_manager import get_logger

logger = get_logger(__name__)


# File operation exceptions
class FileOperationError(Exception):
    """Raised when file operations fail."""
    pass


class FilePermissionError(Exception):
    """Raised when file permissions are insufficient."""
    pass


class UnsupportedImageFormat(Exception):
    """Raised when image format is not supported."""
    pass


class ImageCorrupted(Exception):
    """Raised when image file is corrupted or unreadable."""
    pass


class FileOperations:
    """Handles safe file operations with proper error handling and retry logic."""

    def __init__(self) -> None:
        """Initialize file operations with configuration."""
        self.supported_extensions = tuple(
            config.get(
                "images.supported_extensions", [".png", ".jpg", ".jpeg", ".gif", ".bmp"]
            )
        )
        self.max_file_size = (
            config.get("images.max_file_size_mb", 50) * 1024 * 1024
        )  # Convert to bytes
        self.max_retries = config.get("file_operations.safe_move_retries", 3)
        self.move_delay = config.get("file_operations.move_delay_seconds", 0.5)
        self.backup_originals = config.get("file_operations.backup_originals", False)
        self.confirm_overwrites = config.get("file_operations.confirm_overwrites", True)

    def is_supported_image(self, file_path: Path) -> bool:
        """
        Check if file is a supported image format.

        Args:
            file_path: Path to image file

        Returns:
            True if supported, False otherwise
        """
        return file_path.suffix.lower() in self.supported_extensions

    def verify_image(self, image_path: Path) -> bool:
        """
        Verify image file is valid and close all handles.

        Args:
            image_path: Path to the image file

        Returns:
            True if image is valid, False otherwise

        Raises:
            UnsupportedImageFormat: If format not supported
            ImageCorrupted: If image is corrupted
        """
        if not self.is_supported_image(image_path):
            raise UnsupportedImageFormat(
                f"Unsupported image format: {image_path.suffix}. "
                f"Supported formats: {', '.join(self.supported_extensions)}"
            )

        if not image_path.exists():
            raise FileOperationError(f"Image file not found: {image_path}")

        if not image_path.is_file():
            raise FileOperationError(f"Path is not a file: {image_path}")

        if image_path.stat().st_size > self.max_file_size:
            raise FileOperationError(
                f"Image file too large: {image_path.stat().st_size / (1024 * 1024):.1f}MB. "
                f"Maximum size: {self.max_file_size / (1024 * 1024):.1f}MB"
            )

        try:
            img = Image.open(image_path)
            img.verify()
            img.close()
            # Force garbage collection to ensure handles are released
            gc.collect()
            logger.debug(f"Image verification successful: {image_path.name}")
            return True
        except Exception as e:
            raise ImageCorrupted(
                f"Image verification failed for {image_path}: {e}"
            ) from e

    def safe_file_move(self, src: Path, dst: Path) -> bool:
        """
        Safely move a file using copy and delete strategy.

        Args:
            src: Source file path
            dst: Destination file path

        Returns:
            True if move successful

        Raises:
            FileOperationError: If move fails after all retries
            FilePermissionError: If permission issues prevent move
        """
        # Ensure the destination directory exists
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Check for overwrite conditions
        if dst.exists() and self.confirm_overwrites:
            logger.warning(f"Destination file exists: {dst}")
            # In a CLI context, you might want to prompt user
            # For now, we'll skip overwriting existing files
            raise FileOperationError(f"Destination file already exists: {dst}")

        # Create backup if requested
        backup_path = None
        if self.backup_originals and src.exists():
            backup_path = src.with_suffix(f"{src.suffix}.backup")
            try:
                shutil.copy2(src, backup_path)
                logger.info(f"Created backup: {backup_path}")
            except OSError as e:
                logger.warning(f"Failed to create backup: {e}")

        for attempt in range(self.max_retries):
            try:
                # Copy first
                shutil.copy2(src, dst)
                # Force garbage collection
                gc.collect()
                time.sleep(self.move_delay)  # Small delay to ensure copy is complete

                # Then try to remove original
                try:
                    src.unlink()
                    logger.info(f"Successfully moved: {src.name} -> {dst.name}")

                    # Remove backup if move was successful and backup was created
                    if backup_path and backup_path.exists():
                        backup_path.unlink()
                        logger.debug(f"Removed backup: {backup_path}")

                    return True

                except OSError as e:
                    logger.warning(f"Could not remove original file: {e}")
                    # If we can't remove original, remove the copy and try again
                    if dst.exists():
                        dst.unlink()

                    if attempt == self.max_retries - 1:
                        raise FilePermissionError(
                            f"Cannot remove original file after {self.max_retries} attempts: {e}"
                        ) from e

            except OSError as e:
                if attempt == self.max_retries - 1:
                    # Restore backup if available
                    if backup_path and backup_path.exists():
                        try:
                            shutil.copy2(backup_path, src)
                            backup_path.unlink()
                            logger.info(f"Restored from backup: {src}")
                        except OSError:
                            logger.error(f"Failed to restore backup for: {src}")

                    raise FileOperationError(
                        f"File move failed after {self.max_retries} attempts: {e}"
                    ) from e

                logger.warning(f"Move attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)  # Wait before retry

        return False

    def find_image_files(self, directory: Path, recursive: bool = False) -> list[Path]:
        """
        Find all supported image files in directory.

        Args:
            directory: Directory to search
            recursive: Whether to search recursively

        Returns:
            List of image file paths

        Raises:
            FileOperationError: If directory is invalid
        """
        if not directory.exists():
            raise FileOperationError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise FileOperationError(f"Path is not a directory: {directory}")

        image_files = []

        pattern_func = directory.rglob if recursive else directory.glob

        for file_path in pattern_func("*"):
            if file_path.is_file() and self.is_supported_image(file_path):
                image_files.append(file_path)

        logger.info(
            f"Found {len(image_files)} image files in: {directory} "
            f"({'recursive' if recursive else 'non-recursive'})"
        )
        return image_files

    def get_unique_filename(self, base_path: Path, suffix: str = "") -> Path:
        """
        Generate a unique filename by appending a counter if necessary.

        Args:
            base_path: Base file path
            suffix: Optional suffix to add before extension

        Returns:
            Unique file path
        """
        if suffix:
            name = f"{base_path.stem}{suffix}"
            new_path = base_path.with_name(f"{name}{base_path.suffix}")
        else:
            new_path = base_path

        if not new_path.exists():
            return new_path

        counter = 1
        while True:
            if suffix:
                name = f"{base_path.stem}{suffix}_{counter}"
            else:
                name = f"{base_path.stem}_{counter}"

            unique_path = base_path.with_name(f"{name}{base_path.suffix}")

            if not unique_path.exists():
                return unique_path

            counter += 1

    def create_backup(self, file_path: Path) -> Path:
        """
        Create a backup copy of a file.

        Args:
            file_path: Path to file to backup

        Returns:
            Path to backup file

        Raises:
            FileOperationError: If backup creation fails
        """
        if not file_path.exists():
            raise FileOperationError(
                f"Failed to create backup: {file_path} does not exist"
            )

        timestamp = int(time.time())
        backup_path = file_path.with_suffix(f".backup.{timestamp}{file_path.suffix}")

        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except OSError as e:
            raise FileOperationError(f"Failed to create backup: {e}") from e

    def ensure_directory_exists(self, directory: Path) -> None:
        """
        Ensure directory exists, creating it if necessary.

        Args:
            directory: Directory path to create

        Raises:
            FileOperationError: If directory creation fails
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ensured: {directory}")
        except OSError as e:
            raise FileOperationError(
                f"Failed to create directory {directory}: {e}"
            ) from e
