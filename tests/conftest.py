import pytest
import json
import os
from pathlib import Path

@pytest.fixture
def mock_github_token():
    """Mock GitHub token for testing"""
    return "ghp_test_token_1234567890abcdef"

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary .gist-manager directory for testing"""
    config_dir = tmp_path / ".gist-manager"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def temp_config_file(temp_config_dir, mock_github_token):
    """Create temporary config.json file with mock token"""
    config_file = temp_config_dir / "config.json"
    config_data = {"github_token": mock_github_token}
    config_file.write_text(json.dumps(config_data))
    return config_file

@pytest.fixture
def sample_python_file(tmp_path):
    """Create a sample Python file for testing"""
    file_path = tmp_path / "test.py"
    file_path.write_text("print('hello world')\nprint('testing gist creation')")
    return file_path

@pytest.fixture
def sample_markdown_file(tmp_path):
    """Create a sample Markdown file for testing"""
    file_path = tmp_path / "README.md"
    file_path.write_text("# Test Project\n\nThis is a test markdown file.")
    return file_path

@pytest.fixture
def sample_directory_with_files(tmp_path):
    """Create a directory with multiple sample files"""
    # Python files
    (tmp_path / "main.py").write_text("def main():\n    print('main function')")
    (tmp_path / "utils.py").write_text("def helper():\n    return 'helper'")
    
    # Markdown files
    (tmp_path / "README.md").write_text("# Sample Project")
    (tmp_path / "CHANGELOG.md").write_text("## v1.0.0\n- Initial release")
    
    # Other files that shouldn't be included
    (tmp_path / "data.json").write_text('{"key": "value"}')
    (tmp_path / "image.png").write_bytes(b"fake image data")
    
    return tmp_path

@pytest.fixture
def mock_gist_response():
    """Mock successful GitHub Gist API response"""
    return {
        "id": "abc123def456",
        "html_url": "https://gist.github.com/testuser/abc123def456",
        "git_pull_url": "https://gist.github.com/abc123def456.git",
        "git_push_url": "https://gist.github.com/abc123def456.git",
        "description": "Test gist created via API",
        "public": False,
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "files": {
            "test.py": {
                "filename": "test.py",
                "type": "text/x-python",
                "language": "Python",
                "raw_url": "https://gist.githubusercontent.com/testuser/abc123def456/raw/test.py",
                "size": 42,
                "content": "print('hello world')"
            }
        },
        "owner": {
            "login": "testuser",
            "id": 12345
        }
    }

@pytest.fixture
def mock_gist_error_response():
    """Mock error response from GitHub API"""
    return {
        "message": "Bad credentials",
        "documentation_url": "https://docs.github.com/rest"
    }

@pytest.fixture
def clean_environment(monkeypatch):
    """Clean environment variables for testing"""
    # Remove GITHUB_TOKEN if it exists
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    return monkeypatch

# New fixtures for gist update functionality

@pytest.fixture
def existing_gist_fixture():
    """Fixture for existing gist response"""
    fixtures_dir = Path(__file__).parent / "fixtures" / "mock_responses"
    with open(fixtures_dir / "existing_gist.json") as f:
        return json.load(f)

@pytest.fixture
def updated_gist_fixture():
    """Fixture for updated gist response"""
    fixtures_dir = Path(__file__).parent / "fixtures" / "mock_responses"
    with open(fixtures_dir / "updated_gist.json") as f:
        return json.load(f)

@pytest.fixture
def gist_not_found_fixture():
    """Fixture for gist not found error response"""
    fixtures_dir = Path(__file__).parent / "fixtures" / "mock_responses"
    with open(fixtures_dir / "gist_not_found.json") as f:
        return json.load(f)

@pytest.fixture
def validation_error_fixture():
    """Fixture for validation error response"""
    fixtures_dir = Path(__file__).parent / "fixtures" / "mock_responses"
    with open(fixtures_dir / "validation_error.json") as f:
        return json.load(f)

@pytest.fixture
def auth_error_fixture():
    """Fixture for authentication error response"""
    fixtures_dir = Path(__file__).parent / "fixtures" / "mock_responses"
    with open(fixtures_dir / "auth_error.json") as f:
        return json.load(f)

@pytest.fixture
def gist_list_fixture():
    """Fixture for gist list API response"""
    fixtures_dir = Path(__file__).parent / "fixtures" / "mock_responses"
    with open(fixtures_dir / "gist_list.json") as f:
        return json.load(f)