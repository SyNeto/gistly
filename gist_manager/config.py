"""
Configuration management for GitHub Gist Manager
"""
import os
import json
import stat
import getpass
import requests
from pathlib import Path
from typing import Optional


def get_github_token(interactive: bool = True) -> str:
    """
    Get GitHub token from multiple sources in order of priority:
    1. GITHUB_TOKEN environment variable
    2. ~/.gist-manager/config.json
    3. ./config.json
    4. Interactive prompt (if interactive=True)
    
    Args:
        interactive: If True, prompt user for token if not found
    
    Returns:
        str: GitHub token
        
    Raises:
        Exception: If no token is found or configuration is invalid
    """
    # 1. Check environment variable
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    
    # 2. Check home directory config file
    home_config_path = Path.home() / ".gist-manager" / "config.json"
    token = _read_token_from_config(home_config_path)
    if token:
        return token
    
    # 3. Check local config file
    local_config_path = Path("config.json")
    token = _read_token_from_config(local_config_path)
    if token:
        return token
    
    # 4. Interactive configuration (if enabled)
    if interactive:
        return _interactive_token_setup()
    
    # No token found anywhere
    raise Exception(
        "GitHub token not found. Please run 'gist config' to set up your token, "
        "set GITHUB_TOKEN environment variable, or create a config file at "
        "~/.gist-manager/config.json with format: {\"github_token\": \"your_token_here\"}"
    )


def _read_token_from_config(config_path: Path) -> Optional[str]:
    """
    Read GitHub token from a config file
    
    Args:
        config_path: Path to the config file
        
    Returns:
        str or None: GitHub token if found and valid, None otherwise
        
    Raises:
        Exception: If config file exists but is invalid
    """
    if not config_path.exists():
        return None
    
    try:
        config_content = config_path.read_text()
        config_data = json.loads(config_content)
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON in config file {config_path}: {e}")
    
    if "github_token" not in config_data:
        raise Exception(f"github_token key not found in config file {config_path}")
    
    return config_data["github_token"]


def setup_config(token: str) -> None:
    """
    Create configuration file with GitHub token in home directory with secure permissions
    
    Args:
        token: GitHub token to save
        
    Raises:
        Exception: If unable to create config file or directory
    """
    try:
        config_dir = Path.home() / ".gist-manager"
        config_dir.mkdir(exist_ok=True)
        
        # Set secure permissions on directory (700 - rwx------)
        config_dir.chmod(stat.S_IRWXU)
        
        config_file = config_dir / "config.json"
        config_data = {"github_token": token}
        
        config_file.write_text(json.dumps(config_data, indent=2))
        
        # Set secure permissions on config file (600 - rw-------)
        config_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
        
    except PermissionError as e:
        raise Exception(f"Permission denied while creating config: {e}")
    except Exception as e:
        raise Exception(f"Failed to setup config: {e}")


def _interactive_token_setup() -> str:
    """
    Interactive setup for GitHub token with validation
    
    Returns:
        str: Validated GitHub token
        
    Raises:
        Exception: If user cancels or token validation fails
    """
    print("\n🔧 GitHub Gist Manager - Initial Setup")
    print("=" * 40)
    print("\nNo GitHub token found. Let's set one up!")
    print("\n📋 How to create a GitHub Personal Access Token:")
    print("1. Go to: https://github.com/settings/tokens")
    print("2. Click 'Generate new token (classic)'")
    print("3. Give it a name like 'Gist Manager'")
    print("4. Select the 'gist' scope ✅")
    print("5. Click 'Generate token'")
    print("6. Copy the token (it starts with 'ghp_')")
    
    while True:
        print("\n" + "─" * 40)
        token = getpass.getpass("📝 Paste your GitHub token here (hidden): ").strip()
        
        if not token:
            print("❌ Empty token. Please try again.")
            continue
            
        if not token.startswith(('ghp_', 'github_pat_')):
            print("⚠️  Token doesn't look like a GitHub token (should start with 'ghp_' or 'github_pat_')")
            continue_anyway = input("Continue anyway? (y/N): ").lower().strip()
            if continue_anyway != 'y':
                continue
        
        print("🔍 Validating token...")
        if _validate_github_token(token):
            print("✅ Token is valid!")
            
            # Ask if user wants to save it
            save_token = input("\n💾 Save token to ~/.gist-manager/config.json? (Y/n): ").strip()
            if save_token.lower() not in ('n', 'no'):
                try:
                    setup_config(token)
                    print(f"✅ Token saved securely to {Path.home() / '.gist-manager' / 'config.json'}")
                    print("🔒 File permissions set to 600 (user read/write only)")
                except Exception as e:
                    print(f"⚠️  Failed to save config: {e}")
                    print("You can save it manually later with 'gist config'")
            
            return token
        else:
            print("❌ Token validation failed. Please check:")
            print("   - Token is correct and complete")
            print("   - Token has 'gist' scope enabled")
            print("   - Your internet connection is working")
            
            retry = input("\n🔄 Try again? (Y/n): ").strip()
            if retry.lower() in ('n', 'no'):
                raise Exception("Token setup cancelled by user")


def _validate_github_token(token: str) -> bool:
    """
    Validate GitHub token by making a test API call
    
    Args:
        token: GitHub token to validate
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    try:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Test with a simple API call that requires gist scope
        response = requests.get(
            "https://api.github.com/user",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            # Check if token has gist scope by trying to list gists
            gist_response = requests.get(
                "https://api.github.com/gists",
                headers=headers,
                timeout=10
            )
            return gist_response.status_code == 200
        
        return False
        
    except Exception:
        return False


def has_config() -> bool:
    """
    Check if configuration already exists
    
    Returns:
        bool: True if config exists, False otherwise
    """
    config_path = Path.home() / ".gist-manager" / "config.json"
    return config_path.exists()


def get_config_path() -> Path:
    """
    Get the path to the configuration file
    
    Returns:
        Path: Path to config file
    """
    return Path.home() / ".gist-manager" / "config.json"