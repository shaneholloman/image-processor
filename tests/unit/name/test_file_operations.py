"""
Unit tests for FileOperations class.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from src.image_processor_name.tools.file_operations import (
    FileOperationError,
    FileOperations,
    ImageCorrupted,
)


def test_init_with_defaults():
    """Test FileOperations initialization with default configuration."""
    file_ops = FileOperations()

    assert file_ops.max_retries == 3
    assert file_ops.move_delay == 0.5
    assert file_ops.backup_originals is False
    assert file_ops.confirm_overwrites is True


@pytest.mark.parametrize(
    "extension,expected",
    [
        (".jpg", True),
        (".jpeg", True),
        (".png", True),
        (".gif", True),
        (".bmp", True),
        (".JPG", True),  # Case insensitive
        (".JPEG", True),
        (".txt", False),
        (".pdf", False),
        (".mp4", False),
        ("", False),
    ],
)
def test_is_supported_image(extension: str, expected: bool):
    """Test image format support detection."""
    file_ops = FileOperations()
    test_path = Path(f"test_file{extension}")

    result = file_ops.is_supported_image(test_path)
    assert result == expected


def test_verify_image_valid(sample_image_small: Path):
    """Test image verification with valid image."""
    file_ops = FileOperations()

    # Should not raise any exception
    file_ops.verify_image(sample_image_small)


def test_verify_image_not_found():
    """Test image verification with non-existent file."""
    file_ops = FileOperations()

    with pytest.raises(FileOperationError, match="Image file not found"):
        file_ops.verify_image(Path("/does/not/exist.jpg"))


def test_verify_image_corrupted(corrupted_image: Path):
    """Test image verification with corrupted file."""
    file_ops = FileOperations()

    with pytest.raises(ImageCorrupted, match="Image verification failed"):
        file_ops.verify_image(corrupted_image)


def test_verify_image_too_large(temp_dir: Path):
    """Test image verification with oversized file."""
    # Create a file that exceeds the maximum size
    large_file = temp_dir / "huge.jpg"
    # Write more than 50MB of data (default limit)
    large_file.write_bytes(b"x" * (51 * 1024 * 1024))

    file_ops = FileOperations()

    with pytest.raises(FileOperationError, match="Image file too large"):
        file_ops.verify_image(large_file)


def test_safe_file_move_success(sample_image_small: Path, temp_dir: Path):
    """Test successful file move operation."""
    dest_path = temp_dir / "moved_image.jpg"

    file_ops = FileOperations()
    result = file_ops.safe_file_move(sample_image_small, dest_path)

    assert result is True
    assert dest_path.exists()
    assert not sample_image_small.exists()


def test_safe_file_move_destination_exists_no_overwrite(
    sample_image_small: Path, sample_image_png: Path
):
    """Test file move when destination exists and confirm_overwrites is True."""
    # Convert PNG to JPG path to simulate collision
    dest_path = sample_image_png.with_suffix(".jpg")
    dest_path.write_bytes(b"existing content")

    with patch("src.image_processor_name.tools.config_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            "file_operations.confirm_overwrites": True
        }.get(key, default)

        file_ops = FileOperations()

        # Should raise exception when destination exists and confirm_overwrites is True
        with pytest.raises(FileOperationError, match="Destination file already exists"):
            file_ops.safe_file_move(sample_image_small, dest_path)

        assert sample_image_small.exists()  # Source should still exist


def test_safe_file_move_with_retries(sample_image_small: Path, temp_dir: Path):
    """Test file move with retry mechanism."""
    dest_path = temp_dir / "moved_with_retries.jpg"

    with patch("shutil.copy2") as mock_copy:
        # Fail first two attempts, succeed on third
        mock_copy.side_effect = [
            OSError("Permission denied"),
            OSError("Busy"),
            None,
        ]

        file_ops = FileOperations()

        with patch("time.sleep") as mock_sleep:
            result = file_ops.safe_file_move(sample_image_small, dest_path)

            assert result is True
            assert mock_copy.call_count == 3
            assert mock_sleep.call_count >= 2  # Sleep between retries


def test_safe_file_move_max_retries_exceeded(sample_image_small: Path, temp_dir: Path):
    """Test file move when max retries are exceeded."""
    dest_path = temp_dir / "failed_move.jpg"

    with patch("shutil.copy2") as mock_copy:
        mock_copy.side_effect = OSError("Persistent error")

        file_ops = FileOperations()

        with pytest.raises(FileOperationError, match="File move failed after"):
            file_ops.safe_file_move(sample_image_small, dest_path)

        assert mock_copy.call_count == 3  # Default retry count


def test_safe_file_move_with_backup(sample_image_small: Path, temp_dir: Path):
    """Test file move with backup creation."""
    dest_path = temp_dir / "move_with_backup.jpg"

    # Don't create an existing destination file for this test
    # The backup creation is for the source file, not destination

    with patch("src.image_processor_name.tools.config_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key, default: {
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
            "file_operations.backup_originals": True,
            "file_operations.confirm_overwrites": False,
        }.get(key, default)

        file_ops = FileOperations()
        result = file_ops.safe_file_move(sample_image_small, dest_path)

        assert result is True
        assert dest_path.exists()
        assert not sample_image_small.exists()  # Source should be moved


def test_get_unique_filename_no_collision(temp_dir: Path):
    """Test unique filename generation when no collision exists."""
    target_path = temp_dir / "unique_file.jpg"

    file_ops = FileOperations()
    result = file_ops.get_unique_filename(target_path)

    assert result == target_path


def test_get_unique_filename_with_collision(temp_dir: Path):
    """Test unique filename generation when collision exists."""
    target_path = temp_dir / "colliding_file.jpg"
    target_path.write_bytes(b"existing content")  # Create collision

    file_ops = FileOperations()
    result = file_ops.get_unique_filename(target_path)

    assert result != target_path
    assert result.parent == target_path.parent
    assert result.suffix == target_path.suffix
    assert not result.exists()

    # Should have format like "colliding_file_1.jpg"
    assert "_1" in result.stem or "-1" in result.stem


def test_get_unique_filename_multiple_collisions(temp_dir: Path):
    """Test unique filename generation with multiple collisions."""
    base_path = temp_dir / "multi_collision.jpg"

    # Create multiple existing files
    for i in range(5):
        if i == 0:
            collision_path = base_path
        else:
            collision_path = base_path.with_stem(f"{base_path.stem}_{i}")
        collision_path.write_bytes(b"existing content")

    file_ops = FileOperations()
    result = file_ops.get_unique_filename(base_path)

    assert not result.exists()
    assert "5" in result.stem or "_5" in result.stem


@pytest.mark.parametrize(
    "file_size_mb,max_size_mb,should_pass",
    [
        (10, 50, True),  # Under limit
        (50, 50, True),  # At limit
        (51, 50, False),  # Over limit
        (1, 1, True),  # Exactly at limit
    ],
)
def test_check_file_size_limits(
    temp_dir: Path, file_size_mb: int, max_size_mb: int, should_pass: bool
):
    """Test file size validation with different limits."""
    test_file = temp_dir / "size_test.jpg"
    test_file.write_bytes(b"x" * (file_size_mb * 1024 * 1024))

    with patch("src.image_processor_name.tools.config_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            "images.supported_extensions": [
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".bmp",
            ],
            "images.max_file_size_mb": max_size_mb,
            "file_operations.safe_move_retries": 3,
            "file_operations.move_delay_seconds": 0.5,
            "file_operations.backup_originals": False,
            "file_operations.confirm_overwrites": True,
        }.get(key, default)

        file_ops = FileOperations()

        if should_pass:
            if file_size_mb > max_size_mb:
                # File too large
                with pytest.raises(FileOperationError, match="Image file too large"):
                    file_ops.verify_image(test_file)
            else:
                # Will fail because it's not a real image, but should pass size check
                with pytest.raises(ImageCorrupted, match="Image verification failed"):
                    file_ops.verify_image(test_file)
        else:
            with pytest.raises(FileOperationError, match="Image file too large"):
                file_ops.verify_image(test_file)


def test_file_operations_with_symlinks(sample_image_small: Path, temp_dir: Path):
    """Test file operations with symbolic links."""
    # Create a symlink to the sample image
    symlink_path = temp_dir / "image_symlink.jpg"
    symlink_path.symlink_to(sample_image_small)

    file_ops = FileOperations()

    # Should recognize as supported image
    assert file_ops.is_supported_image(symlink_path)

    # Should be able to verify through symlink
    file_ops.verify_image(symlink_path)

    # Should be able to move symlink
    dest_path = temp_dir / "moved_symlink.jpg"
    result = file_ops.safe_file_move(symlink_path, dest_path)
    assert result is True
