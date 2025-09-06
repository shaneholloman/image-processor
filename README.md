# Image Processor

> Note to self, consider trying these models:

```sh
ollama run llama3.2-vision:11b
ollama run gemma3:12b
```

An application that processes images to generate detailed descriptions using the Ollama LLaVA model and embeds these descriptions as XMP metadata into the images and adds them to a database.

This toolset contains two AI-powered image processing tools:

1. **image-processor-meta** - AI-powered metadata generator that embeds descriptions into images
2. **image-processor-name** - AI-powered image filename generator using descriptive names
3. Maybe I'll add more...

## Features

- **AI-Powered Descriptions**: Uses Ollama LLaVA model for intelligent image analysis
- **Metadata Integration**: Embeds descriptions as XMP metadata directly into image files
- **Database Storage**: Stores descriptions in SQLite database for easy querying and management
- **Batch Processing**: Recursively processes entire directories of images with progress tracking
- **Filename Sanitization**: Automatically cleans up filenames by replacing non-alphanumeric characters
- **Robust Error Handling**: Comprehensive error handling with retry mechanisms
- **Production Architecture**: Modern Python structure with proper logging, configuration management, and testing
- **Type Safety**: Full type annotations throughout the codebase
- **Configurable**: YAML-based configuration with environment variable overrides

## Supported Image Formats

- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif)
- BMP (.bmp)

## Prerequisites

**System Dependencies:**
Install the following system dependencies before setting up the application:

```bash
# macOS
brew install inih brotli gettext

# Ubuntu/Debian
sudo apt-get install libinih-dev libbrotli-dev gettext

# CentOS/RHEL
sudo yum install inih-devel brotli-devel gettext-devel
```

Note: The pyexiv2 library requires these system dependencies that cannot be installed through Python package managers.

**Additional Requirements:**

- **Python 3.13+**
- **`uv`** (Python package manager)
- **Ollama** with LLaVA model installed and running

### Installing Ollama

1. Install Ollama from [ollama.ai](https://ollama.ai/)
2. Pull the LLaVA model: `ollama pull llava`
3. Ensure Ollama is running: `ollama serve`

## Installation

This project uses `uv` for all package management and build operations.

### 1. Install `uv` & `ty`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
uv tool install ty@latest
```

### 2. Clone and Set Up Project

```bash
gh repo clone shaneholloman/image-processor
cd image-processor
```

### 3. Install Dependencies

```bash
# Install production dependencies
uv sync

# Install with development and test dependencies
uv sync --all-extras
```

### 4. Verify Installation

```bash
# Test Ollama connection (either tool)
uv run image-processor-meta --test-connection
uv run image-processor-name --test-connection

# Show help for both tools
uv run image-processor-meta --help
uv run image-processor-name --help
```

## Usage

### Image Metadata Processing

```bash
# Process images in default directory (./images)
uv run image-processor-meta

# Process images in specific directory
uv run image-processor-meta /path/to/images

# Process with explicit directory flag
uv run image-processor-meta -d /path/to/images

# Skip filename sanitization
uv run image-processor-meta --no-sanitize /path/to/images

# Show database statistics
uv run image-processor-meta --db-stats
```

### Image Filename Generation

```bash
# Rename images in a directory using AI-generated descriptions
uv run image-processor-name rename /path/to/images

# Rename single image file
uv run image-processor-name rename image.jpg

# Preview what would be renamed without making changes
uv run image-processor-name --dry-run rename /path/to/images
```

### Common Options

```bash
# Enable verbose logging (either tool)
uv run image-processor-meta -v /path/to/images
uv run image-processor-name -v rename /path/to/images

# List available Ollama models (either tool)
uv run image-processor-meta --list-models
uv run image-processor-name --list-models
```

## Configuration

The application uses YAML configuration files with environment variable overrides.

### Configuration Files

**Meta Tool Configuration** - Edit `config/meta_config.yaml`:

```yaml
# Ollama API settings
ollama:
  endpoint: "http://localhost:11434/api/chat"
  model: "llava"
  timeout: 30

# Database settings
database:
  path: "data/descriptions.db"

# Image processing settings
images:
  supported_extensions:
    - ".png"
    - ".jpg"
    - ".jpeg"
    - ".gif"
    - ".bmp"
  default_directory: "./images"
  max_file_size_mb: 50

# Logging settings
logging:
  level: "INFO"
  file: "logs/image_processor.log"
```

**Name Tool Configuration** - Edit `config/name_config.yaml`:

```yaml
# Ollama API Configuration
ollama:
  endpoint: "http://localhost:11434/api/generate"
  model: "llava-llama3:latest"
  timeout: 30
  retry_attempts: 3
  retry_delay: 1.0

# Image Processing Configuration
images:
  supported_extensions: [".png", ".jpg", ".jpeg", ".gif", ".bmp"]
  max_file_size_mb: 50
  verify_before_processing: true

# Filename Generation Configuration
filename:
  prompt: "Describe this image in 4-5 words"
  pattern_cleanup: true
  max_length: 100
  remove_punctuation: true
  replace_spaces_with: "-"
  case_conversion: "lower"

# Logging Configuration
logging:
  level: "INFO"
  file: "image_renamer.log"
  max_file_size_mb: 10
  backup_count: 5
```

### Environment Variables

Override any configuration with environment variables:

```bash
export OLLAMA_ENDPOINT="http://remote-ollama:11434/api/generate"
export OLLAMA_MODEL="llava-llama3"
export DATABASE_PATH="/custom/path/images.db"
export LOGGING_LEVEL="DEBUG"
```

## Development

### Development Setup

```bash
# Install with dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run specific test categories
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m requires_ollama

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Lint code
uv run ruff check src tests

# Format code
uv run ruff format src tests

# Type checking
uv run ty check src
```

### Building and Publishing

```bash
# Build package
uv build

# Install locally for testing
uv tool install --from ./dist/image_processor_meta-2.0.0-py3-none-any.whl image-processor-meta

# Publish to PyPI (when ready)
uv publish
```

## Project Structure

```text
image-processor/
├── src/
│   ├── image_processor_meta/     # Metadata processing tool
│   │   ├── __init__.py
│   │   ├── main.py              # CLI entry point
│   │   ├── processor.py         # Main processing logic
│   │   ├── exceptions.py        # Custom exceptions
│   │   ├── api/
│   │   │   └── ollama_client.py # Ollama API client
│   │   ├── db/
│   │   │   └── manager.py       # Database management
│   │   └── tools/
│   │       ├── log_manager.py   # Logging utilities
│   │       └── config_manager.py # Configuration management
│   └── image_processor_name/     # Filename generation tool
│       ├── __init__.py
│       ├── main.py              # CLI entry point
│       ├── exceptions.py        # Custom exceptions
│       ├── api/
│       │   └── ollama_client.py # Ollama API client
│       ├── core/
│       │   └── renamer.py       # Main renaming logic
│       └── tools/
│           ├── config_manager.py # Configuration management
│           ├── file_operations.py # File handling utilities
│           └── log_manager.py   # Logging utilities
├── config/
│   ├── meta_config.yaml         # Meta tool configuration
│   └── name_config.yaml         # Name tool configuration
├── tests/
│   ├── conftest.py              # Test fixtures
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── docs/
├── logs/                        # Application logs
├── pyproject.toml              # Unified project configuration
└── README.md
```

## Process Flow

1. **Initialization**
   - Load configuration from YAML and environment variables
   - Initialize database and create tables if needed
   - Test connection to Ollama API

2. **Filename Sanitization** (optional)
   - Replace non-alphanumeric characters with dashes
   - Remove multiple consecutive dashes
   - Ensure clean, consistent filenames

3. **Image Discovery**
   - Recursively scan directory for supported image files
   - Validate file sizes and formats
   - Skip files that already have descriptions (unless forced)

4. **Processing Pipeline**
   - Encode image to base64 for Ollama API
   - Generate detailed description using LLaVA model
   - Store description in SQLite database
   - Embed description as XMP metadata in image file
   - Handle retries and error recovery

5. **Results Summary**
   - Display processing statistics
   - Report any failed files
   - Log detailed information for debugging

## Error Handling

The application includes comprehensive error handling:

- **Connection Errors**: Graceful handling when Ollama is unavailable
- **File Errors**: Proper handling of permission issues and corrupted files
- **Database Errors**: Transaction rollback and connection recovery
- **Metadata Errors**: Retry mechanisms for metadata writing operations
- **Validation Errors**: Clear error messages for invalid inputs

## Database Schema

SQLite database (`descriptions.db`) stores:

```sql
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Logging

Logs are written to both console (with colors) and file:

- **Console**: Colored output for different log levels
- **File**: Plain text logs with rotation (10MB max, 5 backups)
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

Log files are stored in the `logs/` directory.

## Performance Considerations

- **Batch Processing**: Processes multiple images efficiently
- **Connection Pooling**: Reuses database connections
- **Memory Management**: Streams large files without loading entirely into memory
- **Progress Tracking**: Real-time progress indication for long-running operations

## Troubleshooting

### Common Issues

1. **Ollama Connection Failed**

   ```bash
   # Test connection
   uv run image-processor-meta --test-connection

   # Check Ollama status
   ollama list
   ollama serve
   ```

2. **Permission Denied**
   - Ensure write permissions for image directories
   - Check database file permissions
   - Verify log directory is writable

3. **Unsupported Image Format**
   - Check `config/app_config.yaml` for supported extensions
   - Ensure images are not corrupted

4. **Database Locked**
   - Check if another instance is running
   - Verify database file permissions
   - Consider using database backup/restore

### Debug Mode

Enable verbose logging for detailed troubleshooting:

```bash
uv run image-processor-meta -v /path/to/images
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the coding standards
4. Add tests for new functionality
5. Run the full test suite:
6. Run code quality checks: `uv run ruff check src tests && uv run ty src`
7. Submit a pull request

## License

MIT License - see LICENSE file for details.
