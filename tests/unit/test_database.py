"""
Unit tests for database management functionality.
"""

import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from image_meta_processor.db.manager import DatabaseManager
from image_meta_processor.exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
)


@pytest.fixture
def temp_db_path(temp_dir):
    """Create a temporary database path."""
    return temp_dir / "test.db"


@pytest.fixture
def db_manager(temp_db_path):
    """Create a database manager with temporary database."""
    return DatabaseManager(str(temp_db_path))


@pytest.mark.unit
class TestDatabaseInitialization:
    """Test database initialization and setup."""

    def test_database_creation(self, temp_db_path):
        """Test database file and tables are created."""
        # Database shouldn't exist initially
        assert not temp_db_path.exists()

        # Create database manager
        db_manager = DatabaseManager(str(temp_db_path))

        # Database should now exist
        assert temp_db_path.exists()

        # Tables should be created
        with db_manager.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert "images" in tables

    def test_database_connection_error(self, temp_dir):
        """Test database connection error handling."""
        # Use invalid path (directory instead of file)
        invalid_path = temp_dir / "subdir" / "invalid.db"
        invalid_path.parent.mkdir()
        invalid_path.mkdir()  # Create as directory

        with pytest.raises(DatabaseConnectionError):
            DatabaseManager(str(invalid_path))


@pytest.mark.unit
class TestDatabaseOperations:
    """Test basic database operations."""

    def test_save_description_new(self, db_manager):
        """Test saving new description."""
        file_path = "/test/image.jpg"
        description = "Test description"

        result = db_manager.save_description(file_path, description)
        assert result is True

        # Verify saved
        retrieved = db_manager.get_description(file_path)
        assert retrieved == description

    def test_save_description_update(self, db_manager):
        """Test updating existing description."""
        file_path = "/test/image.jpg"
        original_desc = "Original description"
        updated_desc = "Updated description"

        # Save original
        db_manager.save_description(file_path, original_desc)

        # Update
        db_manager.save_description(file_path, updated_desc)

        # Verify updated
        retrieved = db_manager.get_description(file_path)
        assert retrieved == updated_desc

    def test_get_description_not_found(self, db_manager):
        """Test getting non-existent description."""
        result = db_manager.get_description("/nonexistent/image.jpg")
        assert result is None

    def test_delete_description(self, db_manager):
        """Test deleting description."""
        file_path = "/test/image.jpg"
        description = "Test description"

        # Save first
        db_manager.save_description(file_path, description)
        assert db_manager.get_description(file_path) is not None

        # Delete
        result = db_manager.delete_description(file_path)
        assert result is True

        # Verify deleted
        assert db_manager.get_description(file_path) is None

    def test_delete_description_not_found(self, db_manager):
        """Test deleting non-existent description."""
        result = db_manager.delete_description("/nonexistent/image.jpg")
        assert result is False

    def test_count_records(self, db_manager):
        """Test counting database records."""
        assert db_manager.count_records() == 0

        # Add records
        db_manager.save_description("/test/image1.jpg", "Description 1")
        db_manager.save_description("/test/image2.jpg", "Description 2")

        assert db_manager.count_records() == 2

    def test_get_all_descriptions(self, db_manager):
        """Test getting all descriptions."""
        # Add test data
        descriptions = [
            ("/test/image1.jpg", "Description 1"),
            ("/test/image2.jpg", "Description 2"),
        ]

        for file_path, desc in descriptions:
            db_manager.save_description(file_path, desc)

        # Get all
        all_descriptions = db_manager.get_all_descriptions()

        assert len(all_descriptions) == 2
        file_paths = [record["file_path"] for record in all_descriptions]
        assert "/test/image1.jpg" in file_paths
        assert "/test/image2.jpg" in file_paths


@pytest.mark.unit
class TestDatabaseErrorHandling:
    """Test database error handling."""

    def test_save_description_database_error(self, db_manager):
        """Test save operation with database error."""
        with patch.object(db_manager, "connection") as mock_conn:
            mock_conn.side_effect = sqlite3.Error("Database error")

            with pytest.raises(DatabaseOperationError):
                db_manager.save_description("/test/image.jpg", "Description")

    def test_get_description_database_error(self, db_manager):
        """Test get operation with database error."""
        with patch.object(db_manager, "connection") as mock_conn:
            mock_conn.side_effect = sqlite3.Error("Database error")

            with pytest.raises(DatabaseOperationError):
                db_manager.get_description("/test/image.jpg")

    def test_connection_context_manager_rollback(self, db_manager):
        """Test connection context manager handles errors properly."""
        with patch("sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.side_effect = sqlite3.Error("Test error")

            with pytest.raises(DatabaseConnectionError):
                with db_manager.connection() as conn:
                    conn.cursor()

            # Should have called rollback
            mock_conn.rollback.assert_called_once()


@pytest.mark.unit
class TestDatabaseBackup:
    """Test database backup functionality."""

    def test_backup_database(self, db_manager, temp_dir):
        """Test database backup creation."""
        # Add some data
        db_manager.save_description("/test/image.jpg", "Test description")

        # Create backup
        backup_path = temp_dir / "backup.db"
        db_manager.backup_database(str(backup_path))

        # Verify backup exists and contains data
        assert backup_path.exists()

        backup_manager = DatabaseManager(str(backup_path))
        assert backup_manager.count_records() == 1
        assert backup_manager.get_description("/test/image.jpg") == "Test description"

    def test_backup_database_error(self, db_manager, temp_dir):
        """Test backup with database error."""
        backup_path = temp_dir / "readonly_dir"
        backup_path.mkdir(mode=0o444)  # Read-only directory
        backup_file = backup_path / "backup.db"

        with pytest.raises(DatabaseOperationError):
            db_manager.backup_database(str(backup_file))
