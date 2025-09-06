"""
Configuration management for image meta processor.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from image_processor_meta import CONFIG_DIR


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""

    pass


class ConfigManager:
    """Manages application configuration from YAML files and environment variables."""

    def __init__(self, config_file: str = "app_config.yaml") -> None:
        """
        Initialize configuration manager.

        Args:
            config_file: Name of the configuration file in the config directory
        """
        self.config_file = CONFIG_DIR / config_file
        self._config: dict[str, Any] = {}
        self._load_environment()
        self._load_config()

    def _load_environment(self) -> None:
        """Load environment variables from .env file if it exists."""
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_file.exists():
            raise ConfigError(f"Configuration file not found: {self.config_file}")

        try:
            with open(self.config_file, encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}") from e
        except Exception as e:
            raise ConfigError(f"Failed to load config file: {e}") from e

    def get(self, key: str, default: Any | None = None) -> Any:
        """
        Get configuration value by key with optional default.

        Supports nested keys using dot notation (e.g., 'database.host').
        Environment variables take precedence over config file values.

        Args:
            key: Configuration key (supports dot notation for nested values)
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        # Check environment variable first (convert dots to underscores and uppercase)
        env_key = key.replace(".", "_").upper()
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._parse_env_value(env_value)

        # Navigate nested dictionary using dot notation
        keys = key.split(".")
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def _parse_env_value(self, value: str) -> Any:
        """
        Parse environment variable value to appropriate type.

        Args:
            value: String value from environment variable

        Returns:
            Parsed value (bool, int, float, or str)
        """
        # Handle boolean values
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Try to parse as int
        try:
            return int(value)
        except ValueError:
            pass

        # Try to parse as float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def require(self, key: str) -> Any:
        """
        Get required configuration value, raise error if not found.

        Args:
            key: Configuration key

        Returns:
            Configuration value

        Raises:
            ConfigError: If required key is not found
        """
        value = self.get(key)
        if value is None:
            raise ConfigError(f"Required configuration key not found: {key}")
        return value

    def reload(self) -> None:
        """Reload configuration from file and environment."""
        self._load_environment()
        self._load_config()


# Global config manager instance
config = ConfigManager()
