# Test Image Fixtures

This directory contains sample images for testing the image processor tools.

## Image Files

### Standard Test Images

- `small_red.jpg` - 50x50 red JPEG image
- `small_green.png` - 50x50 green PNG image
- `small_blue.gif` - 50x50 blue GIF image
- `medium_yellow.jpg` - 200x200 yellow JPEG image
- `tiny_white.png` - 10x10 white PNG image
- `landscape.jpg` - 300x200 purple landscape JPEG
- `portrait.png` - 150x250 orange portrait PNG

### Edge Case Test Files

- `corrupted.jpg` - Invalid JPEG file for error testing
- `oversized.jpg` - 2MB file for size limit testing

## Usage

These images are used by the test suite to verify:

- Image format support (JPEG, PNG, GIF)
- Various image sizes and orientations
- Error handling with corrupted files
- File size validation
- Color processing capabilities

## Regenerating Images

If you need to regenerate these test images, run:

```bash
# Basic test images
uv run tests/create_test_images.py

# Include nested directory structure for recursive testing
uv run tests/create_test_images.py --with-nested

# Clean existing images first
uv run tests/create_test_images.py --clean
```

The script will automatically create all necessary test images with proper formats, sizes, and edge cases.
