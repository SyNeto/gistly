import pytest
import json
import responses
from pathlib import Path
from unittest.mock import patch, mock_open

from gist_manager.core import GistManager, quick_gist


class TestGistManager:
    """Test cases for GistManager class"""
    
    def test_gist_manager_initializes_with_token(self, mock_github_token):
        """Test that GistManager initializes with provided token"""
        manager = GistManager(token=mock_github_token)
        assert manager.token == mock_github_token
    
    def test_gist_manager_auto_discovers_token(self, mock_github_token):
        """Test that GistManager auto-discovers token when not provided"""
        with patch("gist_manager.core.get_github_token", return_value=mock_github_token):
            manager = GistManager()
            assert manager.token == mock_github_token
    
    def test_gist_manager_raises_exception_for_missing_token(self):
        """Test that GistManager raises exception when no token available"""
        with patch("gist_manager.core.get_github_token", side_effect=Exception("No token found")):
            with pytest.raises(Exception) as exc_info:
                GistManager()
            assert "No token found" in str(exc_info.value)
    
    @responses.activate
    def test_create_gist_success(self, mock_github_token, mock_gist_response):
        """Test successful gist creation"""
        responses.add(
            responses.POST,
            "https://api.github.com/gists",
            json=mock_gist_response,
            status=201
        )
        
        manager = GistManager(token=mock_github_token)
        files_data = {"test.py": "print('hello world')"}
        
        result = manager.create_gist(
            files=files_data,
            description="Test gist",
            public=False
        )
        
        assert result["id"] == mock_gist_response["id"]
        assert result["html_url"] == mock_gist_response["html_url"]
        assert result["description"] == mock_gist_response["description"]
        
        # Verify request was made correctly
        assert len(responses.calls) == 1
        request_data = json.loads(responses.calls[0].request.body)
        assert request_data["description"] == "Test gist"
        assert request_data["public"] is False
        assert "test.py" in request_data["files"]
    
    @responses.activate
    def test_create_gist_authentication_error(self, mock_github_token):
        """Test gist creation with authentication error"""
        responses.add(
            responses.POST,
            "https://api.github.com/gists",
            json={"message": "Bad credentials"},
            status=401
        )
        
        manager = GistManager(token=mock_github_token)
        files_data = {"test.py": "print('hello world')"}
        
        with pytest.raises(Exception) as exc_info:
            manager.create_gist(files=files_data, description="Test")
        
        assert "Authentication failed" in str(exc_info.value)
    
    @responses.activate
    def test_create_gist_rate_limit_error(self, mock_github_token):
        """Test gist creation with rate limit error"""
        responses.add(
            responses.POST,
            "https://api.github.com/gists",
            json={"message": "API rate limit exceeded"},
            status=403
        )
        
        manager = GistManager(token=mock_github_token)
        files_data = {"test.py": "print('hello world')"}
        
        with pytest.raises(Exception) as exc_info:
            manager.create_gist(files=files_data, description="Test")
        
        assert "Rate limit exceeded" in str(exc_info.value)
    
    def test_read_files_from_paths(self, sample_python_file, sample_markdown_file, mock_github_token):
        """Test reading files from file paths"""
        manager = GistManager(token=mock_github_token)
        file_paths = [sample_python_file, sample_markdown_file]
        
        files_data = manager._read_files_from_paths(file_paths)
        
        assert "test.py" in files_data
        assert "README.md" in files_data
        assert "print('hello world')" in files_data["test.py"]
        assert "# Test Project" in files_data["README.md"]
    
    def test_read_files_handles_nonexistent_file(self, mock_github_token):
        """Test that reading nonexistent file raises appropriate error"""
        manager = GistManager(token=mock_github_token)
        nonexistent_file = Path("/nonexistent/file.py")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            manager._read_files_from_paths([nonexistent_file])
        
        assert "file.py" in str(exc_info.value)
    
    def test_read_files_handles_encoding_errors(self, tmp_path, mock_github_token):
        """Test that reading files with encoding issues is handled gracefully"""
        # Create file with binary content
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b'\x80\x81\x82\x83')
        
        manager = GistManager(token=mock_github_token)
        
        with pytest.raises(Exception) as exc_info:
            manager._read_files_from_paths([binary_file])
        
        assert "encoding" in str(exc_info.value).lower()
    
    def test_create_from_directory_with_patterns(self, sample_directory_with_files, mock_github_token):
        """Test creating gist from directory with file patterns"""
        manager = GistManager(token=mock_github_token)
        
        with patch.object(manager, 'create_gist') as mock_create:
            mock_create.return_value = {"id": "test123", "html_url": "https://gist.github.com/test123"}
            
            result = manager.create_from_directory(
                directory=sample_directory_with_files,
                patterns=["*.py", "*.md"],
                description="Test directory gist"
            )
            
            # Verify create_gist was called
            assert mock_create.called
            args, kwargs = mock_create.call_args
            
            # Check that files dict contains expected files
            files = kwargs["files"]
            assert "main.py" in files
            assert "utils.py" in files
            assert "README.md" in files
            assert "CHANGELOG.md" in files
            
            # Check that non-matching files are excluded
            assert "data.json" not in files
            assert "image.png" not in files
    
    def test_create_from_directory_no_matching_files(self, tmp_path, mock_github_token):
        """Test creating gist from directory with no matching files"""
        # Create directory with no matching files
        (tmp_path / "data.json").write_text('{"key": "value"}')
        
        manager = GistManager(token=mock_github_token)
        
        with pytest.raises(Exception) as exc_info:
            manager.create_from_directory(
                directory=tmp_path,
                patterns=["*.py"],
                description="Test"
            )
        
        assert "No files found" in str(exc_info.value)
    
    @responses.activate
    def test_get_gist_success(self, mock_github_token, existing_gist_fixture):
        """Test successful gist retrieval"""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/abc123def456",
            json=existing_gist_fixture,
            status=200
        )
        
        manager = GistManager(token=mock_github_token)
        result = manager.get_gist("abc123def456")
        
        assert result["id"] == "abc123def456"
        assert result["description"] == "My Python Project"
        assert "main.py" in result["files"]
        assert "README.md" in result["files"]
        
        # Verify request was made correctly
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == "https://api.github.com/gists/abc123def456"
    
    @responses.activate
    def test_get_gist_with_url(self, mock_github_token, existing_gist_fixture):
        """Test gist retrieval with full URL"""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/abc123def456",
            json=existing_gist_fixture,
            status=200
        )
        
        manager = GistManager(token=mock_github_token)
        result = manager.get_gist("https://gist.github.com/testuser/abc123def456")
        
        assert result["id"] == "abc123def456"
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_get_gist_not_found(self, mock_github_token, gist_not_found_fixture):
        """Test gist retrieval when gist doesn't exist"""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/nonexistent",
            json=gist_not_found_fixture,
            status=404
        )
        
        manager = GistManager(token=mock_github_token)
        
        with pytest.raises(Exception) as exc_info:
            manager.get_gist("nonexistent")
        
        assert "Gist not found: nonexistent" in str(exc_info.value)
    
    @responses.activate
    def test_get_gist_authentication_error(self, mock_github_token, auth_error_fixture):
        """Test gist retrieval with authentication error"""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/abc123def456",
            json=auth_error_fixture,
            status=401
        )
        
        manager = GistManager(token=mock_github_token)
        
        with pytest.raises(Exception) as exc_info:
            manager.get_gist("abc123def456")
        
        assert "Authentication failed" in str(exc_info.value)
    
    def test_extract_gist_id_from_url(self, mock_github_token):
        """Test gist ID extraction from various URL formats"""
        manager = GistManager(token=mock_github_token)
        
        # Test various URL formats
        assert manager._extract_gist_id("abc123def456") == "abc123def456"
        assert manager._extract_gist_id("https://gist.github.com/user/abc123def456") == "abc123def456"
        assert manager._extract_gist_id("https://gist.github.com/user/abc123def456/") == "abc123def456"
    
    @responses.activate
    def test_update_gist_success(self, mock_github_token, existing_gist_fixture, updated_gist_fixture):
        """Test successful gist update"""
        # Mock GET request to fetch current gist
        responses.add(
            responses.GET,
            "https://api.github.com/gists/abc123def456",
            json=existing_gist_fixture,
            status=200
        )
        
        # Mock PATCH request to update gist
        responses.add(
            responses.PATCH,
            "https://api.github.com/gists/abc123def456",
            json=updated_gist_fixture,
            status=200
        )
        
        manager = GistManager(token=mock_github_token)
        files_to_update = {
            "main.py": "def main():\n    print('Hello Updated World')\n    print('New functionality')\n\nif __name__ == '__main__':\n    main()",
            "utils.py": "def helper():\n    return 'utility'"
        }
        
        result = manager.update_gist(
            gist_id="abc123def456",
            files=files_to_update,
            description="My Python Project - Updated"
        )
        
        assert result["id"] == "abc123def456"
        assert result["description"] == "My Python Project - Updated"
        assert "utils.py" in result["files"]  # New file added
        assert len(result["history"]) == 2  # New revision created
        
        # Verify requests were made correctly
        assert len(responses.calls) == 2
        assert responses.calls[0].request.url.endswith("/gists/abc123def456")  # GET
        assert responses.calls[1].request.url.endswith("/gists/abc123def456")  # PATCH
    
    @responses.activate
    def test_update_gist_no_changes(self, mock_github_token, existing_gist_fixture):
        """Test updating gist with no actual changes"""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/abc123def456",
            json=existing_gist_fixture,
            status=200
        )
        
        manager = GistManager(token=mock_github_token)
        
        # Try to update with same content
        files_to_update = {
            "main.py": "def main():\n    print('Hello World')\n\nif __name__ == '__main__':\n    main()"
        }
        
        with pytest.raises(Exception) as exc_info:
            manager.update_gist(
                gist_id="abc123def456",
                files=files_to_update
            )
        
        assert "No changes detected" in str(exc_info.value)
        assert len(responses.calls) == 1  # Only GET, no PATCH
    
    @responses.activate
    def test_update_gist_add_new_file(self, mock_github_token, existing_gist_fixture, updated_gist_fixture):
        """Test adding new file to existing gist"""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/abc123def456",
            json=existing_gist_fixture,
            status=200
        )
        
        responses.add(
            responses.PATCH,
            "https://api.github.com/gists/abc123def456",
            json=updated_gist_fixture,
            status=200
        )
        
        manager = GistManager(token=mock_github_token)
        
        result = manager.update_gist(
            gist_id="abc123def456",
            files={"utils.py": "def helper():\n    return 'utility'"}
        )
        
        assert result["id"] == "abc123def456"
        assert "utils.py" in result["files"]
        
        # Verify PATCH payload
        patch_request = json.loads(responses.calls[1].request.body)
        assert "files" in patch_request
        assert "utils.py" in patch_request["files"]
        assert patch_request["files"]["utils.py"]["content"] == "def helper():\n    return 'utility'"
    
    @responses.activate
    def test_update_gist_remove_files(self, mock_github_token, existing_gist_fixture, updated_gist_fixture):
        """Test removing files from gist"""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/abc123def456",
            json=existing_gist_fixture,
            status=200
        )
        
        responses.add(
            responses.PATCH,
            "https://api.github.com/gists/abc123def456",
            json=updated_gist_fixture,
            status=200
        )
        
        manager = GistManager(token=mock_github_token)
        
        result = manager.update_gist(
            gist_id="abc123def456",
            files_to_remove=["README.md"]
        )
        
        # Verify PATCH payload
        patch_request = json.loads(responses.calls[1].request.body)
        assert "files" in patch_request
        assert patch_request["files"]["README.md"] is None
    
    @responses.activate
    def test_update_gist_validation_error(self, mock_github_token, existing_gist_fixture, validation_error_fixture):
        """Test gist update with validation error"""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/abc123def456",
            json=existing_gist_fixture,
            status=200
        )
        
        responses.add(
            responses.PATCH,
            "https://api.github.com/gists/abc123def456",
            json=validation_error_fixture,
            status=422
        )
        
        manager = GistManager(token=mock_github_token)
        
        with pytest.raises(Exception) as exc_info:
            manager.update_gist(
                gist_id="abc123def456",
                files={"gistfile1.txt": "invalid name"}  # Invalid filename
            )
        
        assert "Invalid data" in str(exc_info.value)
    
    @responses.activate 
    def test_update_from_directory_success(self, tmp_path, mock_github_token, existing_gist_fixture, updated_gist_fixture):
        """Test updating gist from directory"""
        # Create test files
        (tmp_path / "main.py").write_text("def main():\n    print('Updated from directory')")
        (tmp_path / "utils.py").write_text("def helper():\n    return 'utility'")
        (tmp_path / "README.md").write_text("# Updated README")
        (tmp_path / "ignored.txt").write_text("This should be ignored")
        
        responses.add(
            responses.GET,
            "https://api.github.com/gists/abc123def456",
            json=existing_gist_fixture,
            status=200
        )
        
        responses.add(
            responses.PATCH,
            "https://api.github.com/gists/abc123def456",
            json=updated_gist_fixture,
            status=200
        )
        
        manager = GistManager(token=mock_github_token)
        
        result = manager.update_from_directory(
            gist_id="abc123def456",
            directory=tmp_path,
            patterns=["*.py", "*.md"],
            description="Updated from directory"
        )
        
        assert result["id"] == "abc123def456"
        
        # Verify correct files were processed (ignored.txt should not be included)
        patch_request = json.loads(responses.calls[1].request.body)
        files_in_request = patch_request["files"]
        
        # Should include Python and Markdown files, but not .txt
        assert "main.py" in files_in_request
        assert "utils.py" in files_in_request  
        assert "README.md" in files_in_request
        assert "ignored.txt" not in files_in_request
    
    @responses.activate
    def test_update_from_directory_sync_mode(self, tmp_path, mock_github_token, existing_gist_fixture, updated_gist_fixture):
        """Test updating gist from directory with sync mode"""
        # Create only main.py (README.md missing, should be removed in sync mode)
        (tmp_path / "main.py").write_text("def main():\n    print('Sync mode test')")
        
        responses.add(
            responses.GET,
            "https://api.github.com/gists/abc123def456",
            json=existing_gist_fixture,
            status=200
        )
        
        responses.add(
            responses.PATCH,
            "https://api.github.com/gists/abc123def456",
            json=updated_gist_fixture,
            status=200
        )
        
        manager = GistManager(token=mock_github_token)
        
        result = manager.update_from_directory(
            gist_id="abc123def456",
            directory=tmp_path,
            patterns=["*.py", "*.md"],
            sync=True
        )
        
        # Verify sync mode removes missing files
        patch_request = json.loads(responses.calls[1].request.body)
        files_in_request = patch_request["files"]
        
        assert "main.py" in files_in_request  # Updated
        assert "README.md" in files_in_request  # Should be null (removed)
        assert files_in_request["README.md"] is None


class TestQuickGist:
    """Test cases for quick_gist function"""
    
    @responses.activate
    def test_quick_gist_success(self, mock_gist_response):
        """Test successful quick gist creation"""
        responses.add(
            responses.POST,
            "https://api.github.com/gists",
            json=mock_gist_response,
            status=201
        )
        
        with patch("gist_manager.core.get_github_token", return_value="test_token"):
            result = quick_gist(
                content="print('quick test')",
                filename="quick.py"
            )
            
            assert result == mock_gist_response["html_url"]
            
            # Verify request was made correctly
            assert len(responses.calls) == 1
            request_data = json.loads(responses.calls[0].request.body)
            assert "quick.py" in request_data["files"]
            assert request_data["files"]["quick.py"]["content"] == "print('quick test')"
    
    def test_quick_gist_default_filename(self):
        """Test quick_gist with default filename"""
        with patch("gist_manager.core.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.create_gist.return_value = {"html_url": "https://gist.github.com/test"}
            
            result = quick_gist("test content")
            
            # Verify GistManager was created and used
            assert mock_manager_class.called
            assert mock_manager.create_gist.called
            
            args, kwargs = mock_manager.create_gist.call_args
            files = kwargs["files"]
            assert "snippet.txt" in files
            assert files["snippet.txt"] == "test content"
    
    def test_quick_gist_handles_errors(self):
        """Test that quick_gist handles errors from GistManager"""
        with patch("gist_manager.core.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.create_gist.side_effect = Exception("API Error")
            
            with pytest.raises(Exception) as exc_info:
                quick_gist("test content")
            
            assert "API Error" in str(exc_info.value)