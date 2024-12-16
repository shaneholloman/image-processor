"""
Image Processor Script

This script recursively processes images in a directory, generates descriptions
using the Ollama LLaVA model, and embeds these descriptions as metadata into the images.

Version: 1.0.1
Author: AI Assistant
"""

import argparse
import base64
import json
import logging
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Union

import pyexiv2
import requests
from colorama import Back, Fore, Style, init
from tqdm import tqdm

# Initialize colorama
init(autoreset=True)

# Configuration constants
OLLAMA_API_ENDPOINT = "http://localhost:11434/api/generate"
DB_PATH = "image_descriptions.db"
SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
DEFAULT_IMAGE_DIR = r"./images"
OLLAMA_MODEL = "llava-llama3"
OLLAMA_PROMPT = "Describe this image in great detail using 1 large paragraph."
METADATA_XMP_TAG = "Xmp.dc.description"
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
REQUEST_TIMEOUT = 30  # seconds
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Configure logging
class ColoredFormatter(logging.Formatter):
    """
    Custom logging formatter to add colors to log messages.

    This formatter applies different colors to log messages based on their
    severity level. It uses ANSI color codes provided by the colorama library.

    Attributes:
        FORMAT (str): The base format string for log messages.
        FORMATS (dict): A dictionary mapping logging levels to colored format strings.
    """

    FORMAT = LOG_FORMAT
    FORMATS = {
        logging.DEBUG: Fore.CYAN + FORMAT + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + FORMAT + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + FORMAT + Style.RESET_ALL,
        logging.ERROR: Fore.RED + FORMAT + Style.RESET_ALL,
        logging.CRITICAL: Back.RED + Fore.WHITE + FORMAT + Style.RESET_ALL,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def sanitize_filenames(directory: str) -> None:
    """
    Walk through directory and sanitize filenames by replacing all non-alphanumeric
    characters with dashes, preserving file extensions.

    Args:
        directory (str): Path to the directory containing files to sanitize
    """
    logger.info("Starting filename sanitization...")

    for root, _, files in os.walk(directory):
        for filename in files:
            # Split filename and extension
            name, ext = os.path.splitext(filename)

            # Check if filename needs sanitization (has non-alphanumeric chars)
            if not name.replace('-', '').isalnum():
                old_path = os.path.join(root, filename)

                # Replace all non-alphanumeric chars with dash, preserve extension
                new_name = re.sub(r'[^a-zA-Z0-9]', '-', name)
                # Remove multiple consecutive dashes
                new_name = re.sub(r'-+', '-', new_name)
                # Remove leading/trailing dashes
                new_name = new_name.strip('-')

                new_filename = f"{new_name}{ext}"
                new_path = os.path.join(root, new_filename)

                try:
                    os.rename(old_path, new_path)
                    logger.info("Renamed: %s -> %s", filename, new_filename)
                except OSError as e:
                    logger.error("Failed to rename %s: %s", filename, str(e))


def get_image_description(image_path: str, timeout: int = REQUEST_TIMEOUT) -> str:
    """
    Get image description from Ollama LLaVA model.

    Args:
        image_path (str): Path to the image file.
        timeout (int): Timeout in seconds for the entire operation.

    Returns:
        str: Description of the image.
    """
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        base64_image = base64.b64encode(image_data).decode("utf-8")

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": OLLAMA_PROMPT,
            "images": [base64_image],
            "stream": True,
        }

        start_time = time.time()
        description = ""
        with requests.post(
            OLLAMA_API_ENDPOINT, json=payload, stream=True, timeout=timeout
        ) as response:
            if response.status_code != 200:
                logger.error(
                    "Failed to get description for %s. Status code: %s",
                    image_path,
                    response.status_code,
                )
                return "Failed to generate description"

            for line in response.iter_lines():
                if time.time() - start_time > timeout:
                    logger.error("Operation timed out for %s", image_path)
                    return "Operation timed out"

                if line:
                    try:
                        json_line = json.loads(line)
                        if "response" in json_line:
                            description += json_line["response"]
                    except json.JSONDecodeError:
                        logger.error("Failed to parse JSON from line: %s", line)

        return description.strip()

    except requests.RequestException as e:
        logger.error("Request failed for %s: %s", image_path, str(e))
    except Exception as e:
        logger.error("Unexpected error processing %s: %s", image_path, str(e))

    return "Failed to generate description"


def write_metadata(image_path: str, description: str) -> bool:
    """
    Write the image description as metadata to the image file.
    Handles paths with spaces across Windows and Unix platforms.

    Args:
        image_path (str): Path to the image file.
        description (str): Description to be written as metadata.

    Returns:
        bool: True if metadata was successfully written, False otherwise.
    """
    for attempt in range(MAX_RETRIES):
        try:
            # Convert to Path object and resolve to absolute path
            path_obj = Path(image_path).resolve()

            if not path_obj.exists():
                logger.error("File not found: %s", str(path_obj))
                return False

            logger.debug("Original path: %s", image_path)
            logger.debug("Resolved path object: %s", str(path_obj))

            # Get the file path and encode it properly for pyexiv2
            if os.name == 'nt':  # Windows
                file_path = str(path_obj).replace('\\', '\\\\')
                if ' ' in file_path:
                    file_path = f'"{file_path}"'
            else:  # Unix-like
                file_path = str(path_obj)
                if ' ' in file_path:
                    file_path = file_path.replace(' ', '\\ ')

            logger.debug("Final path for pyexiv2: %s", file_path)

            # Remove any surrounding quotes when passing to pyexiv2
            actual_path = file_path.strip('"')

            with pyexiv2.Image(actual_path) as img:
                img.modify_xmp({METADATA_XMP_TAG: description})
            return True

        except FileNotFoundError as e:
            logger.error(
                "Attempt %d - File not found error for %s: %s",
                attempt + 1,
                file_path,
                str(e)
            )
        except PermissionError as e:
            logger.error(
                "Attempt %d - Permission denied for %s: %s",
                attempt + 1,
                file_path,
                str(e)
            )
        except OSError as e:
            logger.error(
                "Attempt %d - OS error for %s: %s",
                attempt + 1,
                file_path,
                str(e)
            )
        except Exception as e:
            logger.error(
                "Attempt %d - Failed to write metadata for %s: %s",
                attempt + 1,
                file_path,
                str(e)
            )

        if attempt < MAX_RETRIES - 1:
            logger.debug("Retrying after delay...")
            time.sleep(RETRY_DELAY)

    return False


def process_image(image_path: str) -> Dict[str, Union[str, bool]]:
    """
    Process a single image file.

    Args:
        image_path (str): Path to the image file.

    Returns:
        Dict[str, Union[str, bool]]:
        Dictionary containing file path, description, and metadata status.
    """
    print(f"\n{Fore.CYAN}Processing: {Style.BRIGHT}{image_path}{Style.RESET_ALL}")

    description = get_image_description(image_path)

    # Log to console
    print(f"{Fore.GREEN}Description: {Style.RESET_ALL}{description}")

    # Write to database
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO image_descriptions (filepath, description) VALUES (?, ?)",
            (image_path, description),
        )
        conn.commit()
        print(f"{Fore.GREEN}✓ Database updated{Style.RESET_ALL}")
    except sqlite3.Error as e:
        logger.error("Database error for %s: %s", image_path, str(e))
    finally:
        if conn:
            conn.close()

    # Write metadata to image
    metadata_status = write_metadata(image_path, description)
    if metadata_status:
        print(f"{Fore.GREEN}✓ Metadata written{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ Failed to write metadata{Style.RESET_ALL}")

    print(f"{Fore.WHITE}{'='*50}{Style.RESET_ALL}\n")

    return {
        "filepath": image_path,
        "description": description,
        "metadata_written": metadata_status,
    }


def is_supported_image(file_path: str) -> bool:
    """
    Check if the file is a supported image type.

    Args:
        file_path (str): Path to the file.

    Returns:
        bool: True if the file is a supported image type, False otherwise.
    """
    return file_path.lower().endswith(SUPPORTED_EXTENSIONS)


def process_directory(directory: str) -> List[Dict[str, Union[str, bool]]]:
    """
    Recursively process all images in a directory.

    Args:
        directory (str): Path to the directory containing images.

    Returns:
        List[Dict[str, Union[str, bool]]]:
        List of dictionaries containing file paths, descriptions, and metadata statuses.
    """
    results = []
    for root, _, files in os.walk(directory):
        for file in tqdm(
            files,
            desc=f"{Fore.BLUE}Processing {root}{Style.RESET_ALL}",
            unit="file",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
        ):
            file_path = os.path.join(root, file)
            if is_supported_image(file_path):
                try:
                    result = process_image(file_path)
                    results.append(result)
                except Exception as e:
                    logger.error("Error processing %s: %s", file_path, str(e))
            else:
                print(
                    f"{Fore.YELLOW}Skipping unsupported file: {file_path}{Style.RESET_ALL}"
                )
    return results


def main():
    """Main function to run the image processing script."""
    parser = argparse.ArgumentParser(
        description="Process images in a directory, generate descriptions, and embed metadata."
    )
    parser.add_argument(
        "input_directory",
        nargs="?",
        default=DEFAULT_IMAGE_DIR,
        help=f"Path to the directory containing images to process (default: {DEFAULT_IMAGE_DIR})",
    )
    args = parser.parse_args()

    # Confirm the directory with the user
    print(
        f"{Fore.CYAN}The script will process images in: "
        f"{Style.BRIGHT}{args.input_directory}{Style.RESET_ALL}"
    )

    # Ask about filename sanitization
    print(f"\n{Fore.YELLOW}This script will:")
    print("1. Sanitize filenames (replace non-alphanumeric characters with dashes)")
    print("2. Generate descriptions for each image")
    print(f"3. Embed metadata into the images{Style.RESET_ALL}\n")

    user_confirm = (
        input(
            f"{Fore.YELLOW}Do you want to proceed? (y/n): {Style.RESET_ALL}"
        )
        .lower()
        .strip()
    )

    if user_confirm != "y":
        print(f"{Fore.RED}Script execution cancelled.{Style.RESET_ALL}")
        return

    # Sanitize filenames first
    print(f"\n{Fore.CYAN}Step 1: Sanitizing filenames...{Style.RESET_ALL}")
    sanitize_filenames(args.input_directory)
    print(f"{Fore.GREEN}Filename sanitization complete.{Style.RESET_ALL}\n")

    # Process the images
    print(f"{Fore.CYAN}Step 2: Processing images...{Style.RESET_ALL}")
    results = process_directory(args.input_directory)

    # Show summary
    successful_metadata = sum(1 for result in results if result["metadata_written"])
    print(f"\n{Fore.GREEN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Summary:{Style.RESET_ALL}")
    print(f"Processed {Style.BRIGHT}{len(results)}{Style.RESET_ALL} images.")
    print(
        f"Success writing metadata to {Style.BRIGHT}{successful_metadata}{Style.RESET_ALL} images."
    )
    print(f"{Fore.GREEN}{'='*50}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
