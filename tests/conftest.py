"""
Shared test fixtures and configuration.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory that gets cleaned up."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_image_files(temp_dir):
    """Create sample image files with various naming patterns."""
    files = [
        "normal-image.jpg",
        "image with spaces.png",
        "special@#characters.jpeg",
        "Mixed_Case_File.JPG",
        ".hidden_file.gif",
        "multiple---dashes.bmp",
        "underscore_file.jpg",
    ]

    created_files = []
    for filename in files:
        file_path = temp_dir / filename
        file_path.touch()
        created_files.append(file_path)

    return created_files


@pytest.fixture
def mock_ollama_response():
    """Create a mock response for Ollama API calls."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": "This is a detailed description of the test image."
    }
    return mock_response


@pytest.fixture
def sample_image_data():
    """Minimal valid JPEG data for testing."""
    # Minimal JPEG header
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9"


@pytest.fixture
def sample_jpeg_file(temp_dir, sample_image_data):
    """Create a sample JPEG file for testing."""
    jpeg_path = temp_dir / "test_image.jpg"
    with open(jpeg_path, "wb") as f:
        f.write(sample_image_data)
    return jpeg_path
