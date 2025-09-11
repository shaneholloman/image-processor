"""
Core image renaming functionality with AI-powered filename generation.
"""

import re
import time
from pathlib import Path

from tqdm import tqdm

from .config_manager import config
from .file_operations import FileOperations
from .log_manager import get_logger
from .ollama_client import OllamaClient

logger = get_logger(__name__)


class ImageRenameError(Exception):
    pass


class ImageRenamer:
    """Main class for handling AI-powered image filename generation."""

    def __init__(
        self,
        ollama_client: OllamaClient | None = None,
        file_operations: FileOperations | None = None,
    ) -> None:
        """
        Initialize image renamer.

        Args:
            ollama_client: Ollama API client instance
            file_operations: File operations handler instance
        """
        self.ollama_client = ollama_client or OllamaClient()
        self.file_ops = file_operations or FileOperations()

        # Load filename configuration
        self.pattern_cleanup = config.get("filename.pattern_cleanup", True)
        self.max_length = config.get("filename.max_length", 100)
        self.remove_punctuation = config.get("filename.remove_punctuation", True)
        self.replace_spaces_with = config.get("filename.replace_spaces_with", "-")
        self.case_conversion = config.get("filename.case_conversion", "lower")

        logger.info("Image renamer initialized")

    def sanitize_filename(self, description: str, original_extension: str) -> str:
        """
        Convert AI description to a clean filename.

        Args:
            description: AI-generated description
            original_extension: Original file extension

        Returns:
            Sanitized filename
        """
        # Start with the description
        filename = description.strip()

        # Remove trailing punctuation if configured
        if self.remove_punctuation:
            filename = filename.rstrip(".,!?;:")

        # Apply case conversion
        if self.case_conversion == "lower":
            filename = filename.lower()
        elif self.case_conversion == "upper":
            filename = filename.upper()
        elif self.case_conversion == "title":
            filename = filename.title()
        # "none" means no conversion

        if self.pattern_cleanup:
            # Replace non-alphanumeric characters with configured replacement
            filename = re.sub(r"[^a-zA-Z0-9\s]", "", filename)
            # Replace spaces with configured character
            filename = filename.replace(" ", self.replace_spaces_with)
            # Replace multiple consecutive replacement characters
            if self.replace_spaces_with:
                pattern = re.escape(self.replace_spaces_with) + "+"
                filename = re.sub(pattern, self.replace_spaces_with, filename)
            # Remove leading/trailing replacement characters
            filename = filename.strip(self.replace_spaces_with)

        # Limit length while preserving word boundaries
        if len(filename) > self.max_length:
            # Try to break at word boundaries
            words = filename.split(self.replace_spaces_with)
            result = ""
            for word in words:
                test_result = (
                    result + (self.replace_spaces_with if result else "") + word
                )
                if len(test_result) > self.max_length:
                    break
                result = test_result
            filename = result if result else filename[: self.max_length]

        # Ensure filename is not empty
        if not filename:
            filename = "unnamed"

        # Add original extension
        return f"{filename}{original_extension}"

    def generate_filename(
        self, image_path: Path, prompt: str | None = None
    ) -> str | None:
        """
        Generate a new filename for an image using AI description.

        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt

        Returns:
            New filename or None if unsuccessful
        """
        try:
            # Verify image first
            if config.get("images.verify_before_processing", True):
                self.file_ops.verify_image(image_path)

            # Generate description
            description = self.ollama_client.generate_filename(image_path, prompt)

            # Convert to filename
            new_filename = self.sanitize_filename(description, image_path.suffix)

            logger.debug(f"Generated filename: {image_path.name} -> {new_filename}")
            return new_filename

        except Exception as e:
            logger.error(f"Failed to generate filename for {image_path.name}: {e}")
            return None

    def rename_single_image(self, image_path: Path, dry_run: bool = False) -> bool:
        """
        Rename a single image file.

        Args:
            image_path: Path to image file
            dry_run: If True, only show what would be renamed without doing it

        Returns:
            True if renaming successful (or would be successful in dry run)
        """
        try:
            if not image_path.exists() or not image_path.is_file():
                logger.error(f"Image file not found or invalid: {image_path}")
                return False

            if not self.file_ops.is_supported_image(image_path):
                logger.debug(f"Skipping unsupported file: {image_path}")
                return False

            # Generate new filename
            new_filename = self.generate_filename(image_path)
            if not new_filename:
                return False

            new_path = image_path.parent / new_filename

            # Check if new name is the same as current
            if new_path == image_path:
                logger.info(f"Filename already optimal: {image_path.name}")
                return True

            # Handle name conflicts
            if new_path.exists():
                new_path = self.file_ops.get_unique_filename(new_path)
                logger.info(f"Using unique filename: {new_path.name}")

            if dry_run:
                logger.info(
                    f"DRY RUN: Would rename {image_path.name} -> {new_path.name}"
                )
                return True

            # Perform the rename
            success = self.file_ops.safe_file_move(image_path, new_path)
            if success:
                logger.info(
                    f"Successfully renamed: {image_path.name} -> {new_path.name}"
                )
            return success

        except Exception as e:
            logger.error(f"Failed to rename {image_path.name}: {e}")
            return False

    def rename_directory(
        self,
        directory: Path,
        recursive: bool = False,
        dry_run: bool = False,
        show_progress: bool = True,
    ) -> dict[str, int]:
        """
        Rename all images in a directory using the original working logic.

        Args:
            directory: Directory containing images
            recursive: Whether to process subdirectories
            dry_run: If True, only show what would be renamed
            show_progress: Whether to show progress bar

        Returns:
            Dictionary with processing statistics
        """
        start_time = time.time()

        try:
            processed_count = 0
            failed_count = 0
            skipped_count = 0

            # Use original simple logic - process each file exactly once
            pattern = "**/*" if recursive else "*"
            all_files = list(directory.glob(pattern))

            # Filter for image files
            image_files = [
                f
                for f in all_files
                if f.is_file() and self.file_ops.is_supported_image(f)
            ]

            if not image_files:
                logger.warning("No image files found to process")
                return {
                    "total_files": 0,
                    "processed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "processing_time": 0,
                }

            logger.info(f"Found {len(image_files)} images to process")

            # Set up progress bar
            progress_bar = None
            if show_progress and config.get("processing.progress_bar", True):
                action = "Analyzing" if dry_run else "Renaming"
                progress_bar = tqdm(
                    image_files, desc=f"{action} images", unit="img", colour="green"
                )
                iterator = progress_bar
            else:
                iterator = image_files

            try:
                # Simple iteration like the original - no complex tracking
                for image_path in iterator:
                    result = self.rename_single_image(image_path, dry_run)
                    if result:
                        processed_count += 1
                    else:
                        failed_count += 1

                    # Update progress bar description
                    if progress_bar:
                        progress_bar.set_postfix(
                            {
                                "processed": processed_count,
                                "failed": failed_count,
                            }
                        )

            finally:
                if progress_bar:
                    progress_bar.close()

            processing_time = time.time() - start_time

            # Log summary
            action = "analyzed" if dry_run else "processed"
            logger.info(
                f"Processing complete: {processed_count} {action}, {failed_count} failed in {processing_time:.1f}s"
            )

            return {
                "total_files": len(image_files),
                "processed": processed_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"Directory processing failed: {e}")
            raise ImageRenameError(
                f"Failed to process directory {directory}: {e}"
            ) from e

    def test_connection(self) -> bool:
        """
        Test connection to Ollama service.

        Returns:
            True if connection successful
        """
        try:
            return self.ollama_client.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
