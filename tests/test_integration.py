"""
Integration tests for image_sanitize_meta_processor.py

These tests require local setup (Ollama running, real image files)
and are intended for development and feature validation.
"""

import base64
import json
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pyexiv2
import pytest
import requests

from image_sanitize_meta_processor import get_image_description, write_metadata


@pytest.fixture
def temp_image_dir():
    """Create a temporary directory with test images."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_jpeg(temp_image_dir):
    """Create a minimal valid JPEG file for testing."""
    jpeg_path = os.path.join(temp_image_dir, "test.jpg")

    # Copy a test image from the images directory
    test_image = os.path.join("images", os.listdir("images")[0])
    shutil.copy(test_image, jpeg_path)

    return jpeg_path


@pytest.mark.integration
def test_write_metadata(sample_jpeg):
    """Test metadata writing functionality with real image file."""
    test_description = "Test image description"

    # Attempt to write metadata
    result = write_metadata(sample_jpeg, test_description)
    assert result is True

    # Verify metadata was written
    try:

        with pyexiv2.Image(sample_jpeg) as img:
            metadata = img.read_xmp()
            # XMP metadata includes language tag, so we need to check the nested structure
            assert (
                metadata["Xmp.dc.description"]['lang="x-default"'] == test_description
            )
    except Exception as e:
        pytest.fail(f"Failed to verify metadata: {str(e)}")


@pytest.mark.integration
@pytest.mark.requires_ollama
def test_get_image_description_live():
    """Test image description generation with live Ollama API."""
    # Use a real image from our images directory
    test_image = os.path.join("images", os.listdir("images")[0])

    # Get description from Ollama
    description = get_image_description(test_image)

    # Verify we got a non-empty description
    assert description != ""
    assert description != "Failed to generate description"
    assert len(description) > 10  # Reasonable minimum length


@pytest.mark.unit
def test_get_image_description_mocked(sample_jpeg):
    """Test image description generation with mocked API (CI-friendly)."""
    # Mock the streaming response from Ollama
    mock_responses = [
        json.dumps({"response": "This is "}).encode(),
        json.dumps({"response": "a test "}).encode(),
        json.dumps({"response": "description"}).encode(),
    ]

    # Create a mock response that behaves like a context manager
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = mock_responses

    # Configure the mock to work as a context manager
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None

    with patch("requests.post") as mock_post:
        mock_post.return_value = mock_response

        # Test with our sample image
        description = get_image_description(sample_jpeg)

        # Verify the result
        assert description == "This is a test description"

        # Verify the API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/generate"
        assert "images" in call_args[1]["json"]
        assert call_args[1]["json"]["model"] == "llava-llama3"

        # Verify base64 image was included
        assert isinstance(call_args[1]["json"]["images"][0], str)
        # Try decoding base64 to ensure it's valid
        try:
            base64.b64decode(call_args[1]["json"]["images"][0])
        except Exception:
            pytest.fail("Invalid base64 image data in API call")
