"""
Unit tests for image_processor_name Ollama client.
"""

import base64
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from src.image_processor_name.api.ollama_client import OllamaClient


def test_init_with_defaults():
    """Test client initialization with default values."""
    with patch("src.image_processor_name.tools.config_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            "ollama.endpoint": "http://localhost:11434/api/generate",
            "ollama.model": "llava-llama3:latest",
            "ollama.timeout": 30,
        }.get(key, default)

        client = OllamaClient()

        assert client.endpoint == "http://localhost:11434/api/generate"
        assert client.model == "llava-llama3:latest"
        assert client.timeout == 30


def test_encode_image_success(sample_image_small: Path):
    """Test successful image encoding to base64."""
    client = OllamaClient()

    encoded = client.encode_image(sample_image_small)

    # Should return a base64 string
    assert isinstance(encoded, str)
    assert len(encoded) > 0

    # Should be valid base64
    try:
        decoded = base64.b64decode(encoded)
        assert len(decoded) > 0
    except Exception:
        pytest.fail("Encoded string is not valid base64")


@patch("src.image_processor_name.api.ollama_client.requests.post")
def test_generate_filename_success(mock_post: Mock, sample_image_small: Path):
    """Test successful filename generation."""
    # Mock successful API response
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "beautiful sunset beach scene"}
    mock_post.return_value = mock_response

    client = OllamaClient()
    result = client.generate_filename(sample_image_small)

    assert result == "beautiful sunset beach scene"
    mock_post.assert_called_once()


@patch("src.image_processor_name.api.ollama_client.requests.post")
def test_test_connection_success(mock_post: Mock):
    """Test successful connection test."""
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": "test response"}
    mock_post.return_value = mock_response

    client = OllamaClient()
    result = client.test_connection()

    assert result is True
