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


@main.command()
@click.argument('gist_id', required=True)
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--description', '-d', help='Update gist description')
@click.option('--from-dir', type=click.Path(exists=True, file_okay=False), 
              help='Update from directory instead of individual files')
@click.option('--patterns', multiple=True, 
              help='File patterns when using --from-dir (e.g., "*.py" "*.md")')
@click.option('--add', multiple=True, type=click.Path(exists=True), 
              help='Explicitly add new files')
@click.option('--remove', multiple=True, 
              help='Remove files from gist (by filename)')
@click.option('--sync', is_flag=True, 
              help='Sync mode: remove gist files not present in directory')
@click.option('--dry-run', is_flag=True, 
              help='Show what would be changed without making changes')
@click.option('--force', is_flag=True, 
              help='Skip confirmation prompts')
@click.option('--output', '-o', type=click.Choice(['text', 'json']), default='text', 
              help='Output format')
def update(gist_id, files, description, from_dir, patterns, add, remove, sync, dry_run, force, output):
    """Update an existing gist
    
    GIST_ID: The ID or URL of the gist to update
    FILES: Local files to add or update in the gist
    
    Examples:
    
        # Update individual files
        gist update abc123def456 main.py utils.py
        
        # Update from directory
        gist update abc123def456 --from-dir ./src --patterns "*.py" "*.md"
        
        # Sync directory (remove files not in directory)
        gist update abc123def456 --from-dir ./src --patterns "*.py" --sync
        
        # Explicit operations
        gist update abc123def456 --add new_file.py --remove old_file.py
        
        # Update description only
        gist update abc123def456 --description "Updated version"
        
        # Preview changes
        gist update abc123def456 *.py --dry-run
    """
    try:
        # Initialize GistManager
        manager = GistManager()
        
        # Validate input combinations
        if from_dir and files:
            click.echo("Error: Cannot use both individual files and --from-dir", err=True)
            sys.exit(1)
        
        if from_dir and not patterns:
            click.echo("Error: --patterns is required when using --from-dir", err=True)
            sys.exit(1)
            
        if sync and not from_dir:
            click.echo("Error: --sync can only be used with --from-dir", err=True)
            sys.exit(1)
        
        # Collect files to process
        files_to_update = {}
        files_to_remove_list = list(remove) if remove else []
        
        # Process individual files
        if files:
            file_paths = [Path(f) for f in files]
            files_to_update = manager._read_files_from_paths(file_paths)
        
        # Process --add files
        if add:
            add_paths = [Path(f) for f in add]
            add_files = manager._read_files_from_paths(add_paths)
            files_to_update.update(add_files)
        
        # Process directory
        if from_dir:
            if dry_run:
                click.echo(f"Analyzing gist {gist_id}...")
                current_gist = manager.get_gist(gist_id)
                click.echo(f"✓ Gist found: \"{current_gist.get('description', 'No description')}\" ({len(current_gist.get('files', {}))} files)")
                
                click.echo(f"\nScanning directory {from_dir} with patterns: {', '.join(patterns)}")
                
                # Find matching files
                directory_path = Path(from_dir)
                matching_files = []
                for pattern in patterns:
                    matching_files.extend(directory_path.glob(pattern))
                matching_files = [f for f in set(matching_files) if f.is_file()]
                
                if not matching_files:
                    click.echo(f"No files found matching patterns {list(patterns)} in directory {from_dir}")
                    sys.exit(1)
                
                click.echo(f"Found {len(matching_files)} matching files: {', '.join(f.name for f in matching_files)}")
                
                # Read files and prepare changes
                files_data = manager._read_files_from_paths(matching_files)
                current_files = current_gist.get("files", {})
                
                click.echo("\nChanges to be made:")
                changes_found = False
                for filename, content in files_data.items():
                    if filename in current_files:
                        if current_files[filename].get("content", "") != content:
                            click.echo(f"  📝 {filename} (modified)")
                            changes_found = True
                    else:
                        click.echo(f"  ➕ {filename} (new file)")
                        changes_found = True
                
                if sync:
                    for current_filename in current_files.keys():
                        if current_filename not in files_data:
                            click.echo(f"  ❌ {current_filename} (would be removed)")
                            changes_found = True
                
                if not changes_found:
                    click.echo("  No changes detected")
                
                click.echo(f"\n🔍 Dry run complete - no changes made")
                return
            else:
                result = manager.update_from_directory(
                    gist_id=gist_id,
                    directory=from_dir,
                    patterns=list(patterns),
                    description=description,
                    sync=sync
                )
        else:
            # Dry run for individual files
            if dry_run:
                if not files_to_update and not files_to_remove_list and description is None:
                    click.echo("Error: Nothing to update", err=True)
                    sys.exit(1)
                
                click.echo(f"Analyzing gist {gist_id}...")
                current_gist = manager.get_gist(gist_id)
                click.echo(f"✓ Gist found: \"{current_gist.get('description', 'No description')}\" ({len(current_gist.get('files', {}))} files)")
                
                click.echo("\nChanges to be made:")
                changes_found = False
                
                if description is not None:
                    click.echo(f"  📄 Description: \"{description}\"")
                    changes_found = True
                
                current_files = current_gist.get("files", {})
                for filename, content in files_to_update.items():
                    if filename in current_files:
                        if current_files[filename].get("content", "") != content:
                            click.echo(f"  📝 {filename} (modified)")
                            changes_found = True
                    else:
                        click.echo(f"  ➕ {filename} (new file)")
                        changes_found = True
                
                for filename in files_to_remove_list:
                    if filename in current_files:
                        click.echo(f"  ❌ {filename} (would be removed)")
                        changes_found = True
                
                if not changes_found:
                    click.echo("  No changes detected")
                
                click.echo(f"\n🔍 Dry run complete - no changes made")
                return
            
            # Regular update
            if not files_to_update and not files_to_remove_list and description is None:
                click.echo("Error: Nothing to update", err=True)
                sys.exit(1)
            
            # Confirmation prompt (unless --force)
            if not force and not dry_run:
                if not click.confirm(f"Update gist {gist_id}?"):
                    click.echo("Update cancelled.")
                    return
            
            result = manager.update_gist(
                gist_id=gist_id,
                files=files_to_update if files_to_update else None,
                description=description,
                files_to_remove=files_to_remove_list if files_to_remove_list else None
            )
        
        # Output results
        if output == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo("✅ Gist updated successfully!")
            click.echo(f"🔗 URL: {result['html_url']}")
            if result.get('description'):
                click.echo(f"📄 Description: {result['description']}")
            click.echo(f"📁 Files: {len(result.get('files', {}))} total")
            
            # Show revision info if available
            if 'history' in result and result['history']:
                click.echo(f"📊 Revision: {len(result['history'])} (new revision created)")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('gist_ids', nargs=-1, required=False)
@click.option('--force', is_flag=True, 
              help='Skip confirmation prompts and delete immediately')
@click.option('--from-file', type=click.Path(exists=True), 
              help='Read gist IDs from file (one per line)')
@click.option('--dry-run', is_flag=True, 
              help='Show what would be deleted without actually deleting')
@click.option('--quiet', '-q', is_flag=True, 
              help='Minimal output, only show errors')
@click.option('--output', '-o', type=click.Choice(['text', 'json']), default='text',
              help='Output format')
def delete(gist_ids, force, from_file, dry_run, quiet, output):
    """Delete one or more gists permanently
    
    GIST_IDS: One or more gist IDs or URLs to delete
    
    ⚠️  WARNING: This action is irreversible!
    All files, history, and metadata will be permanently lost.
    
    Examples:
    
        # Delete single gist
        gist delete abc123def456
        
        # Delete multiple gists
        gist delete abc123def456 xyz789abc012 mno345pqr678
        
        # Force delete without confirmation
        gist delete abc123def456 --force
        
        # Delete gists listed in file
        gist delete --from-file gists-to-delete.txt
        
        # Preview what would be deleted
        gist delete abc123def456 xyz789abc012 --dry-run
        
        # Quiet mode (minimal output)
        gist delete abc123def456 --quiet --force
        
        # JSON output for scripting
        gist delete abc123def456 --force --output json
    """
    try:
        # Collect all gist IDs
        all_gist_ids = list(gist_ids)
        
        # Read additional IDs from file if specified
        if from_file:
            with open(from_file, 'r') as f:
                file_ids = [line.strip() for line in f if line.strip()]
                all_gist_ids.extend(file_ids)
        
        if not all_gist_ids:
            click.echo("Error: No gist IDs specified", err=True)
            sys.exit(1)
        
        # Initialize GistManager
        manager = GistManager()
        
        # Handle single vs batch deletion
        if len(all_gist_ids) == 1:
            gist_id = all_gist_ids[0]
            
            if dry_run:
                # Dry run: just show what would be deleted
                try:
                    # We can't get gist info without making API call, so just show the ID
                    if output == 'json':
                        result = {
                            "operation": "delete",
                            "dry_run": True,
                            "gist_id": gist_id,
                            "message": "Would delete this gist"
                        }
                        click.echo(json.dumps(result, indent=2))
                    else:
                        click.echo(f"🔍 DRY RUN: Would delete gist {gist_id}")
                        click.echo("\nTo actually delete this gist, run:")
                        click.echo(f"  gist delete {gist_id}")
                except Exception as e:
                    click.echo(f"Error: {e}", err=True)
                    sys.exit(1)
                return
            
            # Show confirmation unless force is used
            if not force and not quiet:
                click.echo(f"⚠️  WARNING: This will permanently delete the gist!")
                click.echo(f"\nGist ID: {gist_id}")
                click.echo("\nThis action CANNOT be undone. All files and history will be lost.")
                
                if not click.confirm("Type 'yes' to confirm deletion", default=False):
                    click.echo("Deletion cancelled.")
                    return
            
            # Delete the gist
            result = manager.delete_gist(gist_id)
            
            if output == 'json':
                response = {
                    "operation": "delete",
                    "success": result["success"],
                    "gist_id": result["gist_id"],
                    "message": result["message"]
                }
                click.echo(json.dumps(response, indent=2))
            else:
                if not quiet:
                    click.echo(f"✅ Gist {result['gist_id']} deleted successfully!")
        
        else:
            # Batch deletion
            if dry_run:
                # Dry run: show what would be deleted
                if output == 'json':
                    result = {
                        "operation": "delete",
                        "dry_run": True,
                        "gists": [{"id": gid, "message": "Would delete"} for gid in all_gist_ids],
                        "total": len(all_gist_ids)
                    }
                    click.echo(json.dumps(result, indent=2))
                else:
                    click.echo(f"🔍 DRY RUN: Would delete {len(all_gist_ids)} gists")
                    click.echo("\nGists that would be deleted:")
                    for i, gid in enumerate(all_gist_ids, 1):
                        click.echo(f"  {i}. {gid}")
                    click.echo(f"\nTo actually delete these gists, run:")
                    click.echo(f"  gist delete {' '.join(all_gist_ids)}")
                return
            
            # Show batch confirmation unless force is used
            if not force and not quiet:
                click.echo(f"⚠️  WARNING: This will permanently delete {len(all_gist_ids)} gists!")
                click.echo(f"\nGists to delete:")
                for i, gid in enumerate(all_gist_ids, 1):
                    click.echo(f"  {i}. {gid}")
                click.echo("\nThis action CANNOT be undone. All files and history will be lost.")
                
                confirm_text = "DELETE ALL" if len(all_gist_ids) > 1 else "DELETE"
                user_input = click.prompt(f"Type '{confirm_text}' to confirm", default="", show_default=False)
                if user_input != confirm_text:
                    click.echo("Deletion cancelled.")
                    return
            
            # Delete all gists
            result = manager.delete_gists_batch(all_gist_ids)
            
            if output == 'json':
                click.echo(json.dumps(result, indent=2))
            else:
                if not quiet:
                    if result["success"]:
                        click.echo(f"✅ All {result['summary']['deleted']} gists deleted successfully!")
                    else:
                        click.echo(f"⚠️  Batch deletion completed with some errors:")
                        click.echo(f"  ✅ Deleted: {result['summary']['deleted']}")
                        click.echo(f"  ❌ Failed: {result['summary']['failed']}")
                        
                        if result["failed"]:
                            click.echo("\nErrors:")
                            for failed in result["failed"]:
                                click.echo(f"  {failed['gist_id']}: {failed['error']}")
    
    except Exception as e:
        if output == 'json':
            error_response = {
                "operation": "delete",
                "success": False,
                "error": str(e)
            }
            click.echo(json.dumps(error_response, indent=2))
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()