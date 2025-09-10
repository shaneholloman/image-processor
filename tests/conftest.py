"""
Shared test fixtures for image processor test suite.
"""

import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock

import pytest
from PIL import Image
from src.image_processor_name.api.ollama_client import OllamaClient
from src.image_processor_name.core.renamer import ImageRenamer
from src.image_processor_name.tools.file_operations import FileOperations


@pytest.fixture
def temp_dir() -> Generator[Path]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_config_dir(temp_dir: Path) -> Path:
    """Create a temporary config directory."""
    config_dir = temp_dir / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def sample_name_config() -> dict:
    """Provide a valid name tool configuration."""
    return {
        "ollama": {
            "endpoint": "http://localhost:11434/api/generate",
            "model": "llava-llama3:latest",
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1.0,
        },
        "images": {
            "supported_extensions": [".png", ".jpg", ".jpeg", ".gif", ".bmp"],
            "max_file_size_mb": 50,
            "verify_before_processing": True,
        },
        "filename": {
            "prompt": "Describe this image in 4-5 words",
            "pattern_cleanup": True,
            "max_length": 100,
            "remove_punctuation": True,
            "replace_spaces_with": "-",
            "case_conversion": "lower",
        },
        "file_operations": {
            "safe_move_retries": 3,
            "move_delay_seconds": 0.5,
            "backup_originals": False,
            "confirm_overwrites": True,
        },
        "logging": {
            "level": "INFO",
            "file": "image_renamer.log",
            "max_file_size_mb": 10,
            "backup_count": 5,
            "console_colors": True,
        },
        "processing": {
            "progress_bar": True,
            "batch_size": 10,
            "concurrent_operations": False,
        },
    }


@pytest.fixture
def invalid_config() -> dict:
    """Provide an invalid configuration for testing error handling."""
    return {
        "ollama": {
            "endpoint": "invalid-url",
            "model": "",
            "timeout": -1,
        },
        "filename": {
            "max_length": -10,
            "case_conversion": "invalid_case",
        },
    }


@pytest.fixture
def sample_image_small(temp_dir: Path) -> Path:
    """Create a small test JPEG image."""
    image_path = temp_dir / "test_image.jpg"
    # Create a small 10x10 red image
    img = Image.new("RGB", (10, 10), color="red")
    img.save(image_path, "JPEG")
    return image_path


@pytest.fixture
def sample_image_png(temp_dir: Path) -> Path:
    """Create a small test PNG image."""
    image_path = temp_dir / "test_image.png"
    # Create a small 10x10 blue image
    img = Image.new("RGB", (10, 10), color="blue")
    img.save(image_path, "PNG")
    return image_path


@pytest.fixture
def sample_images(temp_dir: Path) -> list[Path]:
    """Create multiple sample images for batch testing."""
    images = []
    for i, (fmt, ext) in enumerate(
        [("JPEG", ".jpg"), ("PNG", ".png"), ("GIF", ".gif")]
    ):
        image_path = temp_dir / f"test_image_{i}{ext}"
        img = Image.new("RGB", (10, 10), color=["red", "green", "blue"][i])
        if fmt == "GIF":
            img.save(image_path, fmt, save_all=True)
        else:
            img.save(image_path, fmt)
        images.append(image_path)
    return images


@pytest.fixture
def corrupted_image(temp_dir: Path) -> Path:
    """Create a corrupted image file for error testing."""
    image_path = temp_dir / "corrupted.jpg"
    # Write invalid JPEG data
    image_path.write_bytes(b"Not a valid image file")
    return image_path


@pytest.fixture
def large_image(temp_dir: Path) -> Path:
    """Create a larger test image."""
    image_path = temp_dir / "large_image.jpg"
    # Create a 100x100 image
    img = Image.new("RGB", (100, 100), color="green")
    img.save(image_path, "JPEG")
    return image_path


@pytest.fixture
def temp_image_dir(temp_dir: Path, sample_images: list[Path]) -> Path:
    """Create a directory with sample images."""
    image_dir = temp_dir / "images"
    image_dir.mkdir()

    # Copy sample images to the directory
    for i, sample_image in enumerate(sample_images):
        dest_path = image_dir / f"sample_{i}{sample_image.suffix}"
        dest_path.write_bytes(sample_image.read_bytes())

    return image_dir


@pytest.fixture
def mock_ollama_success() -> Mock:
    """Mock successful Ollama API responses."""
    mock_client = Mock(spec=OllamaClient)
    mock_client.test_connection.return_value = True
    mock_client.generate_filename.return_value = "beautiful sunset beach scene"
    mock_client.list_models.return_value = {"models": [{"name": "llava-llama3:latest"}]}
    return mock_client


@pytest.fixture
def mock_ollama_error() -> Mock:
    """Mock Ollama API error conditions."""
    mock_client = Mock(spec=OllamaClient)
    mock_client.test_connection.return_value = False
    mock_client.generate_filename.side_effect = Exception("Connection failed")
    mock_client.list_models.side_effect = Exception("API unavailable")
    return mock_client


@pytest.fixture
def mock_file_operations() -> Mock:
    """Mock file operations for testing without actual file system changes."""
    mock_ops = Mock(spec=FileOperations)
    mock_ops.is_supported_image.return_value = True
    mock_ops.verify_image.return_value = None
    mock_ops.safe_file_move.return_value = True
    mock_ops.get_unique_filename = lambda p: p
    return mock_ops


@pytest.fixture
def image_renamer(
    mock_ollama_success: Mock, mock_file_operations: Mock
) -> ImageRenamer:
    """Create an ImageRenamer instance with mocked dependencies."""
    return ImageRenamer(mock_ollama_success, mock_file_operations)


@pytest.fixture
def nested_image_dir(temp_dir: Path) -> Path:
    """Create a nested directory structure with images."""
    # Create directory structure
    base_dir = temp_dir / "nested_images"
    sub_dir1 = base_dir / "subdir1"
    sub_dir2 = base_dir / "subdir2" / "deep"

    for directory in [base_dir, sub_dir1, sub_dir2]:
        directory.mkdir(parents=True)

    # Create images in each directory
    for i, directory in enumerate([base_dir, sub_dir1, sub_dir2]):
        image_path = directory / f"image_{i}.jpg"
        img = Image.new("RGB", (10, 10), color=["red", "green", "blue"][i])
        img.save(image_path, "JPEG")

    return base_dir


@pytest.fixture
def unsupported_files(temp_dir: Path) -> list[Path]:
    """Create files with unsupported extensions."""
    files = []
    for ext in [".txt", ".pdf", ".doc", ".mp4"]:
        file_path = temp_dir / f"unsupported{ext}"
        file_path.write_text("Not an image")
        files.append(file_path)
    return files


# Markers for different test categories
pytest.fixture(autouse=True)


def add_markers(request):
    """Automatically add markers based on test location."""
    if "unit" in str(request.fspath):
        request.node.add_marker(pytest.mark.unit)
    elif "integration" in str(request.fspath):
        request.node.add_marker(pytest.mark.integration)
