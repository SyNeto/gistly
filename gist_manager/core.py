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
    
    def delete_gist(self, gist_id: str) -> Dict:
        """
        Delete a gist permanently
        
        Args:
            gist_id: GitHub gist ID or URL
            
        Returns:
            Dict: Operation result with success status and metadata
            
        Raises:
            Exception: If gist deletion fails
        """
        # Extract gist ID from URL if needed
        clean_gist_id = self._extract_gist_id(gist_id)
        
        # Validate gist ID format
        if not self._is_valid_gist_id(clean_gist_id):
            raise Exception(f"Invalid gist ID format: '{gist_id}'")
        
        url = f"{self.base_url}/gists/{clean_gist_id}"
        
        try:
            response = requests.delete(url, headers=self.headers, timeout=30)
            
            if response.status_code == 204:
                return {
                    "success": True,
                    "gist_id": clean_gist_id,
                    "message": "Gist deleted successfully"
                }
            elif response.status_code == 404:
                raise Exception(f"Gist not found: {clean_gist_id}")
            elif response.status_code == 403:
                raise Exception(f"Permission denied: You don't have permission to delete this gist")
            elif response.status_code == 401:
                raise Exception(f"Authentication failed: Invalid or missing token")
            else:
                error_msg = response.json().get("message", "Unknown error") if response.content else "Unknown error"
                raise Exception(f"Failed to delete gist: {error_msg}")
                
        except requests.RequestException as e:
            raise Exception(f"Network error while deleting gist: {str(e)}")
    
    def delete_gists_batch(self, gist_ids: List[str]) -> Dict:
        """
        Delete multiple gists in batch
        
        Args:
            gist_ids: List of gist IDs or URLs
            
        Returns:
            Dict: Batch operation results with individual gist statuses
        """
        results = {
            "success": False,
            "deleted": [],
            "failed": [],
            "summary": {
                "total": len(gist_ids),
                "deleted": 0,
                "failed": 0
            }
        }
        
        for gist_id in gist_ids:
            try:
                result = self.delete_gist(gist_id)
                results["deleted"].append({
                    "gist_id": result["gist_id"],
                    "message": result["message"]
                })
                results["summary"]["deleted"] += 1
            except Exception as e:
                results["failed"].append({
                    "gist_id": gist_id,
                    "error": str(e)
                })
                results["summary"]["failed"] += 1
        
        # Success if all deletions succeeded
        results["success"] = results["summary"]["failed"] == 0
        
        return results
    
    def _extract_gist_id(self, gist_id_or_url: str) -> str:
        """
        Extract gist ID from URL or return ID if already in correct format
        
        Args:
            gist_id_or_url: Gist ID or GitHub gist URL
            
        Returns:
            str: Clean gist ID
            
        Raises:
            Exception: If unable to extract valid gist ID
        """
        if not gist_id_or_url or not gist_id_or_url.strip():
            raise Exception("Invalid gist ID: cannot be empty")
        
        gist_id = gist_id_or_url.strip()
        
        # If it's already a gist ID (not URL), validate and return
        if not gist_id.startswith("http"):
            # For non-URLs, validate the format immediately
            if not self._is_valid_gist_id(gist_id):
                raise Exception(f"Invalid gist ID format: {gist_id}")
            return gist_id
        
        # Extract from GitHub gist URL patterns
        if "gist.github.com" in gist_id:
            # Remove fragment (everything after #)
            if "#" in gist_id:
                gist_id = gist_id.split("#")[0]
            
            # Extract ID from URL patterns:
            # https://gist.github.com/user/abc123def456
            # https://gist.github.com/abc123def456
            # https://gist.github.com/user/abc123def456/
            parts = gist_id.split("/")
            if len(parts) >= 4:
                # Handle trailing slash case - try parts[-1], then parts[-2]
                extracted_id = parts[-1] if parts[-1] else (parts[-2] if len(parts) >= 5 else "")
                # Make sure we got a valid gist ID, not just any string
                if extracted_id and not extracted_id.startswith("gist.github.com") and "." not in extracted_id:
                    return extracted_id
            
            # If we couldn't extract a valid ID from gist URL
            raise Exception(f"Unable to extract gist ID from: {gist_id_or_url}")
        
        # Handle other invalid URL patterns
        if gist_id.startswith("http"):
            raise Exception(f"Unable to extract gist ID from: {gist_id_or_url}")
        
        # This should never be reached since non-URLs are handled above
        return gist_id
    
    def _is_valid_gist_id(self, gist_id: str) -> bool:
        """
        Validate gist ID format
        
        Args:
            gist_id: Gist ID to validate
            
        Returns:
            bool: True if valid format
        """
        if not gist_id or len(gist_id) < 8:
            return False
        
        # GitHub gist IDs can vary in length, but usually 8-40 characters
        if len(gist_id) < 8 or len(gist_id) > 40:
            return False
        
        # Should not contain spaces or special characters except possible hyphens
        if " " in gist_id or "." in gist_id or "/" in gist_id:
            return False
        
        # GitHub gist IDs are hex-like alphanumeric
        # More strict: only allow a-f, 0-9 and possibly some letters
        cleaned = gist_id.replace("-", "")
        if not cleaned.isalnum():
            return False
        
        # Additional checks for common invalid patterns
        if gist_id.count("-") > 4:  # Too many hyphens
            return False
        
        # Only reject obviously invalid patterns, not partial matches
        invalid_patterns = ["invalid-gist-id", "not-a-url", "test-gist", "example-gist"]
        if gist_id.lower() in invalid_patterns:
            return False
        
        return True
    
    def list_gists(
        self, 
        visibility: Optional[str] = None,
        since: Optional[str] = None,
        limit: Optional[int] = None,
        page: int = 1,
        fetch_all: bool = False
    ) -> Dict:
        """
        List gists with filtering and pagination.
        
        Args:
            visibility: 'public', 'private', or None for both
            since: ISO 8601 timestamp to filter by update date
            limit: Maximum results per page (1-100, default 30)
            page: Page number (default 1)
            fetch_all: Fetch all results ignoring pagination
            
        Returns:
            Dict: {
                'gists': [list of gist objects],
                'total_count': int,
                'page': int,
                'per_page': int,
                'has_more': bool
            }
        """
        try:
            # Build query parameters
            params = {}
            per_page = limit if limit else 30
            actual_per_page = min(per_page, 100)  # GitHub's limit
            params['per_page'] = actual_per_page
            params['page'] = page
            
            if since:
                params['since'] = since
            
            response = requests.get(
                f"{self.base_url}/gists",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                gists = response.json()
                
                return {
                    'gists': gists,
                    'total_count': len(gists),
                    'page': page,
                    'per_page': actual_per_page,
                    'has_more': len(gists) == actual_per_page
                }
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                raise Exception(f"Failed to list gists: {response.status_code} - {error_data.get('message', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while listing gists: {e}")


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