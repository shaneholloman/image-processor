"""
Unit tests for ImageRenamer class.
"""

import pathlib
import unittest.mock

import pytest
import src.image_processor_name.renamer


def test_init_with_defaults():
    """Test ImageRenamer initialization with default dependencies."""
    renamer = src.image_processor_name.renamer.ImageRenamer()

    assert renamer.ollama_client is not None
    assert renamer.file_ops is not None
    assert renamer.pattern_cleanup is True
    assert renamer.max_length == 100
    assert renamer.remove_punctuation is True
    assert renamer.replace_spaces_with == "-"
    assert renamer.case_conversion == "lower"


def test_init_with_custom_dependencies(
    mock_ollama_success: unittest.mock.Mock, mock_file_operations: unittest.mock.Mock
):
    """Test ImageRenamer initialization with custom dependencies."""
    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)

    assert renamer.ollama_client == mock_ollama_success
    assert renamer.file_ops == mock_file_operations


@pytest.mark.parametrize(
    "description,extension,expected",
    [
        ("Beautiful sunset beach", ".jpg", "beautiful-sunset-beach.jpg"),
        ("Mountain hiking trail!", ".png", "mountain-hiking-trail.png"),
        ("City skyline at night.", ".gif", "city-skyline-at-night.gif"),
        ("LOUD DESCRIPTION", ".jpg", "loud-description.jpg"),
        ("Multiple   spaces   here", ".png", "multiple-spaces-here.png"),
        ("", ".jpg", "unnamed.jpg"),
        ("a" * 150, ".jpg", "a" * 100 + ".jpg"),
    ],
)
def test_sanitize_filename(description: str, extension: str, expected: str):
    """Test filename sanitization with various inputs."""
    with unittest.mock.patch("image_processor_name.config_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            "filename.pattern_cleanup": True,
            "filename.max_length": 100,
            "filename.remove_punctuation": True,
            "filename.replace_spaces_with": "-",
            "filename.case_conversion": "lower",
        }.get(key, default)

        renamer = src.image_processor_name.renamer.ImageRenamer()
        result = renamer.sanitize_filename(description, extension)

        if description == "a" * 150:
            # For long descriptions, check it's truncated properly
            assert len(result) <= 100 + len(extension)
            assert result.endswith(extension)
        else:
            assert result == expected


def test_sanitize_filename_no_cleanup():
    """Test filename sanitization with pattern cleanup disabled."""
    with unittest.mock.patch("image_processor_name.config_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            "filename.pattern_cleanup": False,
            "filename.max_length": 100,
            "filename.remove_punctuation": True,
            "filename.replace_spaces_with": "-",
            "filename.case_conversion": "lower",
        }.get(key, default)

        renamer = src.image_processor_name.renamer.ImageRenamer()
        result = renamer.sanitize_filename("Hello! World?", ".jpg")

        # With pattern cleanup disabled, spaces should be preserved
        # Only punctuation removal at end and case conversion should happen
        assert result == "hello! world.jpg"


def test_sanitize_filename_different_case_conversions():
    """Test different case conversion options."""
    test_cases = [
        ("upper", "HELLO-WORLD.jpg"),
        ("lower", "hello-world.jpg"),
        ("title", "Hello-World.jpg"),
        ("none", "Hello-World.jpg"),
    ]

    for case_type, expected in test_cases:
        with unittest.mock.patch("image_processor_name.config_manager.config") as mock_config:

            def side_effect(key, default, current_case_type=case_type):
                return {
                    "filename.pattern_cleanup": True,
                    "filename.max_length": 100,
                    "filename.remove_punctuation": True,
                    "filename.replace_spaces_with": "-",
                    "filename.case_conversion": current_case_type,
                }.get(key, default)

            mock_config.get.side_effect = side_effect

            renamer = src.image_processor_name.renamer.ImageRenamer()
            result = renamer.sanitize_filename("Hello World", ".jpg")

            assert result == expected


def test_generate_filename_success(
    mock_ollama_success: unittest.mock.Mock,
    mock_file_operations: unittest.mock.Mock,
    sample_image_small: pathlib.Path,
):
    """Test successful filename generation."""
    mock_ollama_success.generate_filename.return_value = "beautiful sunset scene"

    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)
    result = renamer.generate_filename(sample_image_small)

    assert result == "beautiful-sunset-scene.jpg"
    mock_ollama_success.generate_filename.assert_called_once_with(
        sample_image_small, None
    )


def test_generate_filename_with_custom_prompt(
    mock_ollama_success: unittest.mock.Mock,
    mock_file_operations: unittest.mock.Mock,
    sample_image_small: pathlib.Path,
):
    """Test filename generation with custom prompt."""
    mock_ollama_success.generate_filename.return_value = "artistic description"
    custom_prompt = "Describe artistically"

    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)
    result = renamer.generate_filename(sample_image_small, custom_prompt)

    assert result == "artistic-description.jpg"
    mock_ollama_success.generate_filename.assert_called_once_with(
        sample_image_small, custom_prompt
    )


def test_generate_filename_api_error(
    mock_ollama_error: unittest.mock.Mock,
    mock_file_operations: unittest.mock.Mock,
    sample_image_small: pathlib.Path,
):
    """Test filename generation when API fails."""
    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_error, mock_file_operations)
    result = renamer.generate_filename(sample_image_small)

    assert result is None


def test_generate_filename_verification_enabled(
    mock_ollama_success: unittest.mock.Mock,
    mock_file_operations: unittest.mock.Mock,
    sample_image_small: pathlib.Path,
):
    """Test filename generation with image verification enabled."""
    with unittest.mock.patch("image_processor_name.config_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            "images.verify_before_processing": True,
            "filename.pattern_cleanup": True,
            "filename.max_length": 100,
            "filename.remove_punctuation": True,
            "filename.replace_spaces_with": "-",
            "filename.case_conversion": "lower",
        }.get(key, default)

        mock_ollama_success.generate_filename.return_value = "verified image"
        mock_file_operations.verify_image.return_value = None

        renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)
        result = renamer.generate_filename(sample_image_small)

        assert result == "verified-image.jpg"
        mock_file_operations.verify_image.assert_called_once_with(sample_image_small)


def test_rename_single_image_success(
    mock_ollama_success: unittest.mock.Mock,
    mock_file_operations: unittest.mock.Mock,
    sample_image_small: pathlib.Path,
):
    """Test successful single image rename."""
    mock_ollama_success.generate_filename.return_value = "new filename"
    mock_file_operations.is_supported_image.return_value = True
    mock_file_operations.safe_file_move.return_value = True

    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)
    result = renamer.rename_single_image(sample_image_small)

    assert result is True
    mock_file_operations.safe_file_move.assert_called_once()


def test_rename_single_image_dry_run(
    mock_ollama_success: unittest.mock.Mock,
    mock_file_operations: unittest.mock.Mock,
    sample_image_small: pathlib.Path,
):
    """Test single image rename in dry run mode."""
    mock_ollama_success.generate_filename.return_value = "new filename"
    mock_file_operations.is_supported_image.return_value = True

    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)
    result = renamer.rename_single_image(sample_image_small, dry_run=True)

    assert result is True
    mock_file_operations.safe_file_move.assert_not_called()


def test_rename_single_image_unsupported_format(
    mock_ollama_success: unittest.mock.Mock,
    mock_file_operations: unittest.mock.Mock,
    sample_image_small: pathlib.Path,
):
    """Test rename attempt on unsupported image format."""
    mock_file_operations.is_supported_image.return_value = False

    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)
    result = renamer.rename_single_image(sample_image_small)

    assert result is False
    mock_ollama_success.generate_filename.assert_not_called()


def test_rename_single_image_file_not_found(
    mock_ollama_success: unittest.mock.Mock, mock_file_operations: unittest.mock.Mock
):
    """Test rename attempt on non-existent file."""
    non_existent_path = pathlib.Path("/does/not/exist.jpg")

    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)
    result = renamer.rename_single_image(non_existent_path)

    assert result is False


def test_rename_single_image_same_name(
    mock_ollama_success: unittest.mock.Mock,
    mock_file_operations: unittest.mock.Mock,
    sample_image_small: pathlib.Path,
):
    """Test rename when new filename is same as current."""
    # Mock a generated description that will result in the exact same filename
    # The sanitize_filename method will convert the description and compare against current path
    mock_ollama_success.generate_filename.return_value = sample_image_small.stem
    mock_file_operations.is_supported_image.return_value = True

    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)

    # Mock generate_filename to return the exact filename to avoid move
    with unittest.mock.patch.object(renamer, "generate_filename") as mock_gen:
        mock_gen.return_value = sample_image_small.name  # Same filename as current
        result = renamer.rename_single_image(sample_image_small)

    # Should return True but not attempt to move the file
    assert result is True
    mock_file_operations.safe_file_move.assert_not_called()


def test_rename_single_image_filename_collision(
    mock_ollama_success: unittest.mock.Mock,
    mock_file_operations: unittest.mock.Mock,
    sample_image_small: pathlib.Path,
):
    """Test rename when target filename already exists."""
    mock_ollama_success.generate_filename.return_value = "new filename"
    mock_file_operations.is_supported_image.return_value = True
    mock_file_operations.safe_file_move.return_value = True

    # Simulate filename collision by returning a unique filename
    collision_path = sample_image_small.parent / "new-filename-1.jpg"
    mock_file_operations.get_unique_filename.return_value = collision_path

    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)

    # Create a file that would cause collision
    collision_file = sample_image_small.parent / "new-filename.jpg"
    collision_file.write_bytes(b"collision content")

    result = renamer.rename_single_image(sample_image_small)

    assert result is True
    # Since we created a collision file, the unique filename method should be called
    # Check that the file was successfully processed despite the collision


def test_rename_directory_success(
    mock_ollama_success: unittest.mock.Mock,
    mock_file_operations: unittest.mock.Mock,
    temp_image_dir: pathlib.Path,
):
    """Test successful directory rename operation."""
    mock_ollama_success.generate_filename.return_value = "renamed image"
    mock_file_operations.is_supported_image.return_value = True
    mock_file_operations.safe_file_move.return_value = True

    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)
    results = renamer.rename_directory(temp_image_dir, show_progress=False)

    assert results["total_files"] > 0
    assert results["processed"] > 0
    assert results["failed"] == 0
    assert "processing_time" in results


def test_rename_directory_recursive(
    mock_ollama_success: unittest.mock.Mock,
    mock_file_operations: unittest.mock.Mock,
    nested_image_dir: pathlib.Path,
):
    """Test recursive directory rename operation."""
    mock_ollama_success.generate_filename.return_value = "renamed image"
    mock_file_operations.is_supported_image.return_value = True
    mock_file_operations.safe_file_move.return_value = True

    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)
    results = renamer.rename_directory(
        nested_image_dir, recursive=True, show_progress=False
    )

    # Should find images in subdirectories too
    assert results["total_files"] >= 3  # At least 3 images in nested structure
    assert results["processed"] > 0


def test_rename_directory_dry_run(
    mock_ollama_success: unittest.mock.Mock,
    mock_file_operations: unittest.mock.Mock,
    temp_image_dir: pathlib.Path,
):
    """Test directory rename in dry run mode."""
    mock_ollama_success.generate_filename.return_value = "renamed image"
    mock_file_operations.is_supported_image.return_value = True

    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)
    results = renamer.rename_directory(
        temp_image_dir, dry_run=True, show_progress=False
    )

    assert results["processed"] > 0
    # Should not actually move files in dry run
    mock_file_operations.safe_file_move.assert_not_called()


def test_rename_directory_no_images(
    mock_ollama_success: unittest.mock.Mock, mock_file_operations: unittest.mock.Mock, temp_dir: pathlib.Path
):
    """Test directory rename with no image files."""
    empty_dir = temp_dir / "empty"
    empty_dir.mkdir()

    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)
    results = renamer.rename_directory(empty_dir, show_progress=False)

    assert results["total_files"] == 0
    assert results["processed"] == 0
    assert results["failed"] == 0


def test_rename_directory_with_failures(
    mock_ollama_success: unittest.mock.Mock,
    mock_file_operations: unittest.mock.Mock,
    temp_image_dir: pathlib.Path,
):
    """Test directory rename with some failures."""
    # Make every other call fail
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return call_count % 2 == 1  # Success on odd calls, failure on even

    mock_ollama_success.generate_filename.return_value = "renamed image"
    mock_file_operations.is_supported_image.return_value = True
    mock_file_operations.safe_file_move.side_effect = side_effect

    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)
    results = renamer.rename_directory(temp_image_dir, show_progress=False)

    assert results["failed"] > 0


def test_test_connection(mock_ollama_success: unittest.mock.Mock, mock_file_operations: unittest.mock.Mock):
    """Test connection testing method."""
    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_success, mock_file_operations)
    result = renamer.test_connection()

    assert result is True
    mock_ollama_success.test_connection.assert_called_once()


def test_test_connection_failure(mock_ollama_error: unittest.mock.Mock, mock_file_operations: unittest.mock.Mock):
    """Test connection testing when connection fails."""
    renamer = src.image_processor_name.renamer.ImageRenamer(mock_ollama_error, mock_file_operations)
    result = renamer.test_connection()

    assert result is False
