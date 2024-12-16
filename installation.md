# Installation Guide

[[toc]]

## Using UV Package Manager

UV is a highly performant Python package installer and resolver written in Rust. Here's how to use it with this project.

### Basic UV Usage

1. Install UV:

    ```bash
    pip install uv
    ```

2. Create virtual environment:

    ```bash
    uv venv
    ```

3. Install dependencies:

    ```bash
    uv pip install -r requirements.txt
    ```

### Advantages of UV

- 4-10x faster installation through rust-based parallel downloading
- Built-in compile command for dependency locking
- Automatic virtual environment handling
- Binary caching for faster subsequent installs
- Compatible with existing requirements.txt format

### Managing Development vs. Production Requirements

Best practice is to split requirements into separate files:

1. `requirements.txt` - Core production dependencies

    ```txt
    pyexiv2
    requests
    colorama
    tqdm
    ```

2. `requirements-dev.txt` - Development dependencies

    ```txt
    # Include production dependencies
    -r requirements.txt

    # Development tools
    pytest          # Testing framework for writing and running unit tests
    black           # Code formatter to ensure consistent code style
    pylint          # Static code analyzer and linter for code quality
    mypy            # Static type checker for Python
    ```

Install development dependencies with:

```bash
uv pip install -r requirements-dev.txt
```

### Running Tests

The project uses pytest with different test categories:

1. Unit Tests (CI-friendly):

    ```bash
    python -m pytest -v -m unit
    ```

    - No external dependencies required
    - Safe to run in CI environments
    - Tests core functionality only

2. Integration Tests:

    ```bash
    python -m pytest -v -m integration
    ```

    - Requires local setup (Ollama, image files)
    - Tests real-world functionality
    - Includes metadata writing and API calls

3. All Tests:

    ```bash
    python -m pytest -v -m "unit or integration"
    ```

4. Specific Test Categories:

    ```bash
    # Tests requiring Ollama
    python -m pytest -v -m requires_ollama

    # Tests not requiring Ollama
    python -m pytest -v -m "not requires_ollama"
    ```

### Dependency Locking

UV provides built-in dependency locking:

1. Lock production dependencies:

    ```bash
    uv pip compile requirements.txt -o requirements.lock
    ```

2. Lock development dependencies:

    ```bash
    uv pip compile requirements-dev.txt -o requirements-dev.lock
    ```

Install from lock files:

```bash
uv pip install -r requirements.lock  # Production
uv pip install -r requirements-dev.lock  # Development
```

### UV and PyPI Publishing

While UV is primarily a package installer, for PyPI publishing you'll still use standard tools:

1. Build package:

    ```bash
    pip install build
    python -m build
    ```

2. Upload to PyPI:

    ```bash
    pip install twine
    twine upload dist/*
    ```

> [!TIP]
> UV can be used to install the build dependencies:
>
> ```bash
> uv pip install build twine
> ```

### Converting Existing Project to UV

1. Create new virtual environment:

    ```bash
    uv venv
    ```

2. Install dependencies:

    ```bash
    uv pip install -r requirements.txt  # Production only
    # or
    uv pip install -r requirements-dev.txt  # Including dev tools
    ```

3. Generate lock files (recommended):

    ```bash
    uv pip compile requirements.txt -o requirements.lock
    uv pip compile requirements-dev.txt -o requirements-dev.lock
    ```

### Comparison with Traditional pip Workflows

| Task             | Traditional pip                       | UV                                                     |
| ---------------- | ------------------------------------- | ------------------------------------------------------ |
| Create venv      | `python -m venv venv`                 | `uv venv`                                              |
| Install deps     | `pip install -r requirements.txt`     | `uv pip install -r requirements.txt`                   |
| Lock deps        | `pip-compile requirements.txt`        | `uv pip compile requirements.txt -o requirements.lock` |
| Install dev deps | `pip install -r requirements-dev.txt` | `uv pip install -r requirements-dev.txt`               |

> [!NOTE]
> UV maintains compatibility with pip's workflows while providing significant performance improvements and additional features.
