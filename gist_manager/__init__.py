from .core import GistManager, quick_gist
from .config import get_github_token, setup_config

__version__ = "1.0.0"
__all__ = ["GistManager", "quick_gist", "get_github_token", "setup_config"]