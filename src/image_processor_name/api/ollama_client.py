"""
Ollama API client for image filename generation.
"""

import base64
import json
import time
from pathlib import Path
from typing import Any

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout

from ..tools.config_manager import config
from ..tools.log_manager import get_logger

logger = get_logger(__name__)


# Ollama-specific exceptions
class OllamaConnectionError(Exception):
    """Raised when connection to Ollama fails."""
    pass


class OllamaTimeoutError(Exception):
    """Raised when Ollama request times out."""
    pass


class OllamaResponseError(Exception):
    """Raised when Ollama returns invalid response."""
    pass


class ImageCorrupted(Exception):
    """Raised when image file is corrupted or unreadable."""
    pass


class OllamaClient:
    """Client for interacting with Ollama API for filename generation."""

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
            "ollama.endpoint", "http://localhost:11434/api/generate"
        )
        self.model = model or config.get("ollama.model", "llava-llama3:latest")
        self.timeout = timeout or config.get("ollama.timeout", 30)
        self.retry_attempts = config.get("ollama.retry_attempts", 3)
        self.retry_delay = config.get("ollama.retry_delay", 1.0)

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
            with image_path.open("rb") as image_file:
                image_data = image_file.read()
                encoded_string = base64.b64encode(image_data).decode("utf-8")
                logger.debug(
                    f"Encoded image: {image_path} ({len(encoded_string)} chars)"
                )
                return encoded_string
        except Exception as e:
            raise ImageCorrupted(f"Failed to encode image {image_path}: {e}") from e

    def generate_filename(self, image_path: Path, prompt: str | None = None) -> str:
        """
        Generate filename description for image using Ollama.

        Args:
            image_path: Path to image file
            prompt: Custom prompt for description (optional)

        Returns:
            Generated description text for filename

        Raises:
            OllamaConnectionError: If connection to Ollama fails
            OllamaTimeoutError: If request times out
            OllamaResponseError: If response is invalid
            ImageCorrupted: If image cannot be processed
        """
        start_time = time.time()

        # Use configured prompt if none provided
        if prompt is None:
            prompt = config.get("filename.prompt", "Describe this image in 4-5 words")

        for attempt in range(self.retry_attempts):
            try:
                # Encode image
                encoded_image = self.encode_image(image_path)

                # Prepare request payload for generate API
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "images": [encoded_image],
                }

                logger.info(
                    f"Generating filename for: {image_path.name} (attempt {attempt + 1})"
                )

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

                # Extract description from generate API response
                if "response" not in response_data:
                    raise OllamaResponseError(
                        f"Missing 'response' field in Ollama response: {response_data}"
                    )

                description = response_data["response"].strip()
                if not description:
                    raise OllamaResponseError("Empty description received from Ollama")

                elapsed_time = time.time() - start_time
                logger.info(
                    f"Generated filename description for {image_path.name} "
                    f"({len(description)} chars, {elapsed_time:.1f}s)"
                )

                return description

            except (Timeout, ConnectionError) as e:
                if attempt == self.retry_attempts - 1:
                    if isinstance(e, Timeout):
                        raise OllamaTimeoutError(
                            f"Request to Ollama timed out after {self.timeout}s"
                        ) from e
                    raise OllamaConnectionError(
                        f"Failed to connect to Ollama at {self.endpoint}: {e}"
                    ) from e

                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {self.retry_delay}s..."
                )
                time.sleep(self.retry_delay)

            except RequestException as e:
                if attempt == self.retry_attempts - 1:
                    raise OllamaConnectionError(f"Request to Ollama failed: {e}") from e

                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {self.retry_delay}s..."
                )
                time.sleep(self.retry_delay)

        # This should not be reached due to the retry logic above
        raise OllamaConnectionError("All retry attempts exhausted")

    def test_connection(self) -> bool:
        """
        Test connection to Ollama API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to get model info using the tags endpoint
            base_url = self.endpoint.replace("/api/generate", "")
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
            base_url = self.endpoint.replace("/api/generate", "")
            response = requests.get(f"{base_url}/api/tags", timeout=10)
            response.raise_for_status()
            return response.json()

        except RequestException as e:
            raise OllamaConnectionError(f"Failed to list models: {e}") from e
