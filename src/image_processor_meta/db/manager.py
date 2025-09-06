"""
Database management for image descriptions.
"""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from ..exceptions import DatabaseConnectionError, DatabaseOperationError
from ..tools.config_manager import config
from ..tools.log_manager import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for image descriptions."""

    def __init__(self, db_path: str | None = None) -> None:
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(
            db_path or config.get("database.path", "image_descriptions.db")
        )
        self._ensure_database_exists()

    def _ensure_database_exists(self) -> None:
        """Ensure database file and tables exist."""
        try:
            with self.connection() as conn:
                self._create_tables(conn)
                logger.info(f"Database initialized at: {self.db_path}")
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to initialize database: {e}") from e

    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """
        Create necessary database tables.

        Args:
            conn: Database connection
        """
        cursor = conn.cursor()

        # Create images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index on file_path for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_path ON images(file_path)
        """)

        conn.commit()

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection]:
        """
        Context manager for database connections.

        Yields:
            Database connection

        Raises:
            DatabaseConnectionError: If connection fails
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseConnectionError(f"Database connection failed: {e}") from e
        finally:
            if conn:
                conn.close()

    def save_description(self, file_path: str, description: str) -> bool:
        """
        Save or update image description in database.

        Args:
            file_path: Path to image file
            description: Generated description

        Returns:
            True if operation successful

        Raises:
            DatabaseOperationError: If save operation fails
        """
        try:
            with self.connection() as conn:
                cursor = conn.cursor()

                # Use INSERT OR REPLACE to handle both new and existing records
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO images (file_path, description, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                    (file_path, description),
                )

                conn.commit()
                logger.debug(f"Saved description for: {file_path}")
                return True

        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to save description: {e}") from e

    def get_description(self, file_path: str) -> str | None:
        """
        Get description for image file.

        Args:
            file_path: Path to image file

        Returns:
            Description if found, None otherwise

        Raises:
            DatabaseOperationError: If query fails
        """
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT description FROM images WHERE file_path = ?", (file_path,)
                )

                result = cursor.fetchone()
                return result["description"] if result else None

        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to get description: {e}") from e

    def get_all_descriptions(self) -> list[dict[str, str]]:
        """
        Get all image descriptions from database.

        Returns:
            List of dictionaries containing file paths and descriptions

        Raises:
            DatabaseOperationError: If query fails
        """
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT file_path, description, created_at, updated_at 
                    FROM images 
                    ORDER BY updated_at DESC
                """)

                return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to get descriptions: {e}") from e

    def delete_description(self, file_path: str) -> bool:
        """
        Delete description for image file.

        Args:
            file_path: Path to image file

        Returns:
            True if record was deleted, False if not found

        Raises:
            DatabaseOperationError: If delete operation fails
        """
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM images WHERE file_path = ?", (file_path,))
                conn.commit()

                deleted = cursor.rowcount > 0
                if deleted:
                    logger.debug(f"Deleted description for: {file_path}")

                return deleted

        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to delete description: {e}") from e

    def count_records(self) -> int:
        """
        Get total number of records in database.

        Returns:
            Number of records

        Raises:
            DatabaseOperationError: If count query fails
        """
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM images")
                result = cursor.fetchone()
                return result["count"]

        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to count records: {e}") from e

    def backup_database(self, backup_path: str) -> None:
        """
        Create a backup of the database.

        Args:
            backup_path: Path for backup file

        Raises:
            DatabaseOperationError: If backup fails
        """
        try:
            with self.connection() as conn:
                backup_conn = sqlite3.connect(backup_path)
                conn.backup(backup_conn)
                backup_conn.close()
                logger.info(f"Database backed up to: {backup_path}")

        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Database backup failed: {e}") from e
