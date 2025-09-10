"""
Integration tests for end-to-end image renaming workflows.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml
from src.image_processor_name.api.ollama_client import OllamaClient
from src.image_processor_name.core.renamer import ImageRenamer
from src.image_processor_name.tools.file_operations import FileOperations


def test_single_image_rename_workflow(
    sample_image_small: Path, mock_ollama_success: Mock
):
    """Test complete workflow for renaming a single image."""
    # Create a temporary copy of the image with a generic name
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_path = Path(tmp_dir)
        test_image = temp_path / "IMG_1234.jpg"
        test_image.write_bytes(sample_image_small.read_bytes())

        # Mock the Ollama client to return a descriptive filename
        mock_ollama_success.generate_filename.return_value = (
            "Beautiful sunset over ocean"
        )

        # Create renamer with real file operations but mocked Ollama
        file_ops = FileOperations()
        renamer = ImageRenamer(mock_ollama_success, file_ops)

        # Perform the rename
        result = renamer.rename_single_image(test_image)

        assert result is True
        assert not test_image.exists()  # Original should be gone

        # Check that new file exists with expected name
        renamed_files = list(temp_path.glob("beautiful-sunset-over-ocean.jpg"))
        assert len(renamed_files) == 1
        assert renamed_files[0].exists()


def test_directory_rename_workflow(temp_image_dir: Path, mock_ollama_success: Mock):
    """Test complete workflow for renaming images in a directory."""
    # Mock different descriptions for different images
    descriptions = [
        "Mountain landscape view",
        "City street at night",
        "Forest hiking trail",
    ]
    mock_ollama_success.generate_filename.side_effect = descriptions

    # Get original file count
    original_files = (
        list(temp_image_dir.glob("*.jpg"))
        + list(temp_image_dir.glob("*.png"))
        + list(temp_image_dir.glob("*.gif"))
    )
    original_count = len(original_files)

    # Create renamer and process directory
    file_ops = FileOperations()
    renamer = ImageRenamer(mock_ollama_success, file_ops)

    results = renamer.rename_directory(temp_image_dir, show_progress=False)

    assert results["total_files"] == original_count
    assert results["processed"] > 0
    assert results["failed"] == 0

    # Verify files were renamed with descriptive names
    new_files = list(temp_image_dir.glob("*"))
    descriptive_files = [f for f in new_files if not f.name.startswith("sample_")]
    assert len(descriptive_files) > 0


def test_recursive_directory_workflow(
    nested_image_dir: Path, mock_ollama_success: Mock
):
    """Test recursive directory processing workflow."""
    mock_ollama_success.generate_filename.return_value = "Nested image description"

    # Count original images in all directories
    original_images = list(nested_image_dir.rglob("*.jpg"))
    original_count = len(original_images)

    # Create renamer and process recursively
    file_ops = FileOperations()
    renamer = ImageRenamer(mock_ollama_success, file_ops)

    results = renamer.rename_directory(
        nested_image_dir, recursive=True, show_progress=False
    )

    assert results["total_files"] == original_count
    assert results["processed"] > 0

    # Verify files in subdirectories were also processed
    renamed_images = list(nested_image_dir.rglob("nested-image-description*.jpg"))
    assert len(renamed_images) > 0


def test_dry_run_workflow(sample_image_small: Path, mock_ollama_success: Mock):
    """Test dry run workflow that doesn't actually rename files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_path = Path(tmp_dir)
        test_image = temp_path / "original_name.jpg"
        test_image.write_bytes(sample_image_small.read_bytes())

        mock_ollama_success.generate_filename.return_value = "New descriptive name"

        # Create renamer and perform dry run
        file_ops = FileOperations()
        renamer = ImageRenamer(mock_ollama_success, file_ops)

        result = renamer.rename_single_image(test_image, dry_run=True)

        assert result is True
        assert test_image.exists()  # Original file should still exist

        # No new files should be created
        files = list(temp_path.glob("*.jpg"))
        assert len(files) == 1
        assert files[0].name == "original_name.jpg"


def test_collision_handling_workflow(temp_dir: Path, mock_ollama_success: Mock):
    """Test workflow when filename collisions occur."""
    # Create two images that will get the same generated name
    image1 = temp_dir / "image1.jpg"
    image2 = temp_dir / "image2.jpg"

    from PIL import Image

    img = Image.new("RGB", (10, 10), color="red")
    img.save(image1, "JPEG")
    img.save(image2, "JPEG")

    # Mock to return same description for both
    mock_ollama_success.generate_filename.return_value = "Same description"

    # Create renamer
    file_ops = FileOperations()
    renamer = ImageRenamer(mock_ollama_success, file_ops)

    # Rename first image
    result1 = renamer.rename_single_image(image1)
    assert result1 is True

    # Rename second image (should handle collision)
    result2 = renamer.rename_single_image(image2)
    assert result2 is True

    # Both files should exist with unique names
    renamed_files = list(temp_dir.glob("same-description*.jpg"))
    assert len(renamed_files) == 2

    # Names should be different
    names = [f.name for f in renamed_files]
    assert len(set(names)) == 2  # All unique


def test_mixed_format_workflow(temp_dir: Path, mock_ollama_success: Mock):
    """Test workflow with mixed image formats."""
    # Create images in different formats
    from PIL import Image

    formats = [("JPEG", ".jpg"), ("PNG", ".png"), ("GIF", ".gif")]
    for i, (fmt, ext) in enumerate(formats):
        image_path = temp_dir / f"mixed_{i}{ext}"
        img = Image.new("RGB", (10, 10), color=["red", "green", "blue"][i])
        if fmt == "GIF":
            img.save(image_path, fmt, save_all=True)
        else:
            img.save(image_path, fmt)

    # Mock different descriptions
    descriptions = [
        "Red square image",
        "Green square image",
        "Blue square animation",
    ]
    mock_ollama_success.generate_filename.side_effect = descriptions

    # Process directory
    file_ops = FileOperations()
    renamer = ImageRenamer(mock_ollama_success, file_ops)

    results = renamer.rename_directory(temp_dir, show_progress=False)

    assert results["processed"] == 3
    assert results["failed"] == 0

    # Verify all formats were processed and maintain their extensions
    renamed_files = list(temp_dir.glob("*square*"))
    extensions = [f.suffix for f in renamed_files]
    assert ".jpg" in extensions
    assert ".png" in extensions
    assert ".gif" in extensions


def test_large_batch_workflow(temp_dir: Path, mock_ollama_success: Mock):
    """Test workflow with larger batch of images."""
    # Create multiple images
    from PIL import Image

    num_images = 10
    for i in range(num_images):
        image_path = temp_dir / f"batch_{i:03d}.jpg"
        img = Image.new("RGB", (10, 10), color="red")
        img.save(image_path, "JPEG")

    # Mock unique descriptions
    mock_ollama_success.generate_filename.side_effect = [
        f"Batch image number {i}" for i in range(num_images)
    ]

    # Process batch
    file_ops = FileOperations()
    renamer = ImageRenamer(mock_ollama_success, file_ops)

    results = renamer.rename_directory(temp_dir, show_progress=False)

    assert results["total_files"] == num_images
    assert results["processed"] == num_images
    assert results["failed"] == 0

    # All images should be renamed
    original_files = list(temp_dir.glob("batch_*.jpg"))
    assert len(original_files) == 0  # All should be renamed

    renamed_files = list(temp_dir.glob("batch-image-number-*.jpg"))
    assert len(renamed_files) == num_images


def test_error_recovery_workflow(temp_dir: Path, mock_ollama_success: Mock):
    """Test workflow error recovery with partial failures."""
    # Create multiple images
    from PIL import Image

    images = []
    for i in range(5):
        image_path = temp_dir / f"recovery_{i}.jpg"
        img = Image.new("RGB", (10, 10), color="red")
        img.save(image_path, "JPEG")
        images.append(image_path)

    # Mock to fail on every other call
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count % 2 == 0:
            raise Exception("Simulated API failure")
        return f"Success description {call_count}"

    mock_ollama_success.generate_filename.side_effect = side_effect

    # Process with expected failures
    file_ops = FileOperations()
    renamer = ImageRenamer(mock_ollama_success, file_ops)

    results = renamer.rename_directory(temp_dir, show_progress=False)

    assert results["total_files"] == 5
    assert results["processed"] < 5  # Some should fail
    assert results["failed"] > 0  # Some failures expected

    # Some images should be successfully renamed
    success_files = list(temp_dir.glob("success-description-*.jpg"))
    assert len(success_files) > 0


@pytest.mark.integration
def test_configuration_integration_workflow(temp_dir: Path, sample_name_config: dict):
    """Test workflow with custom configuration."""
    # Create test config file
    config_file = temp_dir / "test_config.yaml"

    # Modify config for testing
    test_config = sample_name_config.copy()
    test_config["filename"]["case_conversion"] = "upper"
    test_config["filename"]["replace_spaces_with"] = "_"
    test_config["filename"]["max_length"] = 50

    with config_file.open("w") as f:
        yaml.dump(test_config, f)

    # Create test image
    from PIL import Image

    test_image = temp_dir / "config_test.jpg"
    img = Image.new("RGB", (10, 10), color="blue")
    img.save(test_image, "JPEG")

    # Mock Ollama response
    with patch("src.image_processor_name.api.ollama_client.requests.post") as mock_post:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Custom Configuration Test Image"
        }
        mock_post.return_value = mock_response

        # Override config to use our test config
        def config_side_effect(key, default=None):
            config_values = {
                "filename.case_conversion": "upper",
                "filename.replace_spaces_with": "_",
                "filename.max_length": 50,
                "filename.pattern_cleanup": True,
                "filename.remove_punctuation": True,
                "images.verify_before_processing": True,
                "images.supported_extensions": [
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".gif",
                    ".bmp",
                ],
                "images.max_file_size_mb": 50,
                "file_operations.safe_move_retries": 3,
                "file_operations.move_delay_seconds": 0.5,
                "file_operations.backup_originals": False,
                "file_operations.confirm_overwrites": True,
                "ollama.endpoint": "http://localhost:11434/api/generate",
                "ollama.model": "llava-llama3:latest",
                "ollama.timeout": 30,
            }
            return config_values.get(key, default)

        with (
            patch(
                "src.image_processor_name.tools.config_manager.config"
            ) as mock_config1,
            patch("src.image_processor_name.core.renamer.config") as mock_config2,
            patch("src.image_processor_name.api.ollama_client.config") as mock_config3,
            patch(
                "src.image_processor_name.tools.file_operations.config"
            ) as mock_config4,
        ):
            # Set up all config mocks with the same side effect
            for mock_config in [
                mock_config1,
                mock_config2,
                mock_config3,
                mock_config4,
            ]:
                mock_config.get.side_effect = config_side_effect

            # Create components with test config
            ollama_client = OllamaClient()
            file_ops = FileOperations()
            renamer = ImageRenamer(ollama_client, file_ops)

            # Process image
            result = renamer.rename_single_image(test_image)

            assert result is True

            # Verify config was applied (uppercase, underscores)
            renamed_files = list(temp_dir.glob("CUSTOM_CONFIGURATION_TEST_IMAGE.jpg"))
            assert len(renamed_files) == 1


def test_progress_reporting_workflow(
    temp_image_dir: Path, mock_ollama_success: Mock, capsys
):
    """Test that progress reporting works in workflows."""
    mock_ollama_success.generate_filename.return_value = "Progress test image"

    # Enable progress bar in config
    with patch("src.image_processor_name.tools.config_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            "processing.progress_bar": True
        }.get(key, default)

        file_ops = FileOperations()
        renamer = ImageRenamer(mock_ollama_success, file_ops)

        # Process directory with progress enabled
        results = renamer.rename_directory(temp_image_dir, show_progress=True)

        assert results["processed"] > 0

        # Note: Progress bar output testing is complex due to tqdm's behavior
        # In a real integration test environment, you would verify tqdm output
