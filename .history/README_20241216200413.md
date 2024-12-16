# Image Meta Processor

A Python application that processes images to generate detailed descriptions using the Ollama LLaVA model and embeds these descriptions as metadata into the images.

## Features

- 🖼️ Supports multiple image formats (PNG, JPG, JPEG, GIF, BMP)
- 🤖 Uses Ollama LLaVA model for AI-powered image descriptions
- 📝 Embeds descriptions as XMP metadata directly into image files
- 🗃️ Stores descriptions in a SQLite database for easy querying
- 🧹 Sanitizes filenames by replacing non-alphanumeric characters
- 🎨 Colorful console output with progress tracking
- ♻️ Handles retries for metadata writing operations
- 📁 Recursively processes entire directories of images

## Prerequisites

- Python 3.x
- [Ollama](https://ollama.ai/) installed and running with the LLaVA model
- UV package manager (recommended) or pip

## Quick Start

1. Install UV (recommended):

    ```bash
    pip install uv
    ```

2. Create and activate virtual environment:

    ```bash
    uv venv
    # Activate based on your OS:
    # Windows: .venv/Scripts/activate
    # Unix: source .venv/bin/activate
    ```

3. Install dependencies:

    ```bash
    uv pip install -r requirements.txt
    ```

4. Run the script:

    ```bash
    python image_sanitize_meta_processor.py [input_directory]
    ```

## Installation Options

See [installation.md](installation.md) for detailed installation instructions, including:

- Using UV vs traditional pip
- Managing development dependencies
- Running tests
- Dependency locking
- Project setup guides

## Usage

The script can be run with an optional input directory parameter:

```bash
python image_sanitize_meta_processor.py [path/to/images]
```

If no directory is specified, it defaults to `./images`.

### Process Flow

1. **Filename Sanitization**:
   - Replaces non-alphanumeric characters with dashes
   - Ensures clean, consistent filenames

2. **Image Processing**:
   - Generates detailed descriptions using LLaVA model
   - Stores descriptions in SQLite database
   - Embeds descriptions as XMP metadata

3. **Progress Tracking**:
   - Shows real-time progress with tqdm
   - Provides colored console output
   - Displays summary after completion

## Database Schema

The SQLite database (`image_descriptions.db`) stores:

- File paths
- Generated descriptions
- Timestamps (automatically added)

## Error Handling

- Retries metadata writing operations up to 3 times
- Handles file permission issues
- Manages API timeouts
- Logs errors with different severity levels

## Development

For development work:

1. Install development dependencies:

    ```bash
    uv pip install -r requirements-dev.txt
    ```

2. Run tests:

    ```bash
    # Unit tests
    python -m pytest -v -m unit

    # Integration tests
    python -m pytest -v -m integration

    # All tests
    python -m pytest -v
   ```

## Known Issues & Future Plans

### Test Suite Improvements

- Expand test coverage to include:
  - SQLite database operations
  - Existing image metadata reading
- Integrate Ollama with GitHub workflow runners
- Resolve linting issues in test_integration.py

### General Improvements

- Optimize image encoding handling (bytes vs base64)
- Enhance SQLite database operations and management
- Improve CI/CD pipeline with automated testing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

[MIT License](LICENSE)
