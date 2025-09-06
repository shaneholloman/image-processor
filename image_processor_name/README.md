# Image Processor Name Tool

AI-powered image filename generator using Ollama LLaVA model. This tool automatically generates descriptive filenames for images based on their content.

## Features

- **AI-Powered Renaming**: Uses Ollama LLaVA model to generate descriptive filenames
- **Multiple Operation Modes**: Batch rename or single file processing
- **Robust Architecture**: Modular design with proper error handling and logging
- **Configurable**: YAML-based configuration with environment variable overrides
- **Safe Operations**: Backup/restore mechanisms and retry logic for file operations
- **Rich CLI**: Comprehensive command-line interface with dry-run capabilities
- **Progress Tracking**: Real-time progress bars and detailed logging
- **Type Safety**: Full type hints throughout the codebase

## Prerequisites

### Required Software

1. **UV** (Python package manager)

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Ollama** with LLaVA model
   - Install from [ollama.ai](https://ollama.ai/)
   - Pull the model: `ollama pull llava-llama3:latest`
   - Start the service: `ollama serve`

## Installation

```bash
# Install all dependencies
uv sync
```

## Quick Start

```bash
# Test Ollama connection
uv run image-processor-name --test-connection

# Preview what would be renamed (dry run)
uv run image-processor-name --dry-run rename /path/to/images

# Rename all images in a directory
uv run image-processor-name rename /path/to/images

```

## Usage

### Command Structure

```bash
uv run image-processor-name [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] PATH
```

### Global Options

- `--dry-run` - Preview operations without making changes
- `--test-connection` - Test Ollama API connectivity
- `--list-models` - Show available Ollama models
- `--verbose, -v` - Enable verbose logging
- `--quiet, -q` - Suppress progress bars
- `--help` - Show help information

### Commands

#### Rename Command

Process images once and exit:

```bash
# Basic directory rename
uv run image-processor-name rename /path/to/images

# Recursive processing
uv run image-processor-name rename -r /path/to/images

# Single file
uv run image-processor-name rename image.jpg

# Custom AI prompt
uv run image-processor-name rename --prompt "Describe in 3 words" /path/to/images

# Dry run to preview
uv run image-processor-name --dry-run rename /path/to/images
```

## Configuration

Configuration is managed via `config/rename_config.yaml`. Key settings:

```yaml
# Ollama API Configuration
ollama:
  endpoint: "http://localhost:11434/api/generate"
  model: "llava-llama3:latest"
  timeout: 30

# Filename Generation
filename:
  prompt: "Describe this image in 4-5 words"
  case_conversion: "lower"  # lower, upper, title, none
  max_length: 100

# File Operations
file_operations:
  safe_move_retries: 3
  backup_originals: false
  confirm_overwrites: true

# Logging
logging:
  level: "INFO"
  file: "image_renamer.log"
  console_colors: true
```

### Environment Variables

Override any config setting using environment variables:

```bash
# Override Ollama model
export OLLAMA_MODEL="llava:7b"

# Override log level
export LOGGING_LEVEL="DEBUG"

# Override filename prompt
export FILENAME_PROMPT="Describe this image briefly"
```

## Example Workflows

### Batch Processing Photos

```bash
# Preview what will happen
uv run image-processor-name --dry-run rename ~/Pictures/vacation

# Process with progress tracking
uv run image-processor-name rename ~/Pictures/vacation

# Recursive processing with verbose logging
uv run image-processor-name -v rename -r ~/Pictures
```

### Development and Testing

```bash
# Test connection
uv run image-processor-name --test-connection

# Check available models
uv run image-processor-name --list-models

# Dry run with verbose logging
uv run image-processor-name --dry-run -v rename test_images/

# Custom prompt testing
uv run image-processor-name --dry-run rename --prompt "One word only" test.jpg
```

## Example Transformations

The AI analyzes image content and generates descriptive filenames:

| Original                  | Generated                             |
| ------------------------- | ------------------------------------- |
| `IMG_20231220_193001.jpg` | `rocket-launching-into-space.jpg`     |
| `Screenshot_2023.png`     | `woman-eating-chocolate-donut.png`    |
| `DSC_0123.jpg`            | `man-in-suit-smoking-cigarette.jpg`   |
| `photo_1.jpeg`            | `golden-retriever-playing-fetch.jpeg` |

## Architecture

```text
src/image_processor_name/
├── api/
│   └── ollama_client.py      # Ollama API integration
├── core/
│   └── renamer.py            # Main renaming logic
├── tools/
│   ├── config_manager.py     # Configuration handling
│   ├── log_manager.py        # Logging setup
│   └── file_operations.py    # Safe file operations
├── exceptions.py             # Custom exceptions
├── main.py                   # CLI interface
└── __main__.py               # Module entry point
```

## Troubleshooting

### Connection Issues

```bash
# Test Ollama connectivity
uv run image-processor-name --test-connection

# Check if Ollama is running
curl http://localhost:11434/api/tags

# Verify model is available
ollama list
```

### File Operation Issues

- **Permission denied**: Check file/directory permissions
- **File in use**: Ensure files aren't open in other applications
- **Disk space**: Verify sufficient storage space
- **Path issues**: Use absolute paths when possible

### Performance Issues

- **Slow processing**: Consider using faster Ollama model (7B vs 13B)
- **High memory usage**: Enable debug logging to monitor resource usage
- **Network timeouts**: Adjust `ollama.timeout` in configuration

### Configuration Issues

- **Config not found**: Ensure `config/rename_config.yaml` exists
- **Invalid YAML**: Check configuration file syntax
- **Environment variables**: Verify environment variable names (use `_` for nested keys)

## Development

### Code Quality

```bash
# Run linting
uv run ruff check src/

# Fix linting issues
uv run ruff check --fix src/

# Type checking
uv run ty check src/
```

### Testing

```bash
# Test basic functionality
uv run image-processor-name --test-connection

# Dry run tests
uv run image-processor-name --dry-run rename test_images/

```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- **Ollama** - Local LLM inference engine
- **LLaVA** - Vision-language model for image understanding
- **UV** - Modern Python packaging and dependency management
