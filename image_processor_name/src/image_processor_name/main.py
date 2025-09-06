"""
Automatic image renaming utility that uses AI to generate descriptive filenames.
Watches directories for new images and renames them based on their content.

Version: 1.3
"""

import argparse
import base64
import gc
import logging
import re
import shutil
import time
from pathlib import Path

import requests
from PIL import Image
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageHandler(FileSystemEventHandler):
    """Handles filesystem events for image files, specifically new file creation."""

    def on_created(self, event) -> None:
        """Process newly created image files for renaming.

        Args:
            event: The filesystem event containing the path of the new file
        """
        if event.is_directory:
            return
        if event.src_path.lower().endswith((".png", ".jpg", ".jpeg")):
            # Add a small delay to ensure file is fully written
            time.sleep(1)
            rename_images_in_dir(event.src_path)


def verify_image(image_path: str) -> bool:
    """Verify image file is valid and close all handles.

    Args:
        image_path: Path to the image file

    Returns:
        bool: True if image is valid, False otherwise
    """
    try:
        img = Image.open(image_path)
        img.verify()
        img.close()
        # Force garbage collection to ensure handles are released
        gc.collect()
        return True
    except Exception as e:
        logger.error("Error verifying image %s: %s", image_path, str(e))
        return False


def encode_image(image_path: str) -> str | None:
    """Encode an image file to base64 string.

    Args:
        image_path: Path to the image file

    Returns:
        Base64 encoded string of the image or None if encoding fails
    """
    try:
        image_path_obj = Path(image_path)
        with image_path_obj.open("rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
        # Force garbage collection to ensure handles are released
        gc.collect()
        return encoded
    except Exception as e:
        logger.error("Error encoding image %s: %s", image_path, str(e))
        return None


def safe_file_move(src: str, dst: str, max_retries: int = 3) -> bool:
    """Safely move a file using copy and delete strategy.

    Args:
        src: Source file path
        dst: Destination file path
        max_retries: Maximum number of retry attempts

    Returns:
        bool: True if move successful, False otherwise
    """
    src_path = Path(src)
    dst_path = Path(dst)

    # Ensure the destination directory exists
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(max_retries):
        try:
            # Copy first
            shutil.copy2(src_path, dst_path)
            # Force garbage collection
            gc.collect()
            time.sleep(0.5)  # Small delay to ensure copy is complete

            # Then try to remove original
            try:
                src_path.unlink()
                return True
            except OSError as e:
                logger.warning("Could not remove original file: %s", str(e))
                # If we can't remove original, remove the copy and try again
                dst_path.unlink()

        except OSError as e:
            logger.warning("Move attempt %d failed: %s", attempt + 1, str(e))
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return False

    return False


def rename_file(path: str) -> str | None:
    """Generate a new name for an image using AI description.

    Args:
        path: Path to the image file

    Returns:
        New filename or None if unsuccessful
    """
    path_obj = Path(path)
    if not path_obj.is_file() or not path_obj.exists():
        return None

    # Verify image first
    if not verify_image(str(path_obj)):
        return None

    try:
        encoded_image = encode_image(str(path_obj))
        if not encoded_image:
            return None

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llava-llama3:latest",
                "prompt": "Describe this image in 4-5 words",
                "stream": False,
                "images": [encoded_image],
            },
            timeout=30
        ).json()

        if "response" in response:
            description = response["response"].strip().lower()
            # Remove trailing punctuation first
            description = description.rstrip('.,!?;:')
            # Replace spaces and special characters with dashes
            new_name = "".join(c if c.isalnum() else "-" for c in description)
            # Clean up multiple consecutive dashes and trailing dashes
            new_name = re.sub(r'-+', '-', new_name).strip('-')
            # Add original extension
            return f"{new_name}{path_obj.suffix}"

    except Exception as e:
        logger.error("Error processing %s: %s", path_obj, str(e))
        return None

    return None


def rename_images_in_dir(path: str) -> None:
    """Rename image files in a directory or a single file.

    Args:
        path: Path to directory or file to process
    """
    path_obj = Path(path)

    if path_obj.is_file():
        new_name = rename_file(str(path_obj))
        if new_name:
            new_path = path_obj.parent / new_name
            if not safe_file_move(str(path_obj), str(new_path)):
                logger.error("Failed to rename %s after multiple attempts", path_obj)
    else:
        for filepath in path_obj.glob("*"):
            if filepath.suffix.lower() in (".png", ".jpg", ".jpeg"):
                new_name = rename_file(str(filepath))
                if new_name:
                    new_path = filepath.parent / new_name
                    if not safe_file_move(str(filepath), str(new_path)):
                        logger.error("Failed to rename %s after multiple attempts", filepath)


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Rename images in a directory or a single file."
    )
    parser.add_argument("path", help="The directory or file to rename images in.")
    args = parser.parse_args()

    path = Path(args.path).resolve()
    if not path.exists():
        logger.error("Specified path does not exist: %s", path)
        return

    rename_images_in_dir(str(path))

    # Only start the observer if the path is a directory
    if path.is_dir():
        event_handler = ImageHandler()
        observer = Observer()
        observer.schedule(event_handler, path=str(path), recursive=False)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        logger.info("Processed single file. Exiting.")


if __name__ == "__main__":
    main()
