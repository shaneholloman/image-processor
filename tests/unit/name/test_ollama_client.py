"""
Unit tests for image_processor_name Ollama client.
"""

import base64
import pathlib
import unittest.mock

import pytest
import src.image_processor_name.ollama_client


def test_init_with_defaults():
    """Test client initialization with default values."""
    with unittest.mock.patch("image_processor_name.config_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            "ollama.endpoint": "http://localhost:11434/api/generate",
            "ollama.model": "llava-llama3:latest",
            "ollama.timeout": 30,
        }.get(key, default)

        client = src.image_processor_name.ollama_client.OllamaClient()

        assert client.endpoint == "http://localhost:11434/api/generate"
        assert client.model == "llava-llama3:latest"
        assert client.timeout == 30


def test_encode_image_success(sample_image_small: pathlib.Path):
    """Test successful image encoding to base64."""
    with unittest.mock.patch("image_processor_name.config_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            "ollama.endpoint": "http://localhost:11434/api/generate",
            "ollama.model": "llava-llama3:latest",
            "ollama.timeout": 30,
            "ollama.retry_attempts": 3,
            "ollama.retry_delay": 1.0,
        }.get(key, default)

        client = src.image_processor_name.ollama_client.OllamaClient()

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


@unittest.mock.patch("image_processor_name.ollama_client.requests.post")
def test_generate_filename_success(mock_post: unittest.mock.Mock, sample_image_small: pathlib.Path):
    """Test successful filename generation."""
    # Mock successful API response
    mock_response = unittest.mock.Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "beautiful sunset beach scene"}
    mock_post.return_value = mock_response

    with unittest.mock.patch("image_processor_name.config_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            "ollama.endpoint": "http://localhost:11434/api/generate",
            "ollama.model": "llava-llama3:latest",
            "ollama.timeout": 30,
            "ollama.retry_attempts": 3,
            "ollama.retry_delay": 1.0,
        }.get(key, default)

        client = src.image_processor_name.ollama_client.OllamaClient()
        result = client.generate_filename(sample_image_small)

        assert result == "beautiful sunset beach scene"
        mock_post.assert_called_once()


@unittest.mock.patch("image_processor_name.ollama_client.requests.post")
def test_test_connection_success(mock_post: unittest.mock.Mock):
    """Test successful connection test."""
    mock_response = unittest.mock.Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": "test response"}
    mock_post.return_value = mock_response

    with unittest.mock.patch("image_processor_name.config_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            "ollama.endpoint": "http://localhost:11434/api/generate",
            "ollama.model": "llava-llama3:latest",
            "ollama.timeout": 30,
            "ollama.retry_attempts": 3,
            "ollama.retry_delay": 1.0,
        }.get(key, default)

        client = src.image_processor_name.ollama_client.OllamaClient()
        result = client.test_connection()

        assert result is True
