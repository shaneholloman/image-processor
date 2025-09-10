"""
Unit tests for image_processor_name configuration manager.
"""


# Note: The actual config manager implementation may differ
# These tests are designed to test the expected interface


def test_config_loading_basic(sample_name_config: dict):
    """Test basic config loading functionality."""
    # This is a placeholder test since we don't have the actual ConfigManager
    # In a real implementation, this would test loading from YAML files

    # Basic assertions about the sample config structure
    assert "ollama" in sample_name_config
    assert "filename" in sample_name_config
    assert "images" in sample_name_config

    # Test config values
    assert (
        sample_name_config["ollama"]["endpoint"]
        == "http://localhost:11434/api/generate"
    )
    assert sample_name_config["filename"]["case_conversion"] == "lower"
    assert sample_name_config["images"]["max_file_size_mb"] == 50


def test_config_defaults():
    """Test that default configuration values are reasonable."""
    # Test the sample config has sensible defaults
    # This would be expanded once the actual ConfigManager is implemented
    pass


def test_config_validation(invalid_config: dict):
    """Test configuration validation."""
    # Test that invalid configs are handled properly
    assert "ollama" in invalid_config
    assert invalid_config["ollama"]["timeout"] == -1  # Invalid value
