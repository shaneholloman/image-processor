"""
Unit tests for image processor functionality.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from image_processor_meta.exceptions import ImageProcessingError, UnsupportedImageFormat
from image_processor_meta.processor import ImageProcessor


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing."""
    client = Mock()
    client.generate_description.return_value = "Test image description"
    return client


@pytest.fixture
def mock_db_manager():
    """Mock database manager for testing."""
    manager = Mock()
    manager.get_description.return_value = None
    manager.save_description.return_value = True
    return manager


@pytest.fixture
def processor(mock_ollama_client, mock_db_manager):
    """Create processor instance with mocked dependencies."""
    return ImageProcessor(mock_ollama_client, mock_db_manager)


@pytest.mark.unit
class TestFilenamesSanitization:
    """Test filename sanitization functionality."""

    def test_sanitize_filename_basic(self, processor):
        """Test basic filename sanitization."""
        assert processor.sanitize_filename("normal-file.jpg") == "normal-file.jpg"
        assert (
            processor.sanitize_filename("file with spaces.png")
            == "file-with-spaces.png"
        )
        assert (
            processor.sanitize_filename("special@#chars.jpeg") == "special-chars.jpeg"
        )

    def test_sanitize_filename_edge_cases(self, processor):
        """Test edge cases in filename sanitization."""
        assert (
            processor.sanitize_filename("---multiple---dashes---.gif")
            == "multiple-dashes.gif"
        )
        assert processor.sanitize_filename("..leading.dots..jpg") == "leading-dots.jpg"
        assert (
            processor.sanitize_filename("trailing...dots...bmp") == "trailing-dots.bmp"
        )

    def test_sanitize_filenames_in_directory(self, processor, sample_image_files):
        """Test sanitizing all files in a directory."""
        directory = sample_image_files[0].parent

        with patch("pathlib.Path.rename") as mock_rename:
            count = processor.sanitize_filenames_in_directory(directory)

            # Should rename files that need sanitization
            assert count > 0
            assert mock_rename.call_count == count


@pytest.mark.unit
class TestImageValidation:
    """Test image file validation."""

    def test_is_supported_image(self, processor):
        """Test supported image format detection."""
        assert processor.is_supported_image(Path("test.jpg")) is True
        assert processor.is_supported_image(Path("test.jpeg")) is True
        assert processor.is_supported_image(Path("test.png")) is True
        assert processor.is_supported_image(Path("test.gif")) is True
        assert processor.is_supported_image(Path("test.bmp")) is True
        assert (
            processor.is_supported_image(Path("test.JPG")) is True
        )  # Case insensitive
        assert processor.is_supported_image(Path("test.txt")) is False
        assert processor.is_supported_image(Path("test")) is False

    def test_validate_image_file_success(self, processor, sample_jpeg_file):
        """Test successful image validation."""
        # Should not raise an exception
        processor.validate_image_file(sample_jpeg_file)

    def test_validate_image_file_not_found(self, processor, temp_dir):
        """Test validation of non-existent file."""
        non_existent = temp_dir / "missing.jpg"

        with pytest.raises(ImageProcessingError, match="Image file not found"):
            processor.validate_image_file(non_existent)

    def test_validate_image_file_unsupported_format(self, processor, temp_dir):
        """Test validation of unsupported format."""
        text_file = temp_dir / "document.txt"
        text_file.touch()

        with pytest.raises(UnsupportedImageFormat):
            processor.validate_image_file(text_file)

    def test_validate_image_file_too_large(self, processor, temp_dir):
        """Test validation of oversized file."""
        large_file = temp_dir / "huge.jpg"

        # Mock file size to be larger than max allowed
        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = 100 * 1024 * 1024  # 100MB
            large_file.touch()

            with pytest.raises(ImageProcessingError, match="Image file too large"):
                processor.validate_image_file(large_file)


@pytest.mark.unit
class TestImageProcessing:
    """Test individual image processing functionality."""

    def test_process_single_image_success(self, processor, sample_jpeg_file):
        """Test successful processing of a single image."""
        with patch.object(processor, "write_metadata_to_image") as mock_write:
            result = processor.process_single_image(sample_jpeg_file)

            assert result is True
            processor.ollama_client.generate_description.assert_called_once()
            processor.db_manager.save_description.assert_called_once()
            mock_write.assert_called_once()

    def test_process_single_image_existing_description(
        self, processor, sample_jpeg_file
    ):
        """Test processing image that already has description."""
        processor.db_manager.get_description.return_value = "Existing description"

        result = processor.process_single_image(sample_jpeg_file)

        assert result is True
        # Should not call Ollama or write metadata for existing descriptions
        processor.ollama_client.generate_description.assert_not_called()

    def test_process_single_image_validation_failure(self, processor, temp_dir):
        """Test processing with validation failure."""
        invalid_file = temp_dir / "invalid.txt"
        invalid_file.touch()

        result = processor.process_single_image(invalid_file)

        assert result is False
        processor.ollama_client.generate_description.assert_not_called()

    def test_find_image_files(self, processor, sample_image_files):
        """Test finding image files in directory."""
        directory = sample_image_files[0].parent

        found_files = processor.find_image_files(directory)

        # Should find all image files (not text files)
        assert len(found_files) == len(sample_image_files)
        for file_path in found_files:
            assert processor.is_supported_image(file_path)


@pytest.mark.unit
class TestDirectoryProcessing:
    """Test directory-level processing functionality."""

    def test_process_directory_success(self, processor, sample_image_files):
        """Test successful directory processing."""
        directory = sample_image_files[0].parent

        with patch.object(
            processor, "process_single_image", return_value=True
        ) as mock_process:
            with patch.object(
                processor, "sanitize_filenames_in_directory", return_value=2
            ):
                results = processor.process_directory(directory, show_progress=False)

        assert results["total_files"] == len(sample_image_files)
        assert results["processed"] == len(sample_image_files)
        assert results["failed"] == 0
        assert results["renamed"] == 2
        assert mock_process.call_count == len(sample_image_files)

    def test_process_directory_with_failures(self, processor, sample_image_files):
        """Test directory processing with some failures."""
        directory = sample_image_files[0].parent

        # Mock some files to fail processing
        def mock_process_side_effect(file_path):
            return "failure" not in file_path.name

        with patch.object(
            processor, "process_single_image", side_effect=mock_process_side_effect
        ):
            with patch.object(
                processor, "sanitize_filenames_in_directory", return_value=0
            ):
                # Create a file with "failure" in the name to trigger failure
                failure_file = directory / "failure_test.jpg"
                failure_file.touch()

                results = processor.process_directory(directory, show_progress=False)

        assert results["failed"] > 0
        assert results["processed"] + results["failed"] == results["total_files"]

    def test_process_directory_not_found(self, processor, temp_dir):
        """Test processing non-existent directory."""
        non_existent = temp_dir / "missing"

        with pytest.raises(ImageProcessingError, match="Directory not found"):
            processor.process_directory(non_existent)

    def test_process_directory_empty(self, processor, temp_dir):
        """Test processing empty directory."""
        results = processor.process_directory(temp_dir, show_progress=False)

        assert results["total_files"] == 0
        assert results["processed"] == 0
        assert results["failed"] == 0


@pytest.mark.unit
class TestMetadataWriting:
    """Test metadata writing functionality."""

    def test_write_metadata_to_image_success(self, processor, sample_jpeg_file):
        """Test successful metadata writing."""
        with patch("pyexiv2.Image") as mock_image_class:
            mock_image = Mock()
            mock_image_class.return_value.__enter__.return_value = mock_image

            processor.write_metadata_to_image(sample_jpeg_file, "Test description")

            mock_image.modify_xmp.assert_called_once()
            call_args = mock_image.modify_xmp.call_args[0][0]
            assert "Xmp.dc.description" in call_args
            assert call_args["Xmp.dc.description"] == "Test description"

    def test_write_metadata_to_image_retry(self, processor, sample_jpeg_file):
        """Test metadata writing with retry mechanism."""
        with patch("pyexiv2.Image") as mock_image_class:
            mock_image = Mock()
            mock_image_class.return_value.__enter__.return_value = mock_image

            # First call fails, second succeeds
            mock_image.modify_xmp.side_effect = [Exception("Write failed"), None]

            with patch("time.sleep"):  # Speed up test
                processor.write_metadata_to_image(sample_jpeg_file, "Test description")

            # Should have been called twice (retry)
            assert mock_image.modify_xmp.call_count == 2
