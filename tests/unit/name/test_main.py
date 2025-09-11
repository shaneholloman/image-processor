"""
Unit tests for image_processor_name main CLI module.
"""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import src.image_processor_name.exceptions as exceptions
import src.image_processor_name.main as main_module


def test_create_argument_parser_basic():
    """Test basic argument parser creation."""
    parser = main_module.create_argument_parser()

    assert isinstance(parser, argparse.ArgumentParser)
    assert parser.description is not None
    assert "AI-powered image filename generator" in parser.description


def test_parse_global_options():
    """Test parsing of global options."""
    parser = main_module.create_argument_parser()

    # Test dry-run option
    args = parser.parse_args(["--dry-run", "rename", "test.jpg"])
    assert args.dry_run is True

    # Test verbose option
    args = parser.parse_args(["-v", "rename", "test.jpg"])
    assert args.verbose is True

    # Test quiet option
    args = parser.parse_args(["-q", "rename", "test.jpg"])
    assert args.quiet is True


def test_parse_rename_command():
    """Test parsing of rename command."""
    parser = main_module.create_argument_parser()

    # Basic rename command
    args = parser.parse_args(["rename", "/path/to/images"])
    assert args.command == "rename"
    assert args.path == "/path/to/images"
    assert args.recursive is False

    # Recursive rename
    args = parser.parse_args(["rename", "-r", "/path/to/images"])
    assert args.recursive is True

    # Custom prompt
    args = parser.parse_args(["rename", "--prompt", "Custom prompt", "test.jpg"])
    assert args.prompt == "Custom prompt"


def test_parse_test_connection():
    """Test parsing of test connection command."""
    parser = main_module.create_argument_parser()

    args = parser.parse_args(["--check-connection"])
    assert args.check_connection is True


def test_parse_list_models():
    """Test parsing of list models command."""
    parser = main_module.create_argument_parser()

    args = parser.parse_args(["--list-models"])
    assert args.list_models is True


def test_parse_version():
    """Test version argument handling."""
    parser = main_module.create_argument_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--version"])


def test_test_ollama_connection_success(mock_ollama_success: Mock, capsys):
    """Test successful connection test."""
    mock_ollama_success.endpoint = "http://localhost:11434/api/generate"
    mock_ollama_success.model = "llava-llama3:latest"

    result = main_module.check_ollama_connection(mock_ollama_success)

    assert result is True
    captured = capsys.readouterr()
    assert "Successfully connected to Ollama" in captured.out
    assert "Using model: llava-llama3:latest" in captured.out


def test_test_ollama_connection_failure(mock_ollama_error: Mock, capsys):
    """Test failed connection test."""
    mock_ollama_error.endpoint = "http://localhost:11434/api/generate"

    result = main_module.check_ollama_connection(mock_ollama_error)

    assert result is False
    captured = capsys.readouterr()
    assert "Failed to connect to Ollama" in captured.out
    assert "Troubleshooting:" in captured.out


def test_handle_rename_command_file_success(sample_image_small: Path):
    """Test successful rename of single file."""
    args = MagicMock()
    args.path = str(sample_image_small)
    args.dry_run = False
    args.recursive = False
    args.quiet = False

    with (
        patch("src.image_processor_name.main.OllamaClient"),
        patch("src.image_processor_name.main.FileOperations") as mock_file_ops_class,
        patch("src.image_processor_name.main.ImageRenamer") as mock_renamer_class,
    ):
        mock_renamer = Mock()
        mock_renamer.test_connection.return_value = True
        mock_renamer.rename_single_image.return_value = True
        mock_renamer_class.return_value = mock_renamer

        mock_file_ops = Mock()
        mock_file_ops.is_supported_image.return_value = True
        mock_file_ops_class.return_value = mock_file_ops

        result = main_module.handle_rename_command(args)

        assert result == 0
        mock_renamer.rename_single_image.assert_called_once()


def test_handle_rename_command_file_not_found():
    """Test rename command with non-existent file."""
    args = MagicMock()
    args.path = "/does/not/exist.jpg"
    args.dry_run = False

    result = main_module.handle_rename_command(args)

    assert result == 1


def test_handle_rename_command_unsupported_format(temp_dir: Path):
    """Test rename command with unsupported file format."""
    unsupported_file = temp_dir / "document.txt"
    unsupported_file.write_text("Not an image")

    args = MagicMock()
    args.path = str(unsupported_file)
    args.dry_run = False

    with patch("src.image_processor_name.main.FileOperations") as mock_file_ops_class:
        mock_file_ops = Mock()
        mock_file_ops.is_supported_image.return_value = False
        mock_file_ops_class.return_value = mock_file_ops

        result = main_module.handle_rename_command(args)

        assert result == 1


def test_handle_rename_command_directory_success(temp_image_dir: Path):
    """Test successful directory rename operation."""
    args = MagicMock()
    args.path = str(temp_image_dir)
    args.dry_run = False
    args.recursive = True
    args.quiet = False

    with (
        patch("src.image_processor_name.main.OllamaClient"),
        patch("src.image_processor_name.main.FileOperations"),
        patch("src.image_processor_name.main.ImageRenamer") as mock_renamer_class,
    ):
        mock_renamer = Mock()
        mock_renamer.test_connection.return_value = True
        mock_renamer.rename_directory.return_value = {
            "total_files": 3,
            "processed": 3,
            "failed": 0,
            "skipped": 0,
            "processing_time": 1.5,
        }
        mock_renamer_class.return_value = mock_renamer

        result = main_module.handle_rename_command(args)

        assert result == 0
        mock_renamer.rename_directory.assert_called_once()


def test_handle_rename_command_directory_with_failures(temp_image_dir: Path):
    """Test directory rename with some failures."""
    args = MagicMock()
    args.path = str(temp_image_dir)
    args.dry_run = False
    args.recursive = False
    args.quiet = False

    with (
        patch("src.image_processor_name.main.OllamaClient"),
        patch("src.image_processor_name.main.FileOperations"),
        patch("src.image_processor_name.main.ImageRenamer") as mock_renamer_class,
    ):
        mock_renamer = Mock()
        mock_renamer.test_connection.return_value = True
        mock_renamer.rename_directory.return_value = {
            "total_files": 3,
            "processed": 2,
            "failed": 1,
            "skipped": 0,
            "processing_time": 2.0,
        }
        mock_renamer_class.return_value = mock_renamer

        result = main_module.handle_rename_command(args)

        assert result == 1  # Should return error code when there are failures


def test_handle_rename_command_connection_failure(sample_image_small: Path):
    """Test rename command when Ollama connection fails."""
    args = MagicMock()
    args.path = str(sample_image_small)
    args.dry_run = False

    with (
        patch("src.image_processor_name.main.OllamaClient"),
        patch("src.image_processor_name.main.FileOperations"),
        patch("src.image_processor_name.main.ImageRenamer") as mock_renamer_class,
    ):
        mock_renamer = Mock()
        mock_renamer.test_connection.return_value = False
        mock_renamer_class.return_value = mock_renamer

        result = main_module.handle_rename_command(args)

        assert result == 1


def test_handle_rename_command_dry_run(sample_image_small: Path):
    """Test rename command in dry run mode."""
    args = MagicMock()
    args.path = str(sample_image_small)
    args.dry_run = True
    args.recursive = False
    args.quiet = False

    with (
        patch("src.image_processor_name.main.OllamaClient"),
        patch("src.image_processor_name.main.FileOperations") as mock_file_ops_class,
        patch("src.image_processor_name.main.ImageRenamer") as mock_renamer_class,
    ):
        mock_renamer = Mock()
        mock_renamer.rename_single_image.return_value = True
        mock_renamer_class.return_value = mock_renamer

        mock_file_ops = Mock()
        mock_file_ops.is_supported_image.return_value = True
        mock_file_ops_class.return_value = mock_file_ops

        result = main_module.handle_rename_command(args)

        assert result == 0
        # In dry run mode, connection test should be skipped
        mock_renamer.test_connection.assert_not_called()


@patch("src.image_processor_name.main.setup_logging")
def test_main_test_connection_success(mock_setup_logging):
    """Test main function with successful connection test."""
    with (
        patch("sys.argv", ["image-processor-name", "--check-connection"]),
        patch("src.image_processor_name.main.OllamaClient") as mock_client_class,
    ):
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client

        result = main_module.main()

        assert result == 0


@patch("src.image_processor_name.main.setup_logging")
def test_main_test_connection_failure(mock_setup_logging):
    """Test main function with failed connection test."""
    with (
        patch("sys.argv", ["image-processor-name", "--check-connection"]),
        patch("src.image_processor_name.main.OllamaClient") as mock_client_class,
    ):
        mock_client = Mock()
        mock_client.test_connection.return_value = False
        mock_client_class.return_value = mock_client

        result = main_module.main()

        assert result == 1


@patch("src.image_processor_name.main.setup_logging")
def test_main_list_models_success(mock_setup_logging):
    """Test main function with successful model listing."""
    with (
        patch("sys.argv", ["image-processor-name", "--list-models"]),
        patch("src.image_processor_name.main.OllamaClient") as mock_client_class,
    ):
        mock_client = Mock()
        mock_client.list_models.return_value = {
            "models": [{"name": "llava-llama3:latest"}]
        }
        mock_client_class.return_value = mock_client

        result = main_module.main()

        assert result == 0


@patch("src.image_processor_name.main.setup_logging")
def test_main_list_models_error(mock_setup_logging):
    """Test main function with model listing error."""
    with (
        patch("sys.argv", ["image-processor-name", "--list-models"]),
        patch("src.image_processor_name.main.OllamaClient") as mock_client_class,
    ):
        mock_client = Mock()
        mock_client.list_models.side_effect = Exception("API error")
        mock_client_class.return_value = mock_client

        result = main_module.main()

        assert result == 1


@patch("src.image_processor_name.main.setup_logging")
@patch("src.image_processor_name.main.handle_rename_command")
def test_main_rename_command(
    mock_handle_rename, mock_setup_logging, sample_image_small: Path
):
    """Test main function with rename command."""
    with patch("sys.argv", ["image-processor-name", "rename", str(sample_image_small)]):
        mock_handle_rename.return_value = 0

        result = main_module.main()

        assert result == 0
        mock_handle_rename.assert_called_once()


@patch("src.image_processor_name.main.setup_logging")
def test_main_no_command(mock_setup_logging):
    """Test main function with no command specified."""
    with patch("sys.argv", ["image-processor-name"]):
        result = main_module.main()

        assert result == 1


@patch("src.image_processor_name.main.setup_logging")
def test_main_configuration_error(mock_setup_logging):
    """Test main function with configuration error."""
    with (
        patch("sys.argv", ["image-processor-name", "--check-connection"]),
        patch("src.image_processor_name.main.OllamaClient") as mock_client_class,
    ):
        mock_client_class.side_effect = exceptions.ConfigurationError("Invalid config")

        result = main_module.main()

        assert result == 1


@patch("src.image_processor_name.main.setup_logging")
def test_main_ollama_connection_error(mock_setup_logging):
    """Test main function with Ollama connection error."""
    with (
        patch("sys.argv", ["image-processor-name", "--check-connection"]),
        patch("src.image_processor_name.main.OllamaClient") as mock_client_class,
    ):
        mock_client_class.side_effect = exceptions.OllamaConnectionError("Connection failed")

        result = main_module.main()

        assert result == 1


@patch("src.image_processor_name.main.setup_logging")
def test_main_keyboard_interrupt(mock_setup_logging):
    """Test main function with keyboard interrupt."""
    with (
        patch("sys.argv", ["image-processor-name", "--check-connection"]),
        patch("src.image_processor_name.main.OllamaClient") as mock_client_class,
    ):
        mock_client_class.side_effect = KeyboardInterrupt()

        result = main_module.main()

        assert result == 130


@patch("src.image_processor_name.main.setup_logging")
def test_main_verbose_logging(mock_setup_logging):
    """Test main function with verbose logging enabled."""
    with (
        patch("sys.argv", ["image-processor-name", "-v", "--check-connection"]),
        patch("src.image_processor_name.main.get_logger") as mock_get_logger,
        patch("src.image_processor_name.main.OllamaClient") as mock_client_class,
    ):
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client

        result = main_module.main()

        assert result == 0
        # Should set debug logging level
        mock_logger.setLevel.assert_called_once()


@patch("src.image_processor_name.main.setup_logging")
def test_main_unexpected_error(mock_setup_logging):
    """Test main function with unexpected error."""
    with (
        patch("sys.argv", ["image-processor-name", "--check-connection"]),
        patch("src.image_processor_name.main.OllamaClient") as mock_client_class,
    ):
        mock_client_class.side_effect = RuntimeError("Unexpected error")

        result = main_module.main()

        assert result == 1
