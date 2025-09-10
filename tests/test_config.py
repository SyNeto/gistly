import pytest
import json
import os
import requests
from pathlib import Path
from unittest.mock import patch, mock_open, Mock

from gist_manager.config import get_github_token, setup_config, has_config, get_config_path, _validate_github_token


class TestGetGitHubToken:
    """Test cases for get_github_token function"""
    
    def test_get_token_from_environment_variable(self, clean_environment, mock_github_token):
        """Test that token is retrieved from GITHUB_TOKEN environment variable"""
        with patch.dict(os.environ, {'GITHUB_TOKEN': mock_github_token}):
            token = get_github_token()
            assert token == mock_github_token
    
    def test_get_token_from_home_config_file(self, clean_environment, mock_github_token):
        """Test that token is retrieved from ~/.gist-manager/config.json"""
        config_data = {"github_token": mock_github_token}
        config_content = json.dumps(config_data)
        
        with patch("gist_manager.config._read_token_from_config") as mock_read_token:
            # First call (home config) returns token, second call won't be made
            mock_read_token.side_effect = [mock_github_token, None]
            
            token = get_github_token()
            assert token == mock_github_token
            assert mock_read_token.call_count == 1
    
    def test_get_token_from_local_config_file(self, clean_environment, mock_github_token):
        """Test that token is retrieved from ./config.json"""
        with patch("gist_manager.config._read_token_from_config") as mock_read_token:
            # First call (home config) returns None, second call (local config) returns token
            mock_read_token.side_effect = [None, mock_github_token]
            
            token = get_github_token()
            assert token == mock_github_token
            assert mock_read_token.call_count == 2
    
    def test_token_search_priority(self, clean_environment, mock_github_token):
        """Test that environment variable takes priority over config files"""
        env_token = "env_token_123"
        config_token = "config_token_456"
        config_data = {"github_token": config_token}
        config_content = json.dumps(config_data)
        
        with patch.dict(os.environ, {'GITHUB_TOKEN': env_token}), \
             patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value=config_content):
            
            token = get_github_token()
            assert token == env_token  # Environment variable should win
    
    def test_no_token_found_raises_exception(self, clean_environment):
        """Test that exception is raised when no token is found"""
        with patch("gist_manager.config._read_token_from_config", return_value=None):
            with pytest.raises(Exception) as exc_info:
                get_github_token(interactive=False)
            
            error_msg = str(exc_info.value)
            assert "GitHub token not found" in error_msg
            assert "gist config" in error_msg
    
    def test_invalid_json_in_config_file(self, clean_environment):
        """Test handling of invalid JSON in config file"""
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value="invalid json"):
            
            with pytest.raises(Exception) as exc_info:
                get_github_token()
            
            assert "Invalid JSON" in str(exc_info.value)
    
    def test_missing_token_key_in_config(self, clean_environment):
        """Test handling of config file without github_token key"""
        config_data = {"other_key": "other_value"}
        config_content = json.dumps(config_data)
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value=config_content):
            
            with pytest.raises(Exception) as exc_info:
                get_github_token()
            
            assert "github_token key not found" in str(exc_info.value)


class TestSetupConfig:
    """Test cases for setup_config function"""
    
    def test_setup_config_creates_directory_and_file(self, tmp_path, mock_github_token):
        """Test that setup_config creates directory and config file"""
        config_dir = tmp_path / ".gist-manager"
        config_file = config_dir / "config.json"
        
        with patch("pathlib.Path.home", return_value=tmp_path):
            setup_config(mock_github_token)
            
            assert config_dir.exists()
            assert config_file.exists()
            
            config_data = json.loads(config_file.read_text())
            assert config_data["github_token"] == mock_github_token
    
    def test_setup_config_overwrites_existing_file(self, tmp_path, mock_github_token):
        """Test that setup_config overwrites existing config file"""
        config_dir = tmp_path / ".gist-manager"
        config_file = config_dir / "config.json"
        
        # Create existing config
        config_dir.mkdir()
        old_config = {"github_token": "old_token"}
        config_file.write_text(json.dumps(old_config))
        
        with patch("pathlib.Path.home", return_value=tmp_path):
            setup_config(mock_github_token)
            
            config_data = json.loads(config_file.read_text())
            assert config_data["github_token"] == mock_github_token
    
    def test_setup_config_handles_permission_errors(self, tmp_path, mock_github_token):
        """Test that setup_config handles permission errors gracefully"""
        with patch("pathlib.Path.home", return_value=tmp_path), \
             patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")):
            
            with pytest.raises(Exception) as exc_info:
                setup_config(mock_github_token)
            
            assert "Permission denied" in str(exc_info.value)


class TestConfigHelpers:
    """Test cases for configuration helper functions"""
    
    def test_has_config_exists(self, tmp_path, mock_github_token):
        """Test has_config returns True when config exists"""
        config_dir = tmp_path / ".gist-manager"
        config_file = config_dir / "config.json"
        config_dir.mkdir()
        config_file.write_text(json.dumps({"github_token": mock_github_token}))
        
        with patch("pathlib.Path.home", return_value=tmp_path):
            assert has_config() is True
    
    def test_has_config_not_exists(self, tmp_path):
        """Test has_config returns False when config doesn't exist"""
        with patch("pathlib.Path.home", return_value=tmp_path):
            assert has_config() is False
    
    def test_get_config_path(self, tmp_path):
        """Test get_config_path returns correct path"""
        with patch("pathlib.Path.home", return_value=tmp_path):
            expected_path = tmp_path / ".gist-manager" / "config.json"
            assert get_config_path() == expected_path
    
    @patch('requests.get')
    def test_validate_github_token_success(self, mock_get, mock_github_token):
        """Test token validation with valid token"""
        # Mock successful API responses
        mock_user_response = Mock()
        mock_user_response.status_code = 200
        
        mock_gist_response = Mock()
        mock_gist_response.status_code = 200
        
        mock_get.side_effect = [mock_user_response, mock_gist_response]
        
        result = _validate_github_token(mock_github_token)
        assert result is True
        assert mock_get.call_count == 2
    
    @patch('requests.get')
    def test_validate_github_token_invalid(self, mock_get, mock_github_token):
        """Test token validation with invalid token"""
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = _validate_github_token(mock_github_token)
        assert result is False
    
    @patch('requests.get')
    def test_validate_github_token_network_error(self, mock_get, mock_github_token):
        """Test token validation handles network errors"""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        result = _validate_github_token(mock_github_token)
        assert result is False
    
    def test_get_github_token_non_interactive(self, clean_environment):
        """Test get_github_token with interactive=False"""
        with patch("gist_manager.config._read_token_from_config", return_value=None):
            with pytest.raises(Exception) as exc_info:
                get_github_token(interactive=False)
            
            error_msg = str(exc_info.value)
            assert "gist config" in error_msg
            assert "GitHub token not found" in error_msg