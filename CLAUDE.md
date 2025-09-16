# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is Gistly, a Python CLI tool project for managing GitHub Gists. The project is fully implemented following TDD methodology with comprehensive test coverage.

## Development Commands

### Virtual Environment Setup
```bash
# Create virtual environment
python3.13 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Deactivate when done
deactivate
```

### Installation and Development
```bash
# Install in development mode
pip install -e .

# Test installation
gist --help
quick-gist --help

# Test basic functionality
python -c "import gist_manager; print('Import successful')"
```

### Testing Strategy

The project follows TDD (Test-Driven Development) approach:

```bash
# Run all tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=gist_manager

# Run specific test file
python -m pytest tests/test_core.py

# Run tests in verbose mode
python -m pytest -v

# Run tests and stop on first failure
python -m pytest -x
```

## Architecture Overview

The project follows a modular Python package structure:

### Core Components
- **`gist_manager/config.py`**: Configuration management
  - Token discovery hierarchy: ENV → `~/.gist-manager/config.json` → `./config.json`
  - Functions: `get_github_token()`, `setup_config()`

- **`gist_manager/core.py`**: Main `GistManager` class with GitHub API integration
  - Automatic token discovery from multiple sources
  - Methods: `create_gist()`, `create_from_directory()`, `update_gist()`, `delete_gist()`, `delete_gists_batch()`
  - Robust HTTP error handling and rate limiting awareness

- **`gist_manager/cli.py`**: Click-based CLI interface
  - Main commands: `gist create`, `gist from-dir`, `gist update`, `gist delete`
  - Separate entry point: `quick-gist` for stdin input
  - Support for multiple output formats (text/json)

### Testing Structure
```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures (tokens, temp dirs, sample files)
├── test_config.py        # Tests for configuration management
├── test_core.py          # Tests for core functionality  
├── test_cli.py           # Tests for CLI commands
└── fixtures/
    ├── sample_files/     # Sample files for testing
    └── mock_responses/   # Mock GitHub API responses
```

### Package Configuration
- **`setup.py`**: Package definition with console script entry points
- **`pyproject.toml`**: Modern Python packaging configuration with test settings
- **`requirements.txt`**: Runtime dependencies (requests, click)
- **`requirements-dev.txt`**: Development dependencies (pytest, pytest-cov, responses)

## Key Implementation Requirements

### Authentication
Token search order:
1. `GITHUB_TOKEN` environment variable
2. `~/.gist-manager/config.json`
3. `./config.json`

### CLI Commands
```bash
# Create gist from specific files
gist create [FILES...] --description "desc" --public

# Create gist from directory with patterns
gist from-dir [DIRECTORY] --patterns "*.py" "*.md"

# List user's gists
gist list --public --limit 10

# Update existing gist
gist update GIST_ID [FILES...] --description "updated desc"

# Delete gist permanently
gist delete GIST_ID --force

# Quick gist from stdin
echo "content" | quick-gist --filename "file.ext"
```

### How to Upload Documents to Gists
When Claude needs to share documents or code with the user, use Gistly:

```bash
# Activate virtual environment first
source venv/bin/activate

# Create public gist with single file
gist create /path/to/document.md --description "Document Title" --public

# Create private gist (default)
gist create /path/to/document.md --description "Document Title"

# Create gist from multiple files
gist create file1.py file2.md --description "Multiple files" --public

# Create gist from directory
gist from-dir ./docs --patterns "*.md" --description "Documentation" --public

# Delete gists (use with caution)
gist delete temp123 draft456 --force

# Bulk delete from file
gist delete --from-file cleanup-list.txt --force
```

**Important**: Always use `source venv/bin/activate` before using gist commands to ensure the tool works correctly.

### Error Handling
- Clear authentication error messages
- File validation before API calls
- Rate limiting awareness
- Proper exit codes (0=success, 1=error)

## Testing Best Practices

### TDD Development Cycle
1. **Red**: Write a failing test first
2. **Green**: Write minimal code to make test pass
3. **Refactor**: Improve code while keeping tests green

### Key Testing Guidelines
- Use `pytest` as the testing framework
- Create fixtures in `conftest.py` for reusable test data
- Mock external API calls using `responses` library
- Use temporary directories for file operations
- Test both success and error cases
- Maintain high test coverage (>90%)

### Test Categories
- **Unit Tests**: Test individual functions/methods in isolation
- **Integration Tests**: Test component interactions
- **CLI Tests**: Test command-line interface using Click's testing utilities
- **Error Handling Tests**: Test failure scenarios and error messages

## Current Test Coverage

All modules have comprehensive test coverage:
- **config.py**: 10 tests covering token discovery, config file handling, error cases
- **core.py**: 65 tests covering GistManager, API integration, file operations, list functionality, delete functionality
- **cli.py**: 41 tests covering all CLI commands, options, error handling

Total: 116 tests, all passing with 78% coverage.

## Development Priority (for future enhancements)

1. **Additional Features** (following TDD)
   - ✅ List existing gists (COMPLETED)
   - ✅ Update/edit existing gists (COMPLETED)
   - ✅ Delete gists (COMPLETED)
   - ✅ Bulk operations (COMPLETED)

2. **Performance Optimizations**
   - Concurrent file reading for large directories
   - Progress bars for long operations
   - Caching of API responses

3. **Enhanced CLI Features**
   - Interactive mode
   - Configuration wizard
   - Better error reporting with suggestions

## Integration Notes

This tool is designed for Claude Code compatibility:
- Simple, direct commands
- Structured output with optional JSON format
- Appropriate exit codes for automation
- Clear error messages for debugging
- Comprehensive test suite for reliability