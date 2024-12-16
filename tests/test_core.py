"""
Core unit tests for image_sanitize_meta_processor.py

These tests focus on core functionality that can run anywhere,
including CI environments. They don't require external services
or specific local setup.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from image_sanitize_meta_processor import is_supported_image, sanitize_filenames


@pytest.fixture
def temp_image_dir():
    """Create a temporary directory with test images."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
# pylint: disable=redefined-outer-name
def sample_images(temp_image_dir):
    """Create sample image files for testing."""
    test_files = [
        "normal-image.jpg",
        "image with spaces.jpg",
        "special@#characters.jpg",
        "Mixed_Case_File.JPG",
        ".hidden_file.jpg",
    ]

    for filename in test_files:
        Path(temp_image_dir, filename).touch()

    return test_files


@pytest.mark.unit
def test_is_supported_image():
    """Test file extension validation."""
    assert is_supported_image("test.jpg") is True
    assert is_supported_image("test.jpeg") is True
    assert is_supported_image("test.png") is True
    assert is_supported_image("test.txt") is False
    assert is_supported_image("test") is False
    assert is_supported_image("test.JPG") is True  # Case insensitive


@pytest.mark.unit
# pylint: disable=redefined-outer-name,unused-argument
def test_sanitize_filenames(temp_image_dir, sample_images):
    """Test filename sanitization functionality."""
    # Run sanitization
    sanitize_filenames(temp_image_dir)

    # Check results
    sanitized_files = os.listdir(temp_image_dir)

    # Verify expected transformations
    assert "normal-image.jpg" in sanitized_files
    assert "image-with-spaces.jpg" in sanitized_files
    assert "hidden-file.jpg" in sanitized_files
