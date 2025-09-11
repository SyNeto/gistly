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
    
    def get_gist(self, gist_id: str) -> Dict:
        """
        Retrieve an existing GitHub Gist
        
        Args:
            gist_id: GitHub gist ID or URL
            
        Returns:
            Dict: Gist information including files and metadata
            
        Raises:
            Exception: If gist not found, permission denied, or retrieval fails
        """
        # Extract gist ID from URL if needed
        clean_gist_id = self._extract_gist_id(gist_id)
        
        try:
            response = requests.get(
                f"{self.base_url}/gists/{clean_gist_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise Exception("Authentication failed. Please check your GitHub token.")
            elif response.status_code == 403:
                error_data = response.json()
                if "rate limit" in error_data.get("message", "").lower():
                    raise Exception("Rate limit exceeded. Please try again later.")
                else:
                    raise Exception(f"Access forbidden: {error_data.get('message', 'Unknown error')}")
            elif response.status_code == 404:
                raise Exception(f"Gist not found: {clean_gist_id}")
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                raise Exception(f"Failed to retrieve gist: {response.status_code} - {error_data.get('message', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while retrieving gist: {e}")
    
    def _extract_gist_id(self, gist_id_or_url: str) -> str:
        """
        Extract gist ID from URL or return ID if already clean
        
        Args:
            gist_id_or_url: Gist ID or full GitHub gist URL
            
        Returns:
            str: Clean gist ID
        """
        # Handle GitHub gist URLs like https://gist.github.com/username/gist_id
        if "gist.github.com" in gist_id_or_url:
            parts = gist_id_or_url.rstrip('/').split('/')
            return parts[-1]  # Last part is the gist ID
        
        return gist_id_or_url.strip()
    
    def _prepare_update_payload(self, current_gist: Dict, 
                               new_files: Dict[str, str],
                               files_to_remove: List[str] = None,
                               description: str = None,
                               sync_mode: bool = False) -> Dict:
        """
        Prepare the payload for PATCH request to update gist
        
        Args:
            current_gist: Current gist data from API
            new_files: Dict of filename -> content for files to add/update
            files_to_remove: List of filenames to remove from gist
            description: New description (optional)
            sync_mode: If True, remove gist files not present in new_files
            
        Returns:
            Dict: Payload for PATCH request
        """
        payload = {}
        files_payload = {}
        
        # Update description if provided
        if description is not None:
            payload["description"] = description
        
        # Get current gist files
        current_files = current_gist.get("files", {})
        
        # Process new/updated files
        if new_files:
            for filename, content in new_files.items():
                # Check if file exists in gist
                if filename in current_files:
                    # Compare content
                    current_content = current_files[filename].get("content", "")
                    if current_content != content:
                        # Content is different, mark for update
                        files_payload[filename] = {"content": content}
                else:
                    # New file, add it
                    files_payload[filename] = {"content": content}
        
        # Process files to remove
        if files_to_remove:
            for filename in files_to_remove:
                if filename in current_files:
                    files_payload[filename] = None
        
        # Sync mode: remove gist files not present in new_files
        if sync_mode and new_files:
            for current_filename in current_files.keys():
                if current_filename not in new_files and current_filename not in files_payload:
                    files_payload[current_filename] = None
        
        # Only include files section if there are changes
        if files_payload:
            payload["files"] = files_payload
        
        return payload
    
    def update_gist(self, gist_id: str, files: Dict[str, str] = None, 
                    description: str = None, files_to_remove: List[str] = None) -> Dict:
        """
        Update an existing GitHub Gist
        
        Args:
            gist_id: GitHub gist ID or URL
            files: Dict of filename -> content for files to add/update
            description: New description (optional)
            files_to_remove: List of filenames to remove from gist
            
        Returns:
            Dict: Updated gist information
            
        Raises:
            Exception: If gist not found, permission denied, or update fails
        """
        # Get current gist data
        current_gist = self.get_gist(gist_id)
        
        # Prepare update payload
        payload = self._prepare_update_payload(
            current_gist=current_gist,
            new_files=files,
            files_to_remove=files_to_remove,
            description=description
        )
        
        # If no changes, return current gist
        if not payload:
            raise Exception("No changes detected. Nothing to update.")
        
        # Extract clean gist ID for API call
        clean_gist_id = self._extract_gist_id(gist_id)
        
        try:
            response = requests.patch(
                f"{self.base_url}/gists/{clean_gist_id}",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise Exception("Authentication failed. Please check your GitHub token.")
            elif response.status_code == 403:
                error_data = response.json()
                if "rate limit" in error_data.get("message", "").lower():
                    raise Exception("Rate limit exceeded. Please try again later.")
                else:
                    raise Exception(f"Access forbidden: {error_data.get('message', 'Unknown error')}")
            elif response.status_code == 404:
                raise Exception(f"Gist not found: {clean_gist_id}")
            elif response.status_code == 422:
                error_data = response.json()
                raise Exception(f"Invalid data: {error_data.get('message', 'Unknown validation error')}")
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                raise Exception(f"Failed to update gist: {response.status_code} - {error_data.get('message', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while updating gist: {e}")
    
    def update_from_directory(self, gist_id: str, directory: Union[str, Path], 
                             patterns: List[str], description: str = None,
                             sync: bool = False) -> Dict:
        """
        Update gist from directory files matching patterns
        
        Args:
            gist_id: GitHub gist ID or URL
            directory: Directory to scan
            patterns: File patterns to match (e.g., ["*.py", "*.md"])
            description: New description (optional)
            sync: If True, remove gist files not present in directory
            
        Returns:
            Dict: Updated gist information
            
        Raises:
            Exception: If directory not found, no matching files, or update fails
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
        
        # Get current gist for sync mode logic
        if sync:
            current_gist = self.get_gist(gist_id)
            payload = self._prepare_update_payload(
                current_gist=current_gist,
                new_files=files_data,
                description=description,
                sync_mode=True
            )
            
            # If no changes, return current gist
            if not payload:
                raise Exception("No changes detected. Nothing to update.")
            
            # Extract clean gist ID for API call
            clean_gist_id = self._extract_gist_id(gist_id)
            
            try:
                response = requests.patch(
                    f"{self.base_url}/gists/{clean_gist_id}",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    # Re-use error handling from update_gist
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    raise Exception(f"Failed to update gist: {response.status_code} - {error_data.get('message', 'Unknown error')}")
                    
            except requests.exceptions.RequestException as e:
                raise Exception(f"Network error while updating gist: {e}")
        else:
            # Non-sync mode: use regular update_gist method
            return self.update_gist(
                gist_id=gist_id,
                files=files_data,
                description=description
            )


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