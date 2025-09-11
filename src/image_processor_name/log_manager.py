"""
Centralized logging management for image processor name tool.
"""

import logging
import logging.handlers
import pathlib

import colorama

# Initialize colorama
colorama.init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """
    Custom logging formatter to add colors to log messages.

    This formatter applies different colors to log messages based on their
    severity level using ANSI color codes provided by colorama.
    """

    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    FORMATS = {
        logging.DEBUG: str(colorama.Fore.CYAN) + FORMAT + str(colorama.Style.RESET_ALL),
        logging.INFO: str(colorama.Fore.GREEN) + FORMAT + str(colorama.Style.RESET_ALL),
        logging.WARNING: str(colorama.Fore.YELLOW) + FORMAT + str(colorama.Style.RESET_ALL),
        logging.ERROR: str(colorama.Fore.RED) + FORMAT + str(colorama.Style.RESET_ALL),
        logging.CRITICAL: str(colorama.Back.RED)
        + str(colorama.Fore.WHITE)
        + FORMAT
        + str(colorama.Style.RESET_ALL),
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with appropriate color."""
        log_fmt = self.FORMATS.get(record.levelno, self.FORMAT)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger(
    name: str,
    log_file: str | None = None,
    level: int = logging.INFO,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    use_colors: bool = True,
) -> logging.Logger:
    """
    Set up a logger with file and console handlers.

    Args:
        name: Logger name
        log_file: Optional log file name (stored in logs/ directory)
        level: Logging level
        max_bytes: Maximum file size before rotation
        backup_count: Number of backup files to keep
        use_colors: Whether to use colored console output

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = pathlib.Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler with optional colored formatter
    console_handler = logging.StreamHandler()
    if use_colors:
        console_handler.setFormatter(ColoredFormatter())
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            logs_dir / log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        # Use plain formatter for file output
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
