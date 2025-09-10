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