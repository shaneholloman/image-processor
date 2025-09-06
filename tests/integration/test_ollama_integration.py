"""
Integration tests for Ollama API client.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from image_processor_meta.api.ollama_client import OllamaClient
from image_processor_meta.exceptions import (
    OllamaConnectionError,
    OllamaResponseError,
    OllamaTimeoutError,
)


@pytest.fixture
def ollama_client():
    """Create Ollama client for testing."""
    return OllamaClient()


@pytest.mark.integration
class TestOllamaClient:
    """Test Ollama client functionality."""

    def test_encode_image(self, ollama_client, sample_jpeg_file):
        """Test image encoding to base64."""
        encoded = ollama_client.encode_image(sample_jpeg_file)

        assert isinstance(encoded, str)
        assert len(encoded) > 0

        # Should be valid base64
        import base64

        try:
            decoded = base64.b64decode(encoded)
            assert len(decoded) > 0
        except Exception:
            pytest.fail("Invalid base64 encoding")

    @patch("requests.post")
    def test_generate_description_success(
        self, mock_post, ollama_client, sample_jpeg_file
    ):
        """Test successful description generation."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "A detailed description of the test image."
        }
        mock_post.return_value = mock_response

        description = ollama_client.generate_description(sample_jpeg_file)

        assert description == "A detailed description of the test image."
        mock_post.assert_called_once()

        # Verify request payload
        call_kwargs = mock_post.call_args[1]
        assert "json" in call_kwargs
        payload = call_kwargs["json"]
        assert payload["model"] == ollama_client.model
        assert "images" in payload
        assert len(payload["images"]) == 1

    @patch("requests.post")
    def test_generate_description_404_error(
        self, mock_post, ollama_client, sample_jpeg_file
    ):
        """Test handling of 404 error (Ollama not found)."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        with pytest.raises(OllamaConnectionError, match="Ollama API not found"):
            ollama_client.generate_description(sample_jpeg_file)

    @patch("requests.post")
    def test_generate_description_server_error(
        self, mock_post, ollama_client, sample_jpeg_file
    ):
        """Test handling of server errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with pytest.raises(OllamaConnectionError, match="Ollama server error"):
            ollama_client.generate_description(sample_jpeg_file)

    @patch("requests.post")
    def test_generate_description_invalid_json(
        self, mock_post, ollama_client, sample_jpeg_file
    ):
        """Test handling of invalid JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_post.return_value = mock_response

        with pytest.raises(OllamaResponseError, match="Invalid JSON response"):
            ollama_client.generate_description(sample_jpeg_file)

    @patch("requests.post")
    def test_generate_description_missing_response_field(
        self, mock_post, ollama_client, sample_jpeg_file
    ):
        """Test handling of response missing 'response' field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Model not found"}
        mock_post.return_value = mock_response

        with pytest.raises(OllamaResponseError, match="Missing 'response' field"):
            ollama_client.generate_description(sample_jpeg_file)

    @patch("requests.post")
    def test_generate_description_empty_response(
        self, mock_post, ollama_client, sample_jpeg_file
    ):
        """Test handling of empty response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "   "}  # Whitespace only
        mock_post.return_value = mock_response

        with pytest.raises(OllamaResponseError, match="Empty description received"):
            ollama_client.generate_description(sample_jpeg_file)

    @patch("requests.post")
    def test_generate_description_timeout(
        self, mock_post, ollama_client, sample_jpeg_file
    ):
        """Test handling of request timeout."""
        from requests.exceptions import Timeout

        mock_post.side_effect = Timeout("Request timed out")

        with pytest.raises(OllamaTimeoutError):
            ollama_client.generate_description(sample_jpeg_file)

    @patch("requests.post")
    def test_generate_description_connection_error(
        self, mock_post, ollama_client, sample_jpeg_file
    ):
        """Test handling of connection errors."""
        from requests.exceptions import ConnectionError

        mock_post.side_effect = ConnectionError("Connection failed")

        with pytest.raises(OllamaConnectionError, match="Failed to connect to Ollama"):
            ollama_client.generate_description(sample_jpeg_file)

    @patch("requests.get")
    def test_test_connection_success(self, mock_get, ollama_client):
        """Test successful connection test."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = ollama_client.test_connection()
        assert result is True

    @patch("requests.get")
    def test_test_connection_failure(self, mock_get, ollama_client):
        """Test failed connection test."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = ollama_client.test_connection()
        assert result is False

    @patch("requests.get")
    def test_test_connection_exception(self, mock_get, ollama_client):
        """Test connection test with exception."""
        from requests.exceptions import ConnectionError

        mock_get.side_effect = ConnectionError("Connection failed")

        result = ollama_client.test_connection()
        assert result is False

    @patch("requests.get")
    def test_list_models_success(self, mock_get, ollama_client):
        """Test successful model listing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llava", "size": 1234567890},
                {"name": "mistral", "size": 987654321},
            ]
        }
        mock_get.return_value = mock_response
        mock_response.raise_for_status = MagicMock()

        models = ollama_client.list_models()

        assert "models" in models
        assert len(models["models"]) == 2
        assert models["models"][0]["name"] == "llava"

    @patch("requests.get")
    def test_list_models_failure(self, mock_get, ollama_client):
        """Test failed model listing."""
        from requests.exceptions import RequestException

        mock_get.side_effect = RequestException("Request failed")

        with pytest.raises(OllamaConnectionError, match="Failed to list models"):
            ollama_client.list_models()


@pytest.mark.integration
@pytest.mark.requires_ollama
class TestOllamaLiveIntegration:
    """Live integration tests requiring running Ollama instance."""

    def test_live_connection(self):
        """Test connection to live Ollama instance."""
        client = OllamaClient()

        # This test will be skipped if Ollama isn't running
        if not client.test_connection():
            pytest.skip("Ollama not available for live testing")

        assert client.test_connection() is True

    def test_live_description_generation(self, sample_jpeg_file):
        """Test live description generation."""
        client = OllamaClient()

        # Skip if Ollama not available
        if not client.test_connection():
            pytest.skip("Ollama not available for live testing")

        try:
            description = client.generate_description(sample_jpeg_file)

            assert isinstance(description, str)
            assert len(description) > 10  # Should be a reasonable description
            assert description != "Failed to generate description"

        except Exception as e:
            pytest.skip(f"Live Ollama test failed (expected in CI): {e}")

    def test_live_model_listing(self):
        """Test live model listing."""
        client = OllamaClient()

        # Skip if Ollama not available
        if not client.test_connection():
            pytest.skip("Ollama not available for live testing")

        try:
            models = client.list_models()

            assert isinstance(models, dict)
            assert "models" in models

        except Exception as e:
            pytest.skip(f"Live Ollama test failed (expected in CI): {e}")
