# Gistly

A powerful CLI tool for managing GitHub Gists with ease. Create, organize, and share your code snippets directly from the command line.

## Features

- 🚀 **Simple CLI Interface** - Intuitive commands for all gist operations
- 📁 **Directory Support** - Create gists from entire directories with pattern matching
- ⚡ **Quick Gists** - Instantly create gists from stdin
- 🔧 **Flexible Configuration** - Multiple token sources (environment, config files)
- 📊 **Multiple Output Formats** - Text and JSON output options
- 🛡️ **Robust Error Handling** - Clear error messages and proper exit codes
- ✅ **Comprehensive Tests** - 41 tests with >90% coverage following TDD methodology

## Installation

### Prerequisites

- Python 3.7 or higher
- GitHub Personal Access Token with `gist` scope

### Install from Source

```bash
# Clone the repository
git clone <repository-url>
cd gistly

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies and package
pip install -r requirements.txt
pip install -e .
```

## Configuration

Gistly will automatically guide you through the setup process on first use. If no configuration is found, it will prompt you interactively.

### Automatic Setup (Recommended)

Simply run any command and follow the interactive setup:

```bash
# This will trigger automatic setup if no config exists
gist create myfile.py

# Or set up configuration explicitly
gist config
```

The tool will:
1. 🔍 **Check for existing tokens** (environment variable, config files)
2. 📋 **Guide you through token creation** with step-by-step instructions
3. ✅ **Validate your token** to ensure it works and has proper permissions
4. 💾 **Save securely** with restricted file permissions (600)

### Manual Configuration Methods

If you prefer manual setup, you have several options:

#### Method 1: Interactive Setup
```bash
gist config                    # First-time setup
gist config --reset           # Reset existing config
```

#### Method 2: Environment Variable
```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

#### Method 3: Configuration File
```bash
# The tool creates this automatically, but you can create it manually:
mkdir -p ~/.gist-manager
echo '{"github_token": "ghp_your_token_here"}' > ~/.gistly/config.json
chmod 600 ~/.gistly/config.json
```

### Token Discovery Priority

The tool searches for tokens in this order:
1. `GITHUB_TOKEN` environment variable
2. `~/.gistly/config.json` (secure storage)
3. `./config.json` (local project config)
4. Interactive prompt (if no token found)

### Security Features

- 🔒 **Secure file permissions** (600 - owner read/write only)
- ✅ **Token validation** before saving
- 🛡️ **Scope verification** (ensures `gist` permissions)
- 📁 **Standard location** (`~/.gistly/` following XDG patterns)

## Usage

### Create Gist from Files

```bash
# Single file
gist create script.py -d "Useful Python script"

# Multiple files
gist create main.py utils.py README.md -d "My Python project" --public

# With JSON output
gist create config.json -d "Configuration file" -o json
```

### Create Gist from Directory

```bash
# Python files only
gist from-dir ./src --patterns "*.py" -d "Source code"

# Multiple patterns
gist from-dir . --patterns "*.py" "*.md" "*.json" -d "Project files" --public

# Current directory
gist from-dir --patterns "*.sh" -d "Shell scripts"
```

### Quick Gists from stdin

```bash
# Basic usage
echo "print('Hello, World!')" | quick-gist -f "hello.py"

# From file
cat script.py | quick-gist -f "script.py" -d "Backup of my script"

# From command output
ls -la | quick-gist -f "directory_listing.txt" -d "Project structure"
```

## Command Reference

### `gist config`

Configure GitHub token for gist management.

```bash
gist config [OPTIONS]
```

**Options:**
- `--reset` - Reset existing configuration

**Examples:**
```bash
gist config                    # Interactive setup
gist config --reset           # Reset existing config
```

### `gist create`

Create a gist from one or more files.

```bash
gist create [FILES...] [OPTIONS]
```

**Options:**
- `-d, --description TEXT` - Description for the gist
- `-p, --public` - Make the gist public (default: private)
- `-o, --output [text|json]` - Output format (default: text)

### `gist from-dir`

Create a gist from files in a directory matching patterns.

```bash
gist from-dir [DIRECTORY] --patterns PATTERN [PATTERN...] [OPTIONS]
```

**Arguments:**
- `DIRECTORY` - Directory to search (default: current directory)

**Options:**
- `--patterns TEXT` - File patterns to include (required, can be used multiple times)
- `-d, --description TEXT` - Description for the gist
- `-p, --public` - Make the gist public (default: private)
- `-o, --output [text|json]` - Output format (default: text)

### `gist update`

Update an existing gist by adding, modifying, or removing files.

```bash
gist update GIST_ID [FILES...] [OPTIONS]
```

**Arguments:**
- `GIST_ID` - The ID or URL of the gist to update
- `FILES` - Local files to add or update in the gist

**Options:**
- `-d, --description TEXT` - Update gist description
- `--from-dir DIRECTORY` - Update from directory instead of individual files
- `--patterns TEXT` - File patterns when using --from-dir (e.g., "*.py" "*.md")
- `--add PATH` - Explicitly add new files
- `--remove TEXT` - Remove files from gist (by filename)
- `--sync` - Sync mode: remove gist files not present in directory
- `--dry-run` - Show what would be changed without making changes
- `--force` - Skip confirmation prompts
- `-o, --output [text|json]` - Output format (default: text)

**Examples:**
```bash
# Update individual files
gist update abc123def456 main.py utils.py

# Update from directory
gist update abc123def456 --from-dir ./src --patterns "*.py" "*.md"

# Sync directory (remove files not in directory)
gist update abc123def456 --from-dir ./src --patterns "*.py" --sync

# Explicit operations
gist update abc123def456 --add new_file.py --remove old_file.py

# Update description only
gist update abc123def456 --description "Updated version"

# Preview changes
gist update abc123def456 *.py --dry-run
```

### `quick-gist`

Create a quick gist from stdin.

```bash
quick-gist [OPTIONS]
```

**Options:**
- `-f, --filename TEXT` - Filename for the gist file (default: "snippet.txt")
- `-d, --description TEXT` - Description for the gist

## Examples

### First Time Usage

```bash
# Simply run any command - it will guide you through setup
gist create script.py -d "My first gist"

# Or configure explicitly
gist config
```

### Development Workflow

```bash
# Share your current work
gist create *.py -d "Work in progress" --public

# Backup configuration
gist from-dir ~/.config/myapp --patterns "*.conf" "*.json" -d "App configuration backup"

# Quick code snippet sharing
echo "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)" | \
  quick-gist -f "fibonacci.py" -d "Simple fibonacci implementation"

# Share command output
docker ps | quick-gist -f "running_containers.txt" -d "Current Docker containers"

# Update existing gist with new version
gist update abc123def456 script.py -d "Updated script with bug fixes"

# Sync project files to existing gist
gist update abc123def456 --from-dir ./src --patterns "*.py" "*.md" --sync
```

### Integration with Other Tools

```bash
# Git integration
git diff | quick-gist -f "changes.diff" -d "Proposed changes"

# Log sharing
tail -100 /var/log/myapp.log | quick-gist -f "app_errors.log" -d "Recent application errors"

# Config sharing
cat nginx.conf | quick-gist -f "nginx.conf" -d "Working nginx configuration"
```

## Development

### Setup Development Environment

```bash
# Clone and setup
git clone <repository-url>
cd gistly
python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=gist_manager

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run specific tests
pytest tests/test_core.py::TestGistManager::test_create_gist_success
```

### Project Structure

```
gistly/
├── gist_manager/           # Main package
│   ├── __init__.py        # Package initialization
│   ├── config.py          # Configuration management
│   ├── core.py            # Core GitHub API functionality
│   └── cli.py             # Command-line interface
├── tests/                  # Test suite
│   ├── conftest.py        # Shared test fixtures
│   ├── test_config.py     # Configuration tests
│   ├── test_core.py       # Core functionality tests
│   ├── test_cli.py        # CLI tests
│   └── fixtures/          # Test data
├── setup.py               # Package setup
├── pyproject.toml         # Modern Python packaging
├── requirements.txt       # Runtime dependencies
├── requirements-dev.txt   # Development dependencies
├── .gitignore            # Git ignore patterns
├── .env.example          # Environment variables example
├── CLAUDE.md             # Claude Code guidance
└── README.md             # This file
```

## Troubleshooting

### Common Issues

#### Authentication Errors
```
Error: Authentication failed. Please check your GitHub token.
```
- Verify your token is valid and has `gist` scope
- Check token is properly set in environment or config file
- Ensure token hasn't expired

#### Rate Limiting
```
Error: Rate limit exceeded. Please try again later.
```
- GitHub API has rate limits (5000 requests/hour for authenticated users)
- Wait a few minutes before trying again
- Check your token usage at: https://github.com/settings/personal-access-tokens

#### File Not Found
```
Error: File not found - /path/to/file.py
```
- Verify file paths are correct
- Check file permissions
- Use absolute paths if relative paths don't work

#### No Files Found
```
Error: No files found matching patterns ['*.py'] in directory /path/to/dir
```
- Check directory exists and contains matching files
- Verify pattern syntax (use quotes: `"*.py"`)
- Try different patterns or check file extensions

### Debug Mode

For detailed error information, you can inspect the full error traces by modifying the CLI commands to not catch exceptions during development.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow TDD: write tests first, then implementation
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -am 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- 📚 Documentation: This README and `CLAUDE.md` for Claude Code integration
- 🐛 Issues: Report bugs and request features on GitHub Issues
- 💡 Discussions: Share ideas and ask questions in GitHub Discussions

## Acknowledgments

- Built with [Click](https://click.palletsprojects.com/) for the CLI interface
- Uses [Requests](https://requests.readthedocs.io/) for GitHub API communication
- Tested with [pytest](https://pytest.org/) following TDD methodology
- Designed for seamless integration with [Claude Code](https://claude.ai/code)