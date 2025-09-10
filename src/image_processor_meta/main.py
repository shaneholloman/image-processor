"""
Main entry point for image meta processor CLI.
"""

import argparse
import sys
from pathlib import Path

from .api.ollama_client import OllamaClient
from .db.manager import DatabaseManager
from .exceptions import ImageProcessorError, OllamaConnectionError
from .processor import ImageProcessor
from .tools.config_manager import config
from .tools.log_manager import get_logger, setup_logger


def setup_logging() -> None:
    """Set up application logging."""
    log_level = config.get("logging.level", "INFO")
    log_file = config.get("logging.file", "image_processor.log")

    setup_logger(
        name="image_processor_meta",
        log_file=log_file,
        level=getattr(__import__("logging"), log_level.upper()),
        max_bytes=config.get("logging.max_file_size_mb", 10) * 1024 * 1024,
        backup_count=config.get("logging.backup_count", 5),
    )


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Process images and generate AI-powered metadata descriptions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Process images in default directory
  %(prog)s /path/to/images          # Process images in specific directory
  %(prog)s -d /path/to/images       # Process with explicit directory flag
  %(prog)s --no-sanitize           # Skip filename sanitization
  %(prog)s --check-connection      # Check Ollama connection only
        """,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        help=f"Directory containing images to process (default: {config.get('images.default_directory', './images')})",
    )

    parser.add_argument(
        "-d",
        "--directory",
        dest="directory_flag",
        help="Directory containing images to process",
    )

    parser.add_argument(
        "--no-sanitize", action="store_true", help="Skip filename sanitization step"
    )

    parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress bar"
    )

    parser.add_argument(
        "--check-connection",
        action="store_true",
        help="Check Ollama connection and exit",
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available Ollama models and exit",
    )

    parser.add_argument(
        "--db-stats", action="store_true", help="Show database statistics and exit"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--version", action="version", version="Image Meta Processor v2.0.0"
    )

    return parser


def check_ollama_connection(ollama_client: OllamaClient) -> bool:
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
    print("2. Check that the LLaVA model is available: ollama pull llava")
    print("3. Verify the endpoint URL in configuration")
    return False


def show_database_stats(db_manager: DatabaseManager) -> None:
    """Show database statistics."""
    print("Database Statistics:")
    print(f"  Database path: {db_manager.db_path}")
    print(f"  Total records: {db_manager.count_records()}")

    try:
        recent_records = db_manager.get_all_descriptions()[:5]
        if recent_records:
            print("  Most recent entries:")
            for record in recent_records:
                print(f"    - {Path(record['file_path']).name}")
    except Exception as e:
        print(f"  Error retrieving records: {e}")


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Set up logging first
        setup_logging()
        logger = get_logger(__name__)

        # Parse arguments
        parser = create_argument_parser()
        args = parser.parse_args()

        # Set verbose logging if requested
        if args.verbose:
            logger.setLevel(__import__("logging").DEBUG)
            logger.debug("Verbose logging enabled")

        # Initialize clients
        ollama_client = OllamaClient()
        db_manager = DatabaseManager()

        # Handle special commands
        if args.check_connection:
            return 0 if check_ollama_connection(ollama_client) else 1

        if args.list_models:
            try:
                models = ollama_client.list_models()
                print("Available Ollama models:")
                for model in models.get("models", []):
                    print(f"  - {model.get('name', 'Unknown')}")
                return 0
            except Exception as e:
                logger.error(f"Failed to list models: {e}")
                return 1

        if args.db_stats:
            show_database_stats(db_manager)
            return 0

        # Determine target directory
        target_dir = (
            args.directory_flag
            or args.directory
            or config.get("images.default_directory", "./images")
        )

        target_path = Path(target_dir).resolve()

        logger.info(f"Starting image processing for: {target_path}")

        # Test Ollama connection before processing
        if not ollama_client.test_connection():
            logger.error("Cannot connect to Ollama. Please ensure it's running.")
            print(
                "\nOllama connection failed. Run with --check-connection for details."
            )
            return 1

        # Initialize processor and run
        processor = ImageProcessor(ollama_client, db_manager)

        results = processor.process_directory(
            directory=target_path,
            sanitize_names=not args.no_sanitize,
            show_progress=not args.no_progress,
        )

        # Print summary
        print("\nProcessing Summary:")
        print(f"  Total files found: {results['total_files']}")
        print(f"  Successfully processed: {results['processed']}")
        print(f"  Failed: {results['failed']}")
        print(f"  Files renamed: {results['renamed']}")
        print(f"  Processing time: {results['processing_time']:.1f} seconds")

        if results["failed"] > 0:
            print(
                f"\nWarning: {results['failed']} files failed processing. Check logs for details."
            )
            return 1

        print("\n✓ All images processed successfully!")
        return 0

    except OllamaConnectionError as e:
        logger.error(f"Ollama connection error: {e}")
        print(f"Error: {e}")
        print("Run with --check-connection to diagnose connection issues.")
        return 1

    except ImageProcessorError as e:
        logger.error(f"Processing error: {e}")
        print(f"Error: {e}")
        return 1

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        print("\nProcessing interrupted by user.")
        return 130

    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
