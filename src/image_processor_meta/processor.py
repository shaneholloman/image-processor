"""
Main image processing module with metadata management.
"""

import re
import time
from pathlib import Path

from tqdm import tqdm

import pyexiv2

from .api.ollama_client import OllamaClient
from .db.manager import DatabaseManager
from .exceptions import (
    FilePermissionError,
    ImageProcessingError,
    MetadataWriteError,
    UnsupportedImageFormat,
)
from .tools.config_manager import config
from .tools.log_manager import get_logger

logger = get_logger(__name__)


class ImageProcessor:
    """Main processor for handling image metadata operations."""

    def __init__(
        self,
        ollama_client: OllamaClient | None = None,
        database_manager: DatabaseManager | None = None,
    ) -> None:
        """
        Initialize image processor.

        Args:
            ollama_client: Ollama API client instance
            database_manager: Database manager instance
        """
        self.ollama_client = ollama_client or OllamaClient()
        self.db_manager = database_manager or DatabaseManager()

        # Load configuration
        self.supported_extensions = tuple(
            config.get(
                "images.supported_extensions", [".png", ".jpg", ".jpeg", ".gif", ".bmp"]
            )
        )
        self.retry_attempts = config.get("metadata.retry_attempts", 3)
        self.retry_delay = config.get("metadata.retry_delay", 1.0)
        self.max_file_size = (
            config.get("images.max_file_size_mb", 50) * 1024 * 1024
        )  # Convert to bytes

        logger.info("Image processor initialized")

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by replacing non-alphanumeric characters with dashes.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")

        # Replace non-alphanumeric chars with dash
        new_name = re.sub(r"[^a-zA-Z0-9]", "-", name)
        # Remove multiple consecutive dashes
        new_name = re.sub(r"-+", "-", new_name)
        # Remove leading/trailing dashes
        new_name = new_name.strip("-")

        return f"{new_name}.{ext}" if ext else new_name

    def sanitize_filenames_in_directory(self, directory: Path) -> int:
        """
        Sanitize all filenames in directory recursively.

        Args:
            directory: Directory to process

        Returns:
            Number of files renamed

        Raises:
            FilePermissionError: If file cannot be renamed
        """
        renamed_count = 0

        logger.info(f"Starting filename sanitization in: {directory}")

        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue

            original_name = file_path.name
            sanitized_name = self.sanitize_filename(original_name)

            if original_name != sanitized_name:
                new_path = file_path.parent / sanitized_name

                try:
                    file_path.rename(new_path)
                    renamed_count += 1
                    logger.info(f"Renamed: {original_name} -> {sanitized_name}")
                except OSError as e:
                    raise FilePermissionError(
                        f"Failed to rename {original_name}: {e}"
                    ) from e

        logger.info(f"Sanitization complete: {renamed_count} files renamed")
        return renamed_count

    def is_supported_image(self, file_path: Path) -> bool:
        """
        Check if file is a supported image format.

        Args:
            file_path: Path to image file

        Returns:
            True if supported, False otherwise
        """
        return file_path.suffix.lower() in self.supported_extensions

    def validate_image_file(self, file_path: Path) -> None:
        """
        Validate image file before processing.

        Args:
            file_path: Path to image file

        Raises:
            UnsupportedImageFormat: If format not supported
            ImageProcessingError: If file is invalid
        """
        if not file_path.exists():
            raise ImageProcessingError(f"Image file not found: {file_path}")

        if not file_path.is_file():
            raise ImageProcessingError(f"Path is not a file: {file_path}")

        if not self.is_supported_image(file_path):
            raise UnsupportedImageFormat(
                f"Unsupported image format: {file_path.suffix}. "
                f"Supported formats: {', '.join(self.supported_extensions)}"
            )

        if file_path.stat().st_size > self.max_file_size:
            raise ImageProcessingError(
                f"Image file too large: {file_path.stat().st_size / (1024 * 1024):.1f}MB. "
                f"Maximum size: {self.max_file_size / (1024 * 1024):.1f}MB"
            )

    def write_metadata_to_image(self, file_path: Path, description: str) -> None:
        """
        Write description as XMP metadata to image file.

        Args:
            file_path: Path to image file
            description: Description text to embed

        Raises:
            MetadataWriteError: If metadata writing fails
        """
        for attempt in range(self.retry_attempts):
            try:
                with pyexiv2.Image(str(file_path)) as image:
                    # Set XMP metadata
                    image.modify_xmp(
                        {
                            "Xmp.dc.description": description,
                            "Xmp.dc.subject": "AI Generated Description",
                            "Xmp.xmp.CreatorTool": "Image Meta Processor v2.0",
                        }
                    )

                logger.debug(f"Metadata written to: {file_path.name}")
                return

            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    raise MetadataWriteError(
                        f"Failed to write metadata after {self.retry_attempts} attempts: {e}"
                    ) from e

                logger.warning(
                    f"Metadata write attempt {attempt + 1} failed for {file_path.name}: {e}. "
                    f"Retrying in {self.retry_delay}s..."
                )
                time.sleep(self.retry_delay)

    def process_single_image(self, file_path: Path) -> bool:
        """
        Process a single image file.

        Args:
            file_path: Path to image file

        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Validate image file
            self.validate_image_file(file_path)

            # Check if description already exists
            existing_description = self.db_manager.get_description(str(file_path))
            if existing_description:
                logger.debug(f"Description already exists for: {file_path.name}")
                return True

            # Generate description
            description = self.ollama_client.generate_description(file_path)

            # Save to database
            self.db_manager.save_description(str(file_path), description)

            # Write metadata to image
            self.write_metadata_to_image(file_path, description)

            logger.info(f"Successfully processed: {file_path.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            return False

    def find_image_files(self, directory: Path) -> list[Path]:
        """
        Find all supported image files in directory recursively.

        Args:
            directory: Directory to search

        Returns:
            List of image file paths
        """
        image_files = []

        for file_path in directory.rglob("*"):
            if file_path.is_file() and self.is_supported_image(file_path):
                image_files.append(file_path)

        logger.info(f"Found {len(image_files)} image files in: {directory}")
        return image_files

    def process_directory(
        self, directory: Path, sanitize_names: bool = True, show_progress: bool = True
    ) -> dict:
        """
        Process all images in a directory.

        Args:
            directory: Directory containing images
            sanitize_names: Whether to sanitize filenames first
            show_progress: Whether to show progress bar

        Returns:
            Dictionary with processing statistics
        """
        start_time = time.time()

        if not directory.exists():
            raise ImageProcessingError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise ImageProcessingError(f"Path is not a directory: {directory}")

        logger.info(f"Starting directory processing: {directory}")

        # Sanitize filenames if requested
        renamed_count = 0
        if sanitize_names:
            renamed_count = self.sanitize_filenames_in_directory(directory)

        # Find image files
        image_files = self.find_image_files(directory)

        if not image_files:
            logger.warning("No image files found to process")
            return {
                "total_files": 0,
                "processed": 0,
                "failed": 0,
                "renamed": renamed_count,
                "processing_time": 0,
            }

        # Process images
        processed_count = 0
        failed_count = 0

        # Set up progress bar
        progress_bar = None
        if show_progress and config.get("processing.progress_bar", True):
            progress_bar = tqdm(
                image_files, desc="Processing images", unit="img", colour="green"
            )
            iterator = progress_bar
        else:
            iterator = image_files

        try:
            for file_path in iterator:
                if self.process_single_image(file_path):
                    processed_count += 1
                else:
                    failed_count += 1

                # Update progress bar description
                if progress_bar:
                    progress_bar.set_postfix(
                        {"processed": processed_count, "failed": failed_count}
                    )
        finally:
            if progress_bar:
                progress_bar.close()

        processing_time = time.time() - start_time

        # Log summary
        logger.info(
            f"Processing complete: {processed_count} processed, {failed_count} failed, "
            f"{renamed_count} renamed in {processing_time:.1f}s"
        )

        return {
            "total_files": len(image_files),
            "processed": processed_count,
            "failed": failed_count,
            "renamed": renamed_count,
            "processing_time": processing_time,
        }
