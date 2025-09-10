#!/usr/bin/env python3
"""
Script to create test image fixtures for the image processor test suite.

This script generates various test images in different formats, sizes, and conditions
to support comprehensive testing of the image processing functionality.
"""

from pathlib import Path

from PIL import Image


def create_test_images():
    """Create all test image fixtures."""
    # Create test images directory
    fixtures_dir = Path(__file__).parent / "fixtures" / "sample_images"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating test images in: {fixtures_dir}")

    # Define test images to create
    test_images = [
        # Standard test images
        ("small_red.jpg", (50, 50), "red", "JPEG"),
        ("small_green.png", (50, 50), "green", "PNG"),
        ("small_blue.gif", (50, 50), "blue", "GIF"),
        ("medium_yellow.jpg", (200, 200), "yellow", "JPEG"),
        ("tiny_white.png", (10, 10), "white", "PNG"),
        ("landscape.jpg", (300, 200), "purple", "JPEG"),
        ("portrait.png", (150, 250), "orange", "PNG"),
        # Additional test images for variety
        ("square_black.bmp", (100, 100), "black", "BMP"),
        ("wide_cyan.png", (400, 100), "cyan", "PNG"),
        ("tall_magenta.jpg", (100, 400), "magenta", "JPEG"),
        ("gradient_test.png", (150, 150), None, "PNG"),  # Special gradient
    ]

    created_count = 0

    for filename, size, color, format in test_images:
        image_path = fixtures_dir / filename

        try:
            if color == "gradient" or filename == "gradient_test.png":
                # Create a gradient image for more complex testing
                img = create_gradient_image(size)
            else:
                img = Image.new("RGB", size, color)

            # Save with appropriate format options
            if format == "GIF":
                img.save(image_path, format, save_all=True)
            elif format == "JPEG":
                img.save(image_path, format, quality=95)
            else:
                img.save(image_path, format)

            print(
                f"✓ Created {filename} - {size[0]}x{size[1]} {color or 'gradient'} {format}"
            )
            created_count += 1

        except Exception as e:
            print(f"✗ Failed to create {filename}: {e}")

    # Create edge case test files
    create_edge_case_files(fixtures_dir)

    print(f"\nSuccessfully created {created_count} test images!")
    print(f"Total files in {fixtures_dir}: {len(list(fixtures_dir.glob('*')))}")


def create_gradient_image(size):
    """Create a gradient image for more complex visual testing."""
    width, height = size
    img = Image.new("RGB", size)
    pixels = img.load()

    if pixels is not None:
        for x in range(width):
            for y in range(height):
                # Create a diagonal gradient from red to blue
                r = int(255 * x / width)
                g = int(128 * (x + y) / (width + height))
                b = int(255 * y / height)
                pixels[x, y] = (r, g, b)

    return img


def create_edge_case_files(fixtures_dir):
    """Create edge case files for error testing."""
    edge_cases_created = 0

    # Create a corrupted image file
    corrupted_path = fixtures_dir / "corrupted.jpg"
    try:
        with corrupted_path.open("wb") as f:
            f.write(b"This is not a valid JPEG file content - corrupted for testing")
        print(f"✓ Created {corrupted_path.name} - corrupted file for error testing")
        edge_cases_created += 1
    except Exception as e:
        print(f"✗ Failed to create corrupted.jpg: {e}")

    # Create an oversized file (simulated large image)
    large_path = fixtures_dir / "oversized.jpg"
    try:
        with large_path.open("wb") as f:
            # Create 2MB of fake JPEG data
            f.write(b"\xff\xd8\xff\xe0")  # JPEG header
            f.write(b"x" * (2 * 1024 * 1024 - 4))  # 2MB total
        print(
            f"✓ Created {large_path.name} - oversized file (2MB) for size limit testing"
        )
        edge_cases_created += 1
    except Exception as e:
        print(f"✗ Failed to create oversized.jpg: {e}")

    # Create an empty file
    empty_path = fixtures_dir / "empty.jpg"
    try:
        empty_path.touch()
        print(f"✓ Created {empty_path.name} - empty file for edge case testing")
        edge_cases_created += 1
    except Exception as e:
        print(f"✗ Failed to create empty.jpg: {e}")

    # Create files with problematic names
    problematic_names = [
        "file with spaces.jpg",
        "file-with-dashes.png",
        "file_with_underscores.gif",
        "UPPERCASE.JPG",
        "MiXeD_CaSe-File.png",
        "numbers123.jpg",
        "special!@#chars.png",
    ]

    for problematic_name in problematic_names:
        try:
            problem_path = fixtures_dir / problematic_name
            img = Image.new("RGB", (30, 30), "gray")

            # Determine format from extension
            ext = problematic_name.lower().split(".")[-1]
            if ext in ["jpg", "jpeg"]:
                img.save(problem_path, "JPEG")
            elif ext == "png":
                img.save(problem_path, "PNG")
            elif ext == "gif":
                img.save(problem_path, "GIF")

            print(f"✓ Created '{problematic_name}' - filename edge case testing")
            edge_cases_created += 1

        except Exception as e:
            print(f"✗ Failed to create '{problematic_name}': {e}")

    print(f"\nCreated {edge_cases_created} edge case test files")


def create_nested_directory_structure(fixtures_dir):
    """Create a nested directory structure with images for recursive testing."""
    nested_dir = fixtures_dir / "nested_test_structure"
    nested_dir.mkdir(exist_ok=True)

    # Create subdirectories
    subdirs = [
        nested_dir / "level1",
        nested_dir / "level1" / "level2",
        nested_dir / "level1" / "level2" / "level3",
        nested_dir / "another_branch",
    ]

    for subdir in subdirs:
        subdir.mkdir(parents=True, exist_ok=True)

    # Create images in each directory
    images_created = 0
    for i, subdir in enumerate(subdirs):
        try:
            image_path = subdir / f"nested_image_{i}.jpg"
            color = ["red", "green", "blue", "yellow"][i % 4]
            img = Image.new("RGB", (40, 40), color)
            img.save(image_path, "JPEG")
            print(
                f"✓ Created {image_path.relative_to(fixtures_dir)} - nested structure testing"
            )
            images_created += 1
        except Exception as e:
            print(f"✗ Failed to create nested image in {subdir}: {e}")

    print(f"Created nested directory structure with {images_created} images")


def clean_test_images():
    """Remove all test image fixtures."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "sample_images"

    if not fixtures_dir.exists():
        print("No test images directory found to clean.")
        return

    removed_count = 0
    for item in fixtures_dir.iterdir():
        if item.is_file():
            try:
                item.unlink()
                removed_count += 1
            except Exception as e:
                print(f"✗ Failed to remove {item.name}: {e}")
        elif item.is_dir():
            try:
                import shutil

                shutil.rmtree(item)
                removed_count += 1
            except Exception as e:
                print(f"✗ Failed to remove directory {item.name}: {e}")

    print(f"Removed {removed_count} test files/directories")


def main():
    """Main function to handle command line arguments."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        print("Cleaning existing test images...")
        clean_test_images()
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--with-nested":
        print("Creating test images with nested directory structure...")
        create_test_images()
        fixtures_dir = Path(__file__).parent / "fixtures" / "sample_images"
        create_nested_directory_structure(fixtures_dir)
        return

    print("Creating test image fixtures...")
    print("Use --clean to remove existing test images")
    print("Use --with-nested to include nested directory structure")
    print()

    create_test_images()


if __name__ == "__main__":
    main()
