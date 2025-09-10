# New Test Suite Plan for Image Processor

## Overview

Create a comprehensive test suite for the consolidated image processor project covering both `image_processor_meta` and `image_processor_name` tools with modern testing practices and current API expectations.

## Test Structure

```text
tests/
├── conftest.py                    # Shared fixtures and test configuration
├── unit/
│   ├── __init__.py
│   ├── meta/
│   │   ├── __init__.py
│   │   ├── test_config_manager.py      # Meta tool configuration
│   │   ├── test_ollama_client.py       # Meta tool API client
│   │   ├── test_database_manager.py    # Database operations
│   │   ├── test_processor.py           # Core processing logic
│   │   └── test_main.py                # CLI entry points
│   ├── name/
│   │   ├── __init__.py
│   │   ├── test_config_manager.py      # Name tool configuration
│   │   ├── test_ollama_client.py       # Name tool API client
│   │   ├── test_renamer.py             # Core renaming logic
│   │   ├── test_file_operations.py     # File handling
│   │   └── test_main.py                # CLI entry points
│   └── shared/
│       ├── __init__.py
│       ├── test_log_manager.py         # Logging utilities
│       └── test_exceptions.py          # Custom exceptions
├── integration/
│   ├── __init__.py
│   ├── test_meta_workflow.py          # End-to-end meta processing
│   ├── test_name_workflow.py          # End-to-end name processing
│   ├── test_ollama_integration.py     # Live Ollama API tests
│   └── test_config_integration.py     # Configuration loading tests
└── fixtures/
    ├── __init__.py
    ├── sample_configs/                 # Test configuration files
    │   ├── meta_config_test.yaml
    │   └── name_config_test.yaml
    ├── sample_images/                  # Test image files
    │   ├── test_image.jpg
    │   ├── test_image.png
    │   └── corrupted_image.jpg
    └── sample_databases/               # Test database files
        └── test_descriptions.db
```

## Test Categories and Coverage Goals

### Unit Tests (Target: 90%+ coverage)

#### Meta Tool Tests (`image_processor_meta`)

##### Configuration Management (`test_config_manager.py`)

- Config file loading (YAML parsing)
- Environment variable overrides
- Default value handling
- Missing config file error handling
- Invalid YAML error handling
- Config validation

##### Ollama Client (`test_ollama_client.py`)

- API endpoint configuration
- Image encoding (base64)
- Request formatting for chat API
- Response parsing and validation
- Error handling (connection, timeout, invalid response)
- Connection testing
- Model listing

##### Database Manager (`test_database_manager.py`)

- Database initialization and schema creation
- Connection management and pooling
- CRUD operations (save, get, update, delete descriptions)
- Transaction handling and rollback
- Database locking and concurrent access
- Backup and restore operations
- Error handling and recovery

##### Processor (`test_processor.py`)

- Image file discovery and filtering
- Filename sanitization logic
- Image validation (format, size, corruption)
- Metadata embedding (XMP)
- Batch processing coordination
- Progress tracking
- Error recovery and retry logic

##### Main CLI (`test_main.py`)

- Argument parsing and validation
- Command execution flows
- Help text generation
- Version display
- Error message formatting

#### Name Tool Tests (`image_processor_name`)

##### Name Configuration Management (`test_config_manager.py`)

- Config file loading with name-specific settings
- Filename generation parameters
- File operation settings
- Watcher configuration
- Environment variable overrides

##### Name Ollama Client (`test_ollama_client.py`)

- API endpoint configuration for generate API
- Image encoding and request formatting
- Response parsing for filename generation
- Prompt customization
- Error handling and retries

##### Renamer Core (`test_renamer.py`)

- AI description generation
- Filename formatting and sanitization
- File collision handling
- Batch renaming operations
- Directory traversal (recursive vs flat)
- File filtering and validation

##### File Operations (`test_file_operations.py`)

- Safe file moving with retries
- Backup creation (if enabled)
- Permission handling
- Directory creation
- File existence checking
- Image format detection

##### Name Main CLI (`test_main.py`)

- Command parsing (rename, watch modes)
- Dry-run functionality
- Progress reporting
- Error handling and user feedback

#### Shared Component Tests

##### Log Manager (`test_log_manager.py`)

- Logger initialization and configuration
- File and console output formatting
- Log level handling
- Log rotation
- Color output (console)

##### Exceptions (`test_exceptions.py`)

- Custom exception hierarchy
- Error message formatting
- Exception chaining
- Context preservation

### Integration Tests (Target: 80%+ coverage)

#### Meta Workflow (`test_meta_workflow.py`)

- Complete image processing pipeline
- Database storage and retrieval
- XMP metadata embedding verification
- Batch processing with progress tracking
- Error recovery in multi-file scenarios

#### Name Workflow (`test_name_workflow.py`)

- Complete renaming pipeline
- Directory processing
- File collision resolution
- Watch mode functionality (if feasible in tests)
- Dry-run mode validation

#### Ollama Integration (`test_ollama_integration.py`)

- Live API connection testing (marked as requires_ollama)
- Model availability verification
- Real image processing (small test images)
- API response validation
- Rate limiting and timeout handling

#### Configuration Integration (`test_config_integration.py`)

- Multi-tool configuration loading
- Environment variable precedence
- Configuration file discovery
- Invalid configuration handling

## Test Fixtures and Utilities

### Shared Fixtures (`conftest.py`)

#### Configuration Fixtures

```python
@pytest.fixture
def temp_config_dir()  # Temporary config directory
@pytest.fixture
def sample_meta_config()  # Valid meta tool config
@pytest.fixture
def sample_name_config()  # Valid name tool config
@pytest.fixture
def invalid_config()  # Malformed YAML config
```

#### Database Fixtures

```python
@pytest.fixture
def temp_database()  # Temporary SQLite database
@pytest.fixture
def populated_database()  # Database with sample data
@pytest.fixture
def corrupted_database()  # Database for error testing
```

#### Image Fixtures

```python
@pytest.fixture
def sample_images()  # Collection of test images
@pytest.fixture
def large_image()  # Image exceeding size limits
@pytest.fixture
def corrupted_image()  # Corrupted image file
@pytest.fixture
def temp_image_dir()  # Directory with sample images
```

#### Mock Fixtures

```python
@pytest.fixture
def mock_ollama_success()  # Successful Ollama responses
@pytest.fixture
def mock_ollama_error()  # Various Ollama error conditions
@pytest.fixture
def mock_file_system()  # File system operations
```

### Sample Test Data

#### Configuration Files

- Valid configurations for both tools
- Invalid configurations for error testing
- Minimal and maximal configuration examples
- Environment-specific configurations

#### Image Files

- Small JPEG, PNG, GIF, BMP files (< 1KB for speed)
- Images with existing XMP metadata
- Images with problematic filenames
- Corrupted/invalid image files

#### Database Content

- Pre-populated databases with sample descriptions
- Empty databases for initialization tests
- Databases with edge cases (very long descriptions, special characters)

## Testing Strategy

### Test Execution

#### Pytest Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--strict-markers"
]
markers = [
    "unit: Fast unit tests that don't require external dependencies",
    "integration: Integration tests that may require setup",
    "requires_ollama: Tests that need Ollama running locally",
    "slow: Tests that take more than 5 seconds to run"
]
```

#### Test Commands

```bash
# Run all tests
uv run --extra dev pytest

# Run only unit tests
uv run --extra dev pytest -m unit

# Run integration tests (requires setup)
uv run --extra dev pytest -m integration

# Run tests that require Ollama
uv run --extra dev pytest -m requires_ollama

# Run with coverage
uv run --extra dev pytest --cov=src --cov-report=html

# Run specific tool tests
uv run --extra dev pytest tests/unit/meta/
uv run --extra dev pytest tests/unit/name/
```

### Mock Strategy

#### External Dependencies

- Mock Ollama API calls for unit tests
- Use real Ollama for integration tests (when available)
- Mock file system operations for unit tests
- Use temporary directories for integration tests

#### Database Operations

- Use in-memory SQLite for unit tests
- Use temporary files for integration tests
- Mock database errors for error handling tests

#### Configuration Loading

- Use temporary config files for tests
- Mock environment variables
- Test both valid and invalid configurations

### Error Handling Testing

#### Network Errors

- Connection timeouts
- API unavailability
- Invalid responses
- Rate limiting

#### File System Errors

- Permission denied
- Disk space issues
- Corrupted files
- Missing directories

#### Configuration Errors

- Missing config files
- Invalid YAML syntax
- Missing required fields
- Invalid values

#### Database Errors

- Connection failures
- Lock conflicts
- Disk space issues
- Schema corruption

### Performance Testing

#### Load Testing

- Process large numbers of images
- Database operations under load
- Memory usage monitoring
- Processing time benchmarks

#### Stress Testing

- Very large images
- Extremely long filenames
- Deep directory structures
- Concurrent operations

## Implementation Phases

### Phase 1: Foundation

1. Set up basic test structure and conftest.py
2. Create essential fixtures for both tools
3. Implement basic unit tests for configuration loading
4. Verify test runner setup and coverage reporting

### Phase 2: Core Unit Tests

1. Complete unit tests for both tools
2. Mock all external dependencies
3. Achieve 90%+ unit test coverage
4. Add comprehensive error handling tests

### Phase 3: Integration Tests

1. Implement workflow integration tests
2. Add Ollama integration tests (conditional)
3. Test cross-tool configuration scenarios
4. Verify end-to-end functionality

### Phase 4: Performance and Edge Cases

1. Add performance benchmarks
2. Implement stress tests
3. Test edge cases and boundary conditions
4. Add load testing for batch operations

### Phase 5: CI/CD Integration

1. Optimize test execution time
2. Create test categories for different environments
3. Add test result reporting
4. Document test maintenance procedures

## Success Criteria

### Coverage Targets

- 90%+ overall code coverage
- 95%+ unit test coverage
- 80%+ integration test coverage
- 100% critical path coverage

### Quality Metrics

- All tests pass consistently
- Test suite runs in < 60 seconds
- No flaky tests
- Clear test failure messages

### Functional Coverage

- Both tools fully tested
- All CLI commands covered
- All configuration options tested
- All error conditions handled
- Integration scenarios verified

### Maintainability

- Clear test organization
- Reusable fixtures
- Good test documentation
- Easy to add new tests

## Dependencies and Requirements

### Test Dependencies

```toml
test = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "pytest-mock>=3.10",
    "pytest-asyncio>=0.21",  # For future async tests
    "pytest-xdist>=3.0",    # For parallel test execution
    "pytest-benchmark>=4.0", # For performance tests
]
```

### Test Data Requirements

- Sample image files (various formats, sizes)
- Test configuration files for both tools
- Sample database files with test data
- Mock response data for Ollama API

### Environment Requirements

- Python 3.13+
- Optional: Ollama running locally for integration tests
- Sufficient disk space for temporary test files
- Write permissions for test directories

This comprehensive test suite will ensure both tools work correctly in the consolidated structure while providing a solid foundation for future development and maintenance.
