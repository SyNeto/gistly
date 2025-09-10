"""
Core functionality for GitHub Gist Manager
"""
import requests
import json
from pathlib import Path
from typing import Dict, List, Union, Optional
from .config import get_github_token


class GistManager:
    """Main class for managing GitHub Gists"""
    
    def __init__(self, token: Optional[str] = None, interactive: bool = True):
        """
        Initialize GistManager with GitHub token
        
        Args:
            token: GitHub token. If not provided, will auto-discover from config
            interactive: If True, will prompt for token if not found
            
        Raises:
            Exception: If no token is found
        """
        if token:
            self.token = token
        else:
            self.token = get_github_token(interactive=interactive)
        
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    def create_gist(self, files: Dict[str, str], description: str = "", public: bool = False) -> Dict:
        """
        Create a new GitHub Gist
        
        Args:
            files: Dictionary with filename as key and content as value
            description: Gist description
            public: Whether the gist should be public
            
        Returns:
            Dict: GitHub API response with gist information
            
        Raises:
            Exception: If gist creation fails
        """
        if not files:
            raise Exception("At least one file is required to create a gist")
        
        # Format files for GitHub API
        gist_files = {}
        for filename, content in files.items():
            gist_files[filename] = {"content": content}
        
        payload = {
            "description": description,
            "public": public,
            "files": gist_files
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/gists",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                return response.json()
            elif response.status_code == 401:
                raise Exception("Authentication failed. Please check your GitHub token.")
            elif response.status_code == 403:
                error_data = response.json()
                if "rate limit" in error_data.get("message", "").lower():
                    raise Exception("Rate limit exceeded. Please try again later.")
                else:
                    raise Exception(f"Access forbidden: {error_data.get('message', 'Unknown error')}")
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                raise Exception(f"Failed to create gist: {response.status_code} - {error_data.get('message', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while creating gist: {e}")
    
    def _read_files_from_paths(self, file_paths: List[Union[str, Path]]) -> Dict[str, str]:
        """
        Read files from filesystem and return as dictionary
        
        Args:
            file_paths: List of file paths to read
            
        Returns:
            Dict: filename -> content mapping
            
        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If file can't be read due to encoding issues
        """
        files_data = {}
        
        for file_path in file_paths:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {path_obj}")
            
            try:
                content = path_obj.read_text(encoding='utf-8')
                filename = path_obj.name
                files_data[filename] = content
            except UnicodeDecodeError:
                raise Exception(f"Unable to read file {path_obj}: encoding error. Only text files are supported.")
            except Exception as e:
                raise Exception(f"Error reading file {path_obj}: {e}")
        
        return files_data
    
    def create_from_directory(self, directory: Union[str, Path], patterns: List[str], description: str = "", public: bool = False) -> Dict:
        """
        Create gist from files in a directory matching given patterns
        
        Args:
            directory: Directory path to search
            patterns: List of glob patterns (e.g., ["*.py", "*.md"])
            description: Gist description
            public: Whether the gist should be public
            
        Returns:
            Dict: GitHub API response with gist information
            
        Raises:
            Exception: If no matching files found or gist creation fails
        """
        directory_path = Path(directory)
        
        if not directory_path.exists() or not directory_path.is_dir():
            raise Exception(f"Directory not found: {directory_path}")
        
        # Find all files matching patterns
        matching_files = []
        for pattern in patterns:
            matching_files.extend(directory_path.glob(pattern))
        
        # Remove duplicates and filter out directories
        matching_files = [f for f in set(matching_files) if f.is_file()]
        
        if not matching_files:
            raise Exception(f"No files found matching patterns {patterns} in directory {directory_path}")
        
        # Read file contents
        files_data = self._read_files_from_paths(matching_files)
        
        # Create the gist
        return self.create_gist(files=files_data, description=description, public=public)


def quick_gist(content: str, filename: str = "snippet.txt") -> str:
    """
    Quickly create a gist with given content
    
    Args:
        content: Content to put in the gist
        filename: Filename for the gist file
        
    Returns:
        str: URL of the created gist
        
    Raises:
        Exception: If gist creation fails
    """
    manager = GistManager()
    
    files = {filename: content}
    result = manager.create_gist(files=files, description=f"Quick gist: {filename}", public=False)
    
    return result["html_url"]