"""
Main entry point for image processor name tool CLI.
"""

import argparse
import sys
from pathlib import Path

from .api.ollama_client import OllamaClient
from .core.renamer import ImageRenamer
from .exceptions import (
    ConfigurationError,
    ImageProcessorNameError,
    OllamaConnectionError,
)
from .tools.config_manager import config
from .tools.file_operations import FileOperations
from .tools.log_manager import get_logger, setup_logger


def setup_logging() -> None:
    """Set up application logging."""
    log_level = config.get("logging.level", "INFO")
    log_file = config.get("logging.file", "image_renamer.log")
    use_colors = config.get("logging.console_colors", True)

    setup_logger(
        name="image_processor_name",
        log_file=log_file,
        level=getattr(__import__("logging"), log_level.upper()),
        max_bytes=config.get("logging.max_file_size_mb", 10) * 1024 * 1024,
        backup_count=config.get("logging.backup_count", 5),
        use_colors=use_colors,
    )


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="AI-powered image filename generator using Ollama LLaVA model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s rename /path/to/images         # Rename all images in directory
  %(prog)s rename image.jpg              # Rename single image file
  %(prog)s --test-connection             # Test Ollama connection
  %(prog)s --dry-run rename /path/images # Preview what would be renamed

Modes:
  rename    Process images once and exit
        """,
    )

    # Global options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without actually renaming files",
    )

    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test Ollama connection and exit",
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available Ollama models and exit",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress bars and non-essential output",
    )

    parser.add_argument(
        "--version", action="version", version="Image Processor Name Tool v2.0.0"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Rename command
    rename_parser = subparsers.add_parser(
        "rename", help="Rename images using AI-generated descriptions"
    )
    rename_parser.add_argument("path", help="Directory or file to process")
    rename_parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Process subdirectories recursively",
    )
    rename_parser.add_argument(
        "--prompt", help="Custom prompt for AI description generation"
    )

    return parser


def test_ollama_connection(ollama_client: OllamaClient) -> bool:
    """
    Test connection to Ollama API.

    Args:
        ollama_client: Ollama client instance

    Returns:
        True if connection successful
    """
    print("Testing Ollama connection...")

    if ollama_client.test_connection():
        print(f"✓ Successfully connected to Ollama at {ollama_client.endpoint}")
        print(f"✓ Using model: {ollama_client.model}")
        return True

    print(f"✗ Failed to connect to Ollama at {ollama_client.endpoint}")
    print("\nTroubleshooting:")
    print("1. Ensure Ollama is installed and running")
    print("2. Check that the LLaVA model is available: ollama pull llava-llama3:latest")
    print("3. Verify the endpoint URL in configuration")
    return False


def handle_rename_command(args: argparse.Namespace) -> int:
    """
    Handle the rename command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    logger = get_logger(__name__)

    try:
        target_path = Path(args.path).resolve()

        if not target_path.exists():
            print(f"Error: Path does not exist: {target_path}")
            return 1

        # Initialize components
        ollama_client = OllamaClient()
        file_ops = FileOperations()
        renamer = ImageRenamer(ollama_client, file_ops)

        # Test connection first
        if not args.dry_run and not renamer.test_connection():
            print("Error: Cannot connect to Ollama. Use --test-connection for details.")
            return 1

        # Process single file or directory
        if target_path.is_file():
            if not file_ops.is_supported_image(target_path):
                print(f"Error: Unsupported image format: {target_path}")
                return 1

            success = renamer.rename_single_image(target_path, args.dry_run)
            return 0 if success else 1

        if target_path.is_dir():
            results = renamer.rename_directory(
                target_path,
                recursive=args.recursive,
                dry_run=args.dry_run,
                show_progress=not args.quiet,
            )

            # Print summary
            action = "analyzed" if args.dry_run else "renamed"
            print("\nProcessing Summary:")
            print(f"  Total files found: {results['total_files']}")
            print(f"  Successfully {action}: {results['processed']}")
            print(f"  Failed: {results['failed']}")
            print(f"  Skipped: {results['skipped']}")
            print(f"  Processing time: {results['processing_time']:.1f} seconds")

            if results["failed"] > 0:
                print(
                    f"\nWarning: {results['failed']} files failed processing. Check logs for details."
                )
                return 1

            success_msg = (
                "Analysis complete!"
                if args.dry_run
                else "All images processed successfully!"
            )
            print(f"\n✓ {success_msg}")
            return 0

        print(f"Error: Path is neither a file nor directory: {target_path}")
        return 1

    except Exception as e:
        logger.error(f"Rename command failed: {e}")
        print(f"Error: {e}")
        return 1


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Parse arguments first to handle early exits
        parser = create_argument_parser()
        args = parser.parse_args()

        # Set up logging
        setup_logging()
        logger = get_logger(__name__)

        # Set verbose logging if requested
        if args.verbose:
            logger.setLevel(__import__("logging").DEBUG)
            logger.debug("Verbose logging enabled")

        # Handle global options that don't need full setup
        if args.test_connection:
            ollama_client = OllamaClient()
            return 0 if test_ollama_connection(ollama_client) else 1

        if args.list_models:
            try:
                ollama_client = OllamaClient()
                models = ollama_client.list_models()
                print("Available Ollama models:")
                for model in models.get("models", []):
                    print(f"  - {model.get('name', 'Unknown')}")
                return 0
            except Exception as e:
                logger.error(f"Failed to list models: {e}")
                print(f"Error listing models: {e}")
                return 1

        # Handle commands
        if args.command == "rename":
            return handle_rename_command(args)
        # No command specified, show help
        parser.print_help()
        return 1

    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        print("Check your configuration file and try again.")
        return 1

    except OllamaConnectionError as e:
        print(f"Ollama connection error: {e}")
        print("Run with --test-connection to diagnose connection issues.")
        return 1

    except ImageProcessorNameError as e:
        print(f"Error: {e}")
        return 1

    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
        return 130

    except Exception as e:
        logger = get_logger(__name__)
        logger.exception("Unexpected error occurred")
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
