import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, Mock

from gist_manager.cli import main, quick_command, create, from_dir, config, update


class TestCreateCommand:
    """Test cases for 'gist create' command"""
    
    def test_create_command_basic(self, sample_python_file):
        """Test basic create command with single file"""
        runner = CliRunner()
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.create_gist.return_value = {
                "id": "test123",
                "html_url": "https://gist.github.com/test123",
                "description": "Test gist"
            }
            
            result = runner.invoke(create, [str(sample_python_file)])
            
            assert result.exit_code == 0
            assert "https://gist.github.com/test123" in result.output
            assert mock_manager.create_gist.called
    
    def test_create_command_multiple_files(self, sample_python_file, sample_markdown_file):
        """Test create command with multiple files"""
        runner = CliRunner()
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager._read_files_from_paths.return_value = {
                "test.py": "print('hello')",
                "README.md": "# Test"
            }
            mock_manager.create_gist.return_value = {
                "id": "test123",
                "html_url": "https://gist.github.com/test123"
            }
            
            result = runner.invoke(create, [
                str(sample_python_file),
                str(sample_markdown_file),
                "--description", "Multiple files test"
            ])
            
            assert result.exit_code == 0
            
            # Verify create_gist was called with correct parameters
            args, kwargs = mock_manager.create_gist.call_args
            assert kwargs["description"] == "Multiple files test"
            assert "test.py" in kwargs["files"]
            assert "README.md" in kwargs["files"]
    
    def test_create_command_public_flag(self, sample_python_file):
        """Test create command with --public flag"""
        runner = CliRunner()
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.create_gist.return_value = {"html_url": "https://gist.github.com/test123"}
            
            result = runner.invoke(create, [str(sample_python_file), "--public"])
            
            assert result.exit_code == 0
            
            args, kwargs = mock_manager.create_gist.call_args
            assert kwargs["public"] is True
    
    def test_create_command_json_output(self, sample_python_file):
        """Test create command with JSON output format"""
        runner = CliRunner()
        
        mock_response = {
            "id": "test123",
            "html_url": "https://gist.github.com/test123",
            "description": "Test gist"
        }
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.create_gist.return_value = mock_response
            
            result = runner.invoke(create, [str(sample_python_file), "--output", "json"])
            
            assert result.exit_code == 0
            
            # Parse output as JSON
            output_data = json.loads(result.output)
            assert output_data["id"] == "test123"
            assert output_data["html_url"] == "https://gist.github.com/test123"
    
    def test_create_command_nonexistent_file(self):
        """Test create command with nonexistent file"""
        runner = CliRunner()
        
        result = runner.invoke(create, ["/nonexistent/file.py"])
        
        assert result.exit_code != 0
        assert ("not found" in result.output.lower() or 
                "does not exist" in result.output.lower())
    
    def test_create_command_no_files(self):
        """Test create command with no files specified"""
        runner = CliRunner()
        
        result = runner.invoke(create, [])
        
        assert result.exit_code != 0
        assert "files" in result.output.lower()
    
    def test_create_command_handles_api_errors(self, sample_python_file):
        """Test create command handles API errors gracefully"""
        runner = CliRunner()
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.create_gist.side_effect = Exception("Authentication failed")
            
            result = runner.invoke(create, [str(sample_python_file)])
            
            assert result.exit_code != 0
            assert "Authentication failed" in result.output


class TestFromDirCommand:
    """Test cases for 'gist from-dir' command"""
    
    def test_from_dir_command_basic(self, sample_directory_with_files):
        """Test basic from-dir command"""
        runner = CliRunner()
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.create_from_directory.return_value = {
                "html_url": "https://gist.github.com/test123"
            }
            
            result = runner.invoke(from_dir, [
                str(sample_directory_with_files),
                "--patterns", "*.py"
            ])
            
            assert result.exit_code == 0
            assert "https://gist.github.com/test123" in result.output
            assert mock_manager.create_from_directory.called
    
    def test_from_dir_command_multiple_patterns(self, sample_directory_with_files):
        """Test from-dir command with multiple patterns"""
        runner = CliRunner()
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.create_from_directory.return_value = {
                "html_url": "https://gist.github.com/test123"
            }
            
            result = runner.invoke(from_dir, [
                str(sample_directory_with_files),
                "--patterns", "*.py",
                "--patterns", "*.md",
                "--description", "Multiple patterns test"
            ])
            
            assert result.exit_code == 0
            
            args, kwargs = mock_manager.create_from_directory.call_args
            assert kwargs["patterns"] == ["*.py", "*.md"]
            assert kwargs["description"] == "Multiple patterns test"
    
    def test_from_dir_command_current_directory(self):
        """Test from-dir command with current directory"""
        runner = CliRunner()
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.create_from_directory.return_value = {
                "html_url": "https://gist.github.com/test123"
            }
            
            result = runner.invoke(from_dir, ["--patterns", "*.py"])
            
            assert result.exit_code == 0
            
            args, kwargs = mock_manager.create_from_directory.call_args
            # Should use current directory if none specified
            assert str(kwargs["directory"]) == "."
    
    def test_from_dir_command_no_patterns(self, sample_directory_with_files):
        """Test from-dir command with no patterns specified"""
        runner = CliRunner()
        
        result = runner.invoke(from_dir, [str(sample_directory_with_files)])
        
        assert result.exit_code != 0
        assert "patterns" in result.output.lower()


class TestQuickCommand:
    """Test cases for 'quick-gist' command"""
    
    def test_quick_command_stdin_input(self):
        """Test quick-gist command with stdin input"""
        runner = CliRunner()
        
        with patch("gist_manager.cli.quick_gist") as mock_quick_gist:
            mock_quick_gist.return_value = "https://gist.github.com/test123"
            
            result = runner.invoke(quick_command, input="print('hello from stdin')")
            
            assert result.exit_code == 0
            assert "https://gist.github.com/test123" in result.output
            
            # Verify quick_gist was called with correct content
            mock_quick_gist.assert_called_once_with(
                content="print('hello from stdin')",
                filename="snippet.txt"
            )
    
    def test_quick_command_custom_filename(self):
        """Test quick-gist command with custom filename"""
        runner = CliRunner()
        
        with patch("gist_manager.cli.quick_gist") as mock_quick_gist:
            mock_quick_gist.return_value = "https://gist.github.com/test123"
            
            result = runner.invoke(quick_command, [
                "--filename", "custom.py"
            ], input="def hello(): pass")
            
            assert result.exit_code == 0
            
            args, kwargs = mock_quick_gist.call_args
            assert kwargs["filename"] == "custom.py"
    
    def test_quick_command_custom_description(self):
        """Test quick-gist command with custom description"""
        runner = CliRunner()
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.create_gist.return_value = {"html_url": "https://gist.github.com/test123"}
            
            result = runner.invoke(quick_command, [
                "--description", "Custom description"
            ], input="test content")
            
            assert result.exit_code == 0
            
            args, kwargs = mock_manager.create_gist.call_args
            assert kwargs["description"] == "Custom description"
    
    def test_quick_command_no_stdin(self):
        """Test quick-gist command with no stdin input"""
        runner = CliRunner()
        
        result = runner.invoke(quick_command, input="")
        
        assert result.exit_code != 0
        assert "content" in result.output.lower() or "empty" in result.output.lower()


class TestMainCommand:
    """Test cases for main CLI group"""
    
    def test_main_help(self):
        """Test main command help"""
        runner = CliRunner()
        
        result = runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        assert "gist" in result.output.lower()
        assert "create" in result.output
        assert "from-dir" in result.output
    
    def test_create_subcommand_help(self):
        """Test create subcommand help"""
        runner = CliRunner()
        
        result = runner.invoke(main, ["create", "--help"])
        
        assert result.exit_code == 0
        assert "description" in result.output
        assert "public" in result.output
        assert "output" in result.output


class TestConfigCommand:
    """Test cases for 'gist config' command"""
    
    def test_config_command_help(self):
        """Test config command help"""
        runner = CliRunner()
        
        result = runner.invoke(config, ["--help"])
        
        assert result.exit_code == 0
        assert "Configure GitHub token" in result.output
        assert "--reset" in result.output
    
    def test_config_existing_config(self):
        """Test config command when config already exists"""
        runner = CliRunner()
        
        with patch("gist_manager.cli.has_config", return_value=True), \
             patch("gist_manager.cli.get_config_path") as mock_path, \
             patch("gist_manager.cli._validate_github_token", return_value=True), \
             patch("gist_manager.config.get_github_token", return_value="test_token"):
            
            mock_path.return_value = "/home/test/.gist-manager/config.json"
            
            result = runner.invoke(config, input="n\n")
            
            assert result.exit_code == 0
            assert "Configuration already exists" in result.output
            assert "Token is valid" in result.output
    
    def test_config_new_setup_cancelled(self):
        """Test config command when user cancels setup"""
        runner = CliRunner()
        
        with patch("gist_manager.cli.has_config", return_value=False), \
             patch("gist_manager.cli._interactive_token_setup", side_effect=KeyboardInterrupt):
            
            result = runner.invoke(config)
            
            assert result.exit_code == 1
            assert "cancelled by user" in result.output


class TestUpdateCommand:
    """Test cases for gist update CLI command"""
    
    def test_update_command_basic_success(self, tmp_path, existing_gist_fixture, updated_gist_fixture):
        """Test basic update command with individual files"""
        runner = CliRunner()
        
        # Create test file
        test_file = tmp_path / "main.py"
        test_file.write_text("def main():\n    print('Updated content')")
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.get_gist.return_value = existing_gist_fixture
            mock_manager._read_files_from_paths.return_value = {"main.py": "def main():\n    print('Updated content')"}
            mock_manager.update_gist.return_value = updated_gist_fixture
            
            result = runner.invoke(update, [
                "abc123def456", 
                str(test_file), 
                "--description", "Updated version",
                "--force"  # Skip confirmation
            ])
            
            assert result.exit_code == 0
            assert "✅ Gist updated successfully!" in result.output
            assert "abc123def456" in result.output
            
            # Verify the manager was called correctly
            mock_manager.update_gist.assert_called_once()
    
    def test_update_command_with_url(self, tmp_path, existing_gist_fixture, updated_gist_fixture):
        """Test update command with full gist URL"""
        runner = CliRunner()
        
        test_file = tmp_path / "main.py" 
        test_file.write_text("updated content")
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.get_gist.return_value = existing_gist_fixture
            mock_manager._read_files_from_paths.return_value = {"main.py": "updated content"}
            mock_manager.update_gist.return_value = updated_gist_fixture
            
            result = runner.invoke(update, [
                "https://gist.github.com/testuser/abc123def456",
                str(test_file),
                "--force"
            ])
            
            assert result.exit_code == 0
            assert "✅ Gist updated successfully!" in result.output
    
    def test_update_command_from_directory(self, tmp_path, existing_gist_fixture, updated_gist_fixture):
        """Test update command from directory with patterns"""
        runner = CliRunner()
        
        # Create test files
        (tmp_path / "main.py").write_text("updated main")
        (tmp_path / "utils.py").write_text("new utils")
        (tmp_path / "README.md").write_text("# Updated README") 
        (tmp_path / "ignored.txt").write_text("should be ignored")
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.update_from_directory.return_value = updated_gist_fixture
            
            result = runner.invoke(update, [
                "abc123def456",
                "--from-dir", str(tmp_path),
                "--patterns", "*.py",
                "--patterns", "*.md",
                "--description", "Directory update",
                "--force"
            ])
            
            assert result.exit_code == 0
            assert "✅ Gist updated successfully!" in result.output
            
            # Verify manager was called correctly
            mock_manager.update_from_directory.assert_called_once_with(
                gist_id="abc123def456",
                directory=str(tmp_path),
                patterns=["*.py", "*.md"],
                description="Directory update",
                sync=False
            )
    
    def test_update_command_sync_mode(self, tmp_path, existing_gist_fixture, updated_gist_fixture):
        """Test update command with sync mode"""
        runner = CliRunner()
        
        (tmp_path / "main.py").write_text("updated main")
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.update_from_directory.return_value = updated_gist_fixture
            
            result = runner.invoke(update, [
                "abc123def456",
                "--from-dir", str(tmp_path),
                "--patterns", "*.py",
                "--sync",
                "--force"
            ])
            
            assert result.exit_code == 0
            
            # Verify sync=True was passed
            mock_manager.update_from_directory.assert_called_once()
            call_args = mock_manager.update_from_directory.call_args
            assert call_args[1]['sync'] is True
    
    def test_update_command_dry_run_individual_files(self, tmp_path, existing_gist_fixture):
        """Test update command dry run with individual files"""
        runner = CliRunner()
        
        test_file = tmp_path / "main.py"
        test_file.write_text("def main():\n    print('Updated content')")
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.get_gist.return_value = existing_gist_fixture
            mock_manager._read_files_from_paths.return_value = {
                "main.py": "def main():\n    print('Updated content')"
            }
            
            result = runner.invoke(update, [
                "abc123def456",
                str(test_file),
                "--dry-run"
            ])
            
            assert result.exit_code == 0
            assert "🔍 Dry run complete - no changes made" in result.output
            assert "📝 main.py (modified)" in result.output
            
            # Verify no update was actually performed
            mock_manager.update_gist.assert_not_called()
    
    def test_update_command_dry_run_directory(self, tmp_path, existing_gist_fixture):
        """Test update command dry run from directory"""
        runner = CliRunner()
        
        # Create files
        (tmp_path / "main.py").write_text("updated main")
        (tmp_path / "new_file.py").write_text("new content")
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.get_gist.return_value = existing_gist_fixture
            mock_manager._read_files_from_paths.return_value = {
                "main.py": "updated main",
                "new_file.py": "new content"
            }
            
            result = runner.invoke(update, [
                "abc123def456",
                "--from-dir", str(tmp_path),
                "--patterns", "*.py",
                "--dry-run"
            ])
            
            assert result.exit_code == 0
            assert "🔍 Dry run complete - no changes made" in result.output
            assert "📝 main.py (modified)" in result.output
            assert "➕ new_file.py (new file)" in result.output
    
    def test_update_command_add_remove_operations(self, tmp_path, existing_gist_fixture, updated_gist_fixture):
        """Test update command with explicit --add and --remove operations"""
        runner = CliRunner()
        
        new_file = tmp_path / "new_utils.py"
        new_file.write_text("def new_util(): pass")
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.get_gist.return_value = existing_gist_fixture
            mock_manager._read_files_from_paths.return_value = {"new_utils.py": "def new_util(): pass"}
            mock_manager.update_gist.return_value = updated_gist_fixture
            
            result = runner.invoke(update, [
                "abc123def456",
                "--add", str(new_file),
                "--remove", "README.md",
                "--force"
            ])
            
            assert result.exit_code == 0
            assert "✅ Gist updated successfully!" in result.output
            
            # Verify correct parameters were passed
            call_args = mock_manager.update_gist.call_args
            assert "new_utils.py" in call_args[1]['files']
            assert "README.md" in call_args[1]['files_to_remove']
    
    def test_update_command_json_output(self, tmp_path, existing_gist_fixture, updated_gist_fixture):
        """Test update command with JSON output"""
        runner = CliRunner()
        
        test_file = tmp_path / "main.py"
        test_file.write_text("updated content")
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.get_gist.return_value = existing_gist_fixture
            mock_manager._read_files_from_paths.return_value = {"main.py": "updated content"}
            mock_manager.update_gist.return_value = updated_gist_fixture
            
            result = runner.invoke(update, [
                "abc123def456",
                str(test_file),
                "--output", "json",
                "--force"
            ])
            
            assert result.exit_code == 0
            # Should contain JSON output
            import json
            output_data = json.loads(result.output)
            assert output_data["id"] == "abc123def456"
    
    def test_update_command_validation_errors(self, tmp_path):
        """Test update command input validation"""
        runner = CliRunner()
        
        # Create a dummy file
        dummy_file = tmp_path / "file.py"
        dummy_file.write_text("test")
        dummy_dir = tmp_path / "some_dir"
        dummy_dir.mkdir()
        
        # Test: both files and --from-dir
        result = runner.invoke(update, [
            "abc123def456", 
            str(dummy_file),
            "--from-dir", str(dummy_dir)
        ])
        assert result.exit_code == 1
        assert "Cannot use both individual files and --from-dir" in result.output
        
        # Test: --from-dir without --patterns
        result = runner.invoke(update, [
            "abc123def456",
            "--from-dir", str(dummy_dir)
        ])
        assert result.exit_code == 1
        assert "--patterns is required when using --from-dir" in result.output
        
        # Test: --sync without --from-dir
        result = runner.invoke(update, [
            "abc123def456",
            str(dummy_file), 
            "--sync"
        ])
        assert result.exit_code == 1
        assert "--sync can only be used with --from-dir" in result.output
    
    def test_update_command_no_changes_error(self, tmp_path, existing_gist_fixture):
        """Test update command when no changes are provided"""
        runner = CliRunner()
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.get_gist.return_value = existing_gist_fixture
            
            result = runner.invoke(update, [
                "abc123def456",
                "--force"
            ])
            
            assert result.exit_code == 1
            assert "Nothing to update" in result.output
    
    def test_update_command_api_error_handling(self, tmp_path, existing_gist_fixture):
        """Test update command handles API errors gracefully"""
        runner = CliRunner()
        
        test_file = tmp_path / "main.py"
        test_file.write_text("updated content")
        
        with patch("gist_manager.cli.GistManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.update_gist.side_effect = Exception("Gist not found: abc123def456")
            
            result = runner.invoke(update, [
                "abc123def456",
                str(test_file),
                "--force"
            ])
            
            assert result.exit_code == 1
            assert "Error: Gist not found: abc123def456" in result.output
    
    def test_update_command_help(self):
        """Test update command help text"""
        runner = CliRunner()
        
        result = runner.invoke(update, ["--help"])
        
        assert result.exit_code == 0
        assert "Update an existing gist" in result.output
        assert "--from-dir" in result.output
        assert "--patterns" in result.output
        assert "--sync" in result.output
        assert "--dry-run" in result.output