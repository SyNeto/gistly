"""
Command-line interface for GitHub Gist Manager
"""
import click
import json
import sys
from pathlib import Path
from typing import List

from .core import GistManager, quick_gist
from .config import setup_config, has_config, get_config_path, _validate_github_token, _interactive_token_setup


@click.group()
@click.version_option(version="1.0.0")
def main():
    """GitHub Gist Manager - CLI tool for managing GitHub Gists"""
    pass


@main.command()
@click.argument('files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--description', '-d', default="", help='Description for the gist')
@click.option('--public', '-p', is_flag=True, help='Make the gist public (default: private)')
@click.option('--output', '-o', type=click.Choice(['text', 'json']), default='text', 
              help='Output format')
def create(files, description, public, output):
    """Create a gist from one or more files
    
    FILES: One or more file paths to include in the gist
    
    Examples:
    
        gist create main.py utils.py -d "My Python project" --public
        
        gist create script.sh -d "Useful script" -o json
    """
    if not files:
        click.echo("Error: No files specified", err=True)
        sys.exit(1)
    
    try:
        # Initialize GistManager
        manager = GistManager()
        
        # Read files
        file_paths = [Path(f) for f in files]
        files_data = manager._read_files_from_paths(file_paths)
        
        # Create gist
        result = manager.create_gist(
            files=files_data,
            description=description,
            public=public
        )
        
        # Output result
        if output == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Gist created successfully!")
            click.echo(f"URL: {result['html_url']}")
            if description:
                click.echo(f"Description: {description}")
            click.echo(f"Public: {'Yes' if public else 'No'}")
            click.echo(f"Files: {', '.join(files_data.keys())}")
            
    except FileNotFoundError as e:
        click.echo(f"Error: File not found - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("from-dir")
@click.argument('directory', default=".", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--patterns', multiple=True, required=True,
              help='File patterns to include (e.g., "*.py" "*.md"). Can be specified multiple times.')
@click.option('--description', '-d', default="", help='Description for the gist')
@click.option('--public', '-p', is_flag=True, help='Make the gist public (default: private)')
@click.option('--output', '-o', type=click.Choice(['text', 'json']), default='text',
              help='Output format')
def from_dir(directory, patterns, description, public, output):
    """Create a gist from files in a directory matching patterns
    
    DIRECTORY: Directory to search for files (default: current directory)
    
    Examples:
    
        gist from-dir ./src --patterns "*.py" -d "Source code"
        
        gist from-dir . --patterns "*.py" "*.md" --public
    """
    if not patterns:
        click.echo("Error: No file patterns specified. Use --patterns option.", err=True)
        sys.exit(1)
    
    try:
        # Initialize GistManager
        manager = GistManager()
        
        # Create gist from directory
        result = manager.create_from_directory(
            directory=directory,
            patterns=list(patterns),
            description=description,
            public=public
        )
        
        # Output result
        if output == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Gist created successfully from directory!")
            click.echo(f"URL: {result['html_url']}")
            click.echo(f"Directory: {directory}")
            click.echo(f"Patterns: {', '.join(patterns)}")
            if description:
                click.echo(f"Description: {description}")
            click.echo(f"Public: {'Yes' if public else 'No'}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.option('--filename', '-f', default="snippet.txt", help='Filename for the gist file')
@click.option('--description', '-d', default="", help='Description for the gist')
def quick_command(filename, description):
    """Create a quick gist from stdin
    
    Reads content from stdin and creates a gist with it.
    
    Examples:
    
        echo "print('hello world')" | quick-gist -f "hello.py"
        
        cat script.py | quick-gist -f "script.py" -d "Useful script"
    """
    try:
        # Read content from stdin
        content = sys.stdin.read().strip()
        
        if not content:
            click.echo("Error: No content provided via stdin", err=True)
            sys.exit(1)
        
        if description:
            # Use GistManager directly for custom description
            manager = GistManager()
            files = {filename: content}
            result = manager.create_gist(files=files, description=description, public=False)
            gist_url = result["html_url"]
        else:
            # Use quick_gist function for default behavior
            gist_url = quick_gist(content=content, filename=filename)
        
        click.echo(f"Quick gist created successfully!")
        click.echo(f"URL: {gist_url}")
        click.echo(f"Filename: {filename}")
        if description:
            click.echo(f"Description: {description}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--reset', is_flag=True, help='Reset existing configuration')
def config(reset):
    """Configure GitHub token for gist management
    
    Set up your GitHub Personal Access Token for creating and managing gists.
    
    Examples:
    
        gist config                 # Interactive setup
        
        gist config --reset         # Reset existing config
    """
    try:
        config_exists = has_config()
        
        if config_exists and not reset:
            config_path = get_config_path()
            click.echo(f"✅ Configuration already exists at: {config_path}")
            click.echo("🔒 File permissions: 600 (user read/write only)")
            
            # Show some info about current config
            try:
                from .config import get_github_token
                token = get_github_token(interactive=False)
                if _validate_github_token(token):
                    click.echo("✅ Token is valid and has gist permissions")
                else:
                    click.echo("⚠️  Token validation failed - you may need to reset your config")
            except Exception:
                click.echo("⚠️  Could not validate existing token")
            
            if not click.confirm("\n🔄 Do you want to reconfigure?"):
                click.echo("Configuration unchanged.")
                return
        
        # Run interactive setup
        click.echo("\n🔧 Starting interactive configuration...")
        token = _interactive_token_setup()
        
        click.echo("\n✅ Configuration complete!")
        click.echo("🎉 You can now use 'gist create', 'gist from-dir', and 'quick-gist' commands!")
        
    except KeyboardInterrupt:
        click.echo("\n\n❌ Configuration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ Configuration failed: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()