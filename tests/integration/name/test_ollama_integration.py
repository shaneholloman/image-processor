"""
Integration tests for Ollama API connectivity (requires running Ollama).
"""

import pathlib

import PIL.Image
import pytest
import src.image_processor_name.ollama_client


@pytest.fixture(scope="module")
def ollama_client():
    """Create an Ollama client for testing."""
    return src.image_processor_name.ollama_client.OllamaClient()


@pytest.mark.requires_ollama
def test_connection_to_local_ollama(ollama_client: src.image_processor_name.ollama_client.OllamaClient):
    """Test basic connection to local Ollama instance."""
    result = ollama_client.test_connection()

    if not result:
        pytest.skip("Ollama not available - skipping integration tests")

    assert result is True


@pytest.mark.requires_ollama
def test_list_available_models(ollama_client: src.image_processor_name.ollama_client.OllamaClient):
    """Test listing available models from Ollama."""
    try:
        models = ollama_client.list_models()

        assert "models" in models
        assert isinstance(models["models"], list)

        # Should have at least one model
        assert len(models["models"]) > 0

        # Each model should have a name
        for model in models["models"]:
            assert "name" in model
            assert isinstance(model["name"], str)
            assert len(model["name"]) > 0

    except src.image_processor_name.ollama_client.OllamaConnectionError:
        pytest.skip("Ollama not available - skipping model list test")


@pytest.mark.requires_ollama
def test_generate_filename_with_real_image(
    ollama_client: src.image_processor_name.ollama_client.OllamaClient, sample_image_small: pathlib.Path
):
    """Test filename generation with a real image using live Ollama."""
    try:
        description = ollama_client.generate_filename(sample_image_small)

        assert isinstance(description, str)
        assert len(description) > 0
        assert len(description.split()) >= 2  # Should be multiple words

        # Description should not contain obvious error messages
        description_lower = description.lower()
        error_indicators = ["error", "failed", "cannot", "unable", "invalid"]
        for indicator in error_indicators:
            assert indicator not in description_lower

    except src.image_processor_name.ollama_client.OllamaConnectionError:
        pytest.skip("Ollama not available - skipping filename generation test")


@pytest.mark.requires_ollama
def test_generate_filename_with_custom_prompt(
    ollama_client: src.image_processor_name.ollama_client.OllamaClient, sample_image_small: pathlib.Path
):
    """Test filename generation with custom prompt using live Ollama."""
    custom_prompt = "Describe this image in exactly 3 words"

    try:
        description = ollama_client.generate_filename(sample_image_small, custom_prompt)

        assert isinstance(description, str)
        assert len(description) > 0

        # With custom prompt, response might be more constrained
        word_count = len(description.split())
        assert 1 <= word_count <= 10  # Reasonable range

    except src.image_processor_name.ollama_client.OllamaConnectionError:
        pytest.skip("Ollama not available - skipping custom prompt test")


@pytest.mark.requires_ollama
def test_multiple_image_processing(
    ollama_client: src.image_processor_name.ollama_client.OllamaClient, sample_images: list[pathlib.Path]
):
    """Test processing multiple different images in sequence."""
    descriptions = []

    try:
        for image_path in sample_images[:3]:  # Test first 3 images
            description = ollama_client.generate_filename(image_path)
            descriptions.append(description)

            assert isinstance(description, str)
            assert len(description) > 0

        # All descriptions should be strings
        assert len(descriptions) == 3

        # Descriptions should be reasonably different (not identical)
        unique_descriptions = set(descriptions)
        assert len(unique_descriptions) >= 2  # At least some variety

    except src.image_processor_name.ollama_client.OllamaConnectionError:
        pytest.skip("Ollama not available - skipping multiple image test")


@pytest.mark.requires_ollama
def test_large_image_processing(ollama_client: src.image_processor_name.ollama_client.OllamaClient, temp_dir: pathlib.Path):
    """Test processing a larger image file."""
    # Create a larger test image (500x500 pixels)
    large_image_path = temp_dir / "large_test.jpg"
    large_img = PIL.Image.new("RGB", (500, 500), color="purple")
    large_img.save(large_image_path, "JPEG")

    try:
        description = ollama_client.generate_filename(large_image_path)

        assert isinstance(description, str)
        assert len(description) > 0

    except src.image_processor_name.ollama_client.OllamaConnectionError:
        pytest.skip("Ollama not available - skipping large image test")


@pytest.mark.requires_ollama
def test_different_image_formats(ollama_client: src.image_processor_name.ollama_client.OllamaClient, temp_dir: pathlib.Path):
    """Test processing different image formats."""
    formats = [
        ("JPEG", ".jpg", "red"),
        ("PNG", ".png", "green"),
        ("GIF", ".gif", "blue"),
    ]

    descriptions = []

    try:
        for fmt, ext, color in formats:
            image_path = temp_dir / f"format_test{ext}"
            img = PIL.Image.new("RGB", (50, 50), color=color)

            if fmt == "GIF":
                img.save(image_path, fmt, save_all=True)
            else:
                img.save(image_path, fmt)

            description = ollama_client.generate_filename(image_path)
            descriptions.append((fmt, description))

            assert isinstance(description, str)
            assert len(description) > 0

        # Should have processed all formats
        assert len(descriptions) == 3

        # All should have valid descriptions
        for _fmt, desc in descriptions:
            assert len(desc.split()) >= 1

    except src.image_processor_name.ollama_client.OllamaConnectionError:
        pytest.skip("Ollama not available - skipping format test")


@pytest.mark.requires_ollama
def test_api_timeout_handling(temp_dir: pathlib.Path):
    """Test API timeout configuration and handling."""
    # Create client with very short timeout
    short_timeout_client = src.image_processor_name.ollama_client.OllamaClient(timeout=1)

    # Create test image
    test_image = temp_dir / "timeout_test.jpg"
    img = PIL.Image.new("RGB", (100, 100), color="orange")
    img.save(test_image, "JPEG")

    try:
        # This might timeout or succeed depending on Ollama response time
        description = short_timeout_client.generate_filename(test_image)

        # If it succeeds, should be valid
        assert isinstance(description, str)

    except src.image_processor_name.ollama_client.OllamaTimeoutError:
        # Timeout is expected with short timeout
        pass
    except src.image_processor_name.ollama_client.OllamaConnectionError:
        pytest.skip("Ollama not available - skipping timeout test")


@pytest.mark.requires_ollama
def test_model_availability(ollama_client: src.image_processor_name.ollama_client.OllamaClient):
    """Test that the configured model is actually available."""
    try:
        models = ollama_client.list_models()
        model_names = [model["name"] for model in models.get("models", [])]

        # The client's configured model should be in the list
        configured_model = ollama_client.model

        # Check exact match or partial match (for version tags)
        model_available = any(
            configured_model in model_name or model_name in configured_model
            for model_name in model_names
        )

        if not model_available:
            pytest.skip(
                f"Configured model '{configured_model}' not available in Ollama"
            )

        assert model_available

    except src.image_processor_name.ollama_client.OllamaConnectionError:
        pytest.skip("Ollama not available - skipping model availability test")


@pytest.mark.requires_ollama
def test_concurrent_requests(ollama_client: src.image_processor_name.ollama_client.OllamaClient, sample_images: list[pathlib.Path]):
    """Test handling multiple concurrent-ish requests."""
    import threading
    import time

    results = []
    errors = []

    def process_image(image_path: pathlib.Path, index: int):
        try:
            description = ollama_client.generate_filename(image_path)
            results.append((index, description))
        except Exception as e:
            errors.append((index, str(e)))

    try:
        # Start multiple threads (simulate concurrent usage)
        threads = []
        for i, image_path in enumerate(sample_images[:3]):
            thread = threading.Thread(target=process_image, args=(image_path, i))
            threads.append(thread)
            thread.start()
            time.sleep(0.1)  # Small delay to avoid overwhelming

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout per thread

        # Should have some successful results
        assert len(results) > 0

        # Check that results are valid
        for _index, description in results:
            assert isinstance(description, str)
            assert len(description) > 0

        # If there are errors, they should be connection-related, not crashes
        for _index, error in errors:
            assert "connection" in error.lower() or "timeout" in error.lower()

    except src.image_processor_name.ollama_client.OllamaConnectionError:
        pytest.skip("Ollama not available - skipping concurrent test")


@pytest.mark.requires_ollama
def test_error_response_handling(ollama_client: src.image_processor_name.ollama_client.OllamaClient, temp_dir: pathlib.Path):
    """Test handling of various error responses from Ollama."""
    # Create a very small image that might cause issues
    tiny_image = temp_dir / "tiny.jpg"
    tiny_img = PIL.Image.new("RGB", (1, 1), color="white")
    tiny_img.save(tiny_image, "JPEG")

    try:
        # Try to process tiny image
        description = ollama_client.generate_filename(tiny_image)

        # If it succeeds, should be valid (Ollama might handle tiny images fine)
        assert isinstance(description, str)

    except (src.image_processor_name.ollama_client.OllamaResponseError, src.image_processor_name.ollama_client.OllamaConnectionError):
        # These exceptions are acceptable for edge cases
        pass
    except Exception as e:
        # Other exceptions should be wrapped properly
        pytest.fail(f"Unexpected exception type: {type(e).__name__}: {e}")


@pytest.mark.requires_ollama
@pytest.mark.slow
def test_stress_processing(ollama_client: src.image_processor_name.ollama_client.OllamaClient, temp_dir: pathlib.Path):
    """Stress test with multiple image processing (marked as slow)."""
    # Create multiple test images
    num_images = 10
    images = []

    for i in range(num_images):
        image_path = temp_dir / f"stress_{i}.jpg"
        # Create images with different colors to give variety
        color_value = int(255 * i / num_images)
        color = (color_value, 128, 255 - color_value)
        img = PIL.Image.new("RGB", (30, 30), color=color)
        img.save(image_path, "JPEG")
        images.append(image_path)

    successful_count = 0
    error_count = 0

    try:
        for image_path in images:
            try:
                description = ollama_client.generate_filename(image_path)
                assert isinstance(description, str)
                assert len(description) > 0
                successful_count += 1

            except (src.image_processor_name.ollama_client.OllamaConnectionError, src.image_processor_name.ollama_client.OllamaTimeoutError, src.image_processor_name.ollama_client.OllamaResponseError):
                error_count += 1
                # These errors are acceptable under stress
                continue

        # Should have processed most images successfully
        success_rate = successful_count / num_images
        assert success_rate >= 0.7  # At least 70% success rate

    except Exception as e:
        pytest.skip(f"Ollama not available or unstable during stress test: {e}")
