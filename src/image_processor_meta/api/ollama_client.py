"""
Ollama API client for image description generation.
"""

import base64
import json
import time
from pathlib import Path
from typing import Any

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout

from ..exceptions import (
    ImageCorrupted,
    OllamaConnectionError,
    OllamaResponseError,
    OllamaTimeoutError,
)
from ..tools.config_manager import config
from ..tools.log_manager import get_logger

logger = get_logger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(
        self,
        endpoint: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """
        Initialize Ollama client.

        Args:
            endpoint: Ollama API endpoint URL
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint or config.get(
            "ollama.endpoint", "http://localhost:11434/api/chat"
        )
        self.model = model or config.get("ollama.model", "llava")
        self.timeout = timeout or config.get("ollama.timeout", 30)

        logger.info(f"Initialized Ollama client: {self.endpoint} (model: {self.model})")

    def encode_image(self, image_path: Path) -> str:
        """
        Encode image file to base64 string.

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded image string

        Raises:
            ImageCorrupted: If image file cannot be read
        """
        try:
            with Path(image_path).open("rb") as image_file:
                image_data = image_file.read()
                encoded_string = base64.b64encode(image_data).decode("utf-8")
                logger.debug(
                    f"Encoded image: {image_path} ({len(encoded_string)} chars)"
                )
                return encoded_string
        except Exception as e:
            raise ImageCorrupted(f"Failed to encode image {image_path}: {e}") from e

    def generate_description(self, image_path: Path, prompt: str | None = None) -> str:
        """
        Generate description for image using Ollama.

        Args:
            image_path: Path to image file
            prompt: Custom prompt for description (optional)

        Returns:
            Generated description text

        Raises:
            OllamaConnectionError: If connection to Ollama fails
            OllamaTimeoutError: If request times out
            OllamaResponseError: If response is invalid
            ImageCorrupted: If image cannot be processed
        """
        start_time = time.time()

        try:
            # Encode image
            encoded_image = self.encode_image(image_path)

            # Prepare request payload for chat API
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt or "Describe this image in detail.",
                        "images": [encoded_image]
                    }
                ],
                "stream": False,
            }

            logger.info(f"Generating description for: {image_path.name}")

            # Make request to Ollama
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )

            # Handle HTTP errors
            if response.status_code == 404:
                raise OllamaConnectionError(
                    f"Ollama API not found at {self.endpoint}. "
                    "Ensure Ollama is running and accessible."
                )
            if response.status_code >= 500:
                raise OllamaConnectionError(
                    f"Ollama server error (HTTP {response.status_code}): {response.text}"
                )
            if response.status_code != 200:
                raise OllamaResponseError(
                    f"Unexpected HTTP status {response.status_code}: {response.text}"
                )

            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                raise OllamaResponseError(f"Invalid JSON response: {e}") from e

            # Extract description from chat API response
            if "message" not in response_data:
                raise OllamaResponseError(
                    f"Missing 'message' field in Ollama response: {response_data}"
                )

            if "content" not in response_data["message"]:
                raise OllamaResponseError(
                    f"Missing 'content' field in message: {response_data}"
                )

            description = response_data["message"]["content"].strip()
            if not description:
                raise OllamaResponseError("Empty description received from Ollama")

            elapsed_time = time.time() - start_time
            logger.info(
                f"Generated description for {image_path.name} "
                f"({len(description)} chars, {elapsed_time:.1f}s)"
            )

            return description

        except Timeout as e:
            raise OllamaTimeoutError(
                f"Request to Ollama timed out after {self.timeout}s"
            ) from e
        except ConnectionError as e:
            raise OllamaConnectionError(
                f"Failed to connect to Ollama at {self.endpoint}: {e}"
            ) from e
        except RequestException as e:
            raise OllamaConnectionError(f"Request to Ollama failed: {e}") from e

    def test_connection(self) -> bool:
        """
        Test connection to Ollama API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to get model info using the tags endpoint
            base_url = self.endpoint.replace('/api/chat', '')
            response = requests.get(
                f"{base_url}/api/tags",
                timeout=5,
            )

            if response.status_code == 200:
                logger.info("Ollama connection test successful")
                return True
            logger.warning(
                f"Ollama connection test failed: HTTP {response.status_code}"
            )
            return False

        except Exception as e:
            logger.warning(f"Ollama connection test failed: {e}")
            return False

    def list_models(self) -> dict[str, Any]:
        """
        List available models from Ollama.

        Returns:
            Dictionary containing model information

        Raises:
            OllamaConnectionError: If request fails
        """
        try:
            base_url = self.endpoint.replace('/api/chat', '')
            response = requests.get(
                f"{base_url}/api/tags", timeout=10
            )
            response.raise_for_status()
            return response.json()

        except RequestException as e:
            raise OllamaConnectionError(f"Failed to list models: {e}") from e
