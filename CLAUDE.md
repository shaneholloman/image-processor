# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a dual-tool AI-powered image processing system that provides two distinct CLI applications:

1. **image-processor-meta** - Embeds AI-generated descriptions as XMP metadata into images and stores them in SQLite database
2. **image-processor-name** - Renames images using AI-generated descriptive filenames

Both tools use Ollama's LLaVA model for computer vision analysis.

## Development Commands

### Package Management & Setup

```bash
# Install dependencies (production)
uv sync

# Install with dev/test dependencies
uv sync --all-extras

# Install ty for type checking
uv tool install ty@latest
```

### Code Quality & Testing

```bash
# Run linting
uv run ruff check src tests

# Auto-fix linting issues
uv run ruff check --fix src tests

# Format code
uv run ruff format src tests

# Type checking
uv run ty check src

# Run all tests
uv run pytest tests/

# Run only unit tests (faster - ~4 seconds vs 67 seconds for full suite)
uv run pytest tests/unit/

# Run single test file
uv run pytest tests/unit/name/test_renamer.py -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Application Usage

```bash
# Check Ollama connections
uv run image-processor-meta --check-connection
uv run image-processor-name --check-connection

# Run meta tool (embeds descriptions as metadata)
uv run image-processor-meta /path/to/images

# Run name tool (renames files)
uv run image-processor-name rename /path/to/images

# Dry run to preview changes
uv run image-processor-name --dry-run rename /path/to/images

# Verbose logging
uv run image-processor-meta -v /path/to/images
```

## Architecture

### Dual-Tool Structure

The project contains two independent CLI tools sharing common patterns but with different purposes:

**Shared Components:**

- Ollama API clients for LLaVA model integration
- Configuration management (YAML + environment variables)
- Logging utilities with file rotation
- Exception hierarchies
- Comprehensive test suites

**Tool-Specific Components:**

**Meta Tool** (`image_processor_meta/`):

- `processor.py` - Main processing engine with batch operations
- `db/manager.py` - SQLite database operations and schema management
- Embeds XMP metadata directly into image files using pyexiv2
- Uses chat API endpoint (`/api/chat`)

**Name Tool** (`image_processor_name/`):

- `core/renamer.py` - Filename sanitization and renaming logic
- `tools/file_operations.py` - Safe file operations with retry logic
- Handles filename collisions with unique naming
- Uses generate API endpoint (`/api/generate`)

### Configuration Architecture

- Tool-specific YAML configs: `config/meta_config.yaml`, `config/name_config.yaml`
- Environment variable overrides (e.g., `OLLAMA_ENDPOINT`, `LOGGING_LEVEL`)
- Nested configuration access via dot notation (e.g., `config.get("ollama.timeout", 30)`)

### Test Architecture

- **Unit tests**: Fast (~4 seconds), mock all external dependencies
- **Integration tests**: Test complete workflows with file fixtures
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.requires_ollama`
- **Fixtures**: Comprehensive test fixtures in `conftest.py` for mock clients, file operations, sample images

## Key Implementation Details

### Error Handling Patterns

Both tools implement comprehensive error handling:

- Custom exception hierarchy with specific error types
- Retry mechanisms for network and file operations
- Graceful degradation when services unavailable
- Transaction rollback for database operations

### File Operations Safety

The name tool implements robust file operations:

- Copy-then-delete strategy for moves (not atomic rename)
- Configurable retry logic with delays
- Backup creation for critical operations
- Collision detection with unique filename generation

### Configuration Management

- Config loaded during initialization and cached as instance variables
- Environment variables take precedence over YAML
- Type conversion for environment strings (bool, int, float)
- Nested access patterns: `config.get("images.max_file_size_mb", 50)`

### Testing Challenges & Solutions

When working with tests, note these important patterns:

1. **Config Mocking**: Mock `src.image_processor_name.core.renamer.config` not `tools.config_manager.config` because ImageRenamer loads config during `__init__`

2. **Mock Setup**: Set `status_code = 200` on mock HTTP responses to avoid comparison errors

3. **File Operations**: Tests use real file operations with temp directories, not mocks for file I/O

4. **Ollama Client**: Mock the requests, not the client methods for integration-like testing

## Prerequisites & Dependencies

### System Requirements

- Python 3.13+
- System libraries: `inih`, `brotli`, `gettext` (for pyexiv2)
- Ollama with LLaVA models: `llava`, `llava-llama3:latest`

### Model Management

```bash
# Pull required models
ollama pull llava
ollama pull llava-llama3:latest

# Alternative models mentioned in README
ollama pull llama3.2-vision:11b
ollama pull gemma3:12b
```

### Critical Dependencies

- **pyexiv2**: XMP metadata manipulation (requires system libraries)
- **requests**: HTTP client for Ollama API
- **Pillow**: Image processing and validation
- **pyyaml**: Configuration file parsing
- **tqdm**: Progress bars for batch operations

## Common Development Patterns

### Adding New Configuration

1. Add to appropriate YAML config file
2. Update config loading in `tools/config_manager.py`
3. Add environment variable support
4. Update tests with new config values

### Adding New Tests

1. Use existing fixtures from `conftest.py`
2. Follow naming: `test_*.py`, `Test*` classes, `test_*` methods
3. Use appropriate markers (`@pytest.mark.unit`, etc.)
4. Mock external dependencies (Ollama, file system for unit tests)

### Error Handling

1. Create specific exception types in `exceptions.py`
2. Use try-catch with specific exception types
3. Log errors with appropriate levels
4. Provide user-friendly error messages

## Project Observations

Based on extensive work with this codebase, here are key observations from today's development session:

### What Worked Well

**Test Suite Development**: Created a comprehensive test suite from scratch with 115+ tests covering both unit and integration scenarios. The test architecture with fixtures in `conftest.py` provides excellent reusability across test modules.

**Systematic Debugging Approach**: When faced with 17 failing tests, a methodical approach of running individual tests, analyzing error messages, and fixing root causes proved highly effective. Each fix built on the previous understanding.

**Mock Strategy**: The dual approach of using real file operations with temp directories while mocking external services (Ollama API) struck the right balance between test reliability and execution speed.

**Configuration Patterns**: The YAML + environment variable configuration system with dot notation access (`config.get("ollama.timeout", 30)`) provides excellent flexibility for both development and production use.

**Code Quality Tools Integration**: The combination of ruff (linting + formatting), ty (type checking), and pytest with coverage provides a solid development workflow. Ruff's auto-fix capabilities saved significant time.

### Challenges Encountered

**Config Mocking Complexity**: Initial attempts to mock configuration failed because the ImageRenamer class loads and caches config values during `__init__`. Solution required mocking `core.renamer.config` before class instantiation, not the global config manager.

**Mock Object Comparison Errors**: Mock objects without explicit attributes caused comparison failures in conditional logic (`if response.status_code >= 500`). Required adding `status_code = 200` to all mock HTTP responses.

**Test-Implementation Mismatch**: Several tests made incorrect assumptions about implementation behavior:
- Expected `Path.rename()` calls but implementation uses `shutil.copy2()` 
- Expected `ImageProcessingError` but implementation raises `FileOperationError`
- Expected different sanitization behavior based on incomplete understanding of the pattern cleanup logic

**Pytest Test Discovery Conflicts**: Fixed by renaming `test_ollama_connection()` to `check_ollama_connection()` in both main.py files to prevent pytest from incorrectly discovering application code as test cases.

### Key Insights

**Test Speed Optimization**: Unit tests run in ~4 seconds vs 67 seconds for the full suite (94% reduction). This dramatic difference makes unit tests practical for rapid development feedback loops.

**Exception Hierarchy Importance**: The custom exception types (`FileOperationError`, `ImageCorrupted`, `OllamaConnectionError`) provide precise error handling but require careful attention in tests to expect the correct exception type.

**File Operations Safety**: The copy-then-delete strategy for file moves (rather than atomic rename) provides better error recovery but requires understanding when writing tests that expect specific system call patterns.

**Production-Ready Architecture**: The dual-tool structure with shared infrastructure demonstrates how to build related CLI tools that share common patterns while maintaining separation of concerns. The comprehensive error handling, retry logic, and configuration management show production-ready thinking.

### Recommendations for Future Development

1. **Test-First Approach**: When adding new features, write tests that match the actual implementation behavior rather than assumed behavior
2. **Config Testing**: Always test configuration mocking at the correct level (module import, not global manager)
3. **Mock Setup Patterns**: Establish consistent patterns for mock HTTP responses with all required attributes
4. **Error Handling**: Maintain the custom exception hierarchy and ensure tests expect the correct exception types
5. **Performance Monitoring**: Use unit tests for rapid feedback, integration tests for complete workflow validation

This codebase emphasizes production-ready patterns with comprehensive testing, robust error handling, and clear separation of concerns between the two tools while sharing common infrastructure.
