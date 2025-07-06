#!/usr/bin/env python3
"""
Command Line Interface for Obsidian Project Sync
"""

import click
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .config import ProjectConfig
from .sync_manager import ObsidianSyncManager
from .init_project import ProjectInitializer

console = Console()


@click.group()
@click.version_option()
def main():
    """Obsidian Project Sync - Bidirectional synchronization tool"""
    pass


@main.command()
@click.option("--project-name", "-n", help="Project name for Obsidian vault path")
@click.option("--vault-path", "-v", help="Custom vault path (e.g., '10-Projects/my-project')")
@click.option("--notes-dir", "-d", default="notes", help="Local notes directory name")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing configuration")
def init(project_name: Optional[str], vault_path: Optional[str], notes_dir: str, force: bool):
    """Initialize Obsidian sync in current project"""
    try:
        initializer = ProjectInitializer()
        success = initializer.initialize_project(
            project_name=project_name,
            vault_path=vault_path,
            notes_dir=notes_dir,
            force=force
        )
        
        if success:
            rprint("✅ [green]Project initialized successfully![/green]")
            rprint("\n📝 Next steps:")
            rprint("1. Copy [cyan].env.example[/cyan] to [cyan].env[/cyan] and configure your API settings")
            rprint("2. Run [cyan]obsidian-sync test[/cyan] to verify connection")
            rprint("3. Run [cyan]obsidian-sync[/cyan] to start syncing")
        else:
            rprint("❌ [red]Failed to initialize project[/red]")
            sys.exit(1)
            
    except Exception as e:
        rprint(f"❌ [red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option("--watch", "-w", is_flag=True, help="Continuous monitoring mode")
@click.option("--interval", "-i", type=int, help="Sync interval in seconds (for watch mode)")
@click.option("--dry-run", "-n", is_flag=True, help="Show what would be synced without actual changes")
@click.option("--log-level", "-l", type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), 
              help="Override log level")
def sync(watch: bool, interval: Optional[int], dry_run: bool, log_level: Optional[str]):
    """Run synchronization between local notes and Obsidian vault"""
    try:
        config = ProjectConfig()
        
        if log_level:
            config._yaml_config.setdefault('logging', {})['level'] = log_level
        
        sync_manager = ObsidianSyncManager(config, dry_run=dry_run)
        
        if not _check_connection(sync_manager):
            sys.exit(1)
        
        if watch:
            rprint(f"👀 [blue]Starting continuous monitoring mode...[/blue]")
            if interval:
                rprint(f"⏰ Sync interval: {interval} seconds")
            sync_manager.watch_mode(interval)
        else:
            rprint("🔄 [blue]Running one-time synchronization...[/blue]")
            results = sync_manager.bidirectional_sync()
            _display_sync_results(results)
            
    except KeyboardInterrupt:
        rprint("\n👋 [yellow]Synchronization stopped by user[/yellow]")
    except Exception as e:
        rprint(f"❌ [red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option("--verbose", "-v", is_flag=True, help="Show detailed connection information")
def test(verbose: bool):
    """Test connection to Obsidian Local REST API"""
    try:
        config = ProjectConfig()
        sync_manager = ObsidianSyncManager(config)
        
        rprint("🔌 [blue]Testing Obsidian API connection...[/blue]")
        
        # Test basic connection
        success = sync_manager.test_connection()
        
        if success:
            notes = sync_manager.get_vault_notes()
            rprint(f"✅ [green]Connection successful![/green]")
            rprint(f"📝 Found {len(notes)} notes in project vault")
            
            if verbose:
                _display_connection_details(config, notes)
        else:
            rprint("❌ [red]Connection failed[/red]")
            _display_troubleshooting_tips(config)
            sys.exit(1)
            
    except Exception as e:
        rprint(f"❌ [red]Error: {e}[/red]")
        _display_troubleshooting_tips(None)
        sys.exit(1)


@main.command()
@click.option("--format", "-f", type=click.Choice(['table', 'yaml', 'json']), 
              default='table', help="Output format")
def config(format: str):
    """Show current configuration"""
    try:
        config = ProjectConfig()
        summary = config.get_config_summary()
        
        if format == 'table':
            _display_config_table(summary)
        elif format == 'yaml':
            import yaml
            print(yaml.dump(summary, default_flow_style=False))
        elif format == 'json':
            import json
            print(json.dumps(summary, indent=2))
            
    except Exception as e:
        rprint(f"❌ [red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option("--max-backups", "-m", type=int, help="Maximum number of backups to keep")
def backup(max_backups: Optional[int]):
    """Create manual backup of notes directory"""
    try:
        config = ProjectConfig()
        sync_manager = ObsidianSyncManager(config)
        
        rprint("💾 [blue]Creating backup...[/blue]")
        backup_path = sync_manager.create_backup()
        
        if backup_path:
            rprint(f"✅ [green]Backup created: {backup_path}[/green]")
            
            # Cleanup old backups if requested
            if max_backups:
                sync_manager.cleanup_old_backups(max_backups)
                rprint(f"🧹 Cleaned up old backups (keeping {max_backups} most recent)")
        else:
            rprint("⚠️ [yellow]No backup created (notes directory not found or backup disabled)[/yellow]")
            
    except Exception as e:
        rprint(f"❌ [red]Error: {e}[/red]")
        sys.exit(1)


def _check_connection(sync_manager: ObsidianSyncManager) -> bool:
    """Check API connection before sync operations"""
    if not sync_manager.test_connection():
        rprint("❌ [red]Cannot connect to Obsidian API[/red]")
        rprint("💡 Run [cyan]obsidian-sync test[/cyan] for troubleshooting")
        return False
    return True


def _display_sync_results(results: dict):
    """Display sync operation results"""
    table = Table(title="🔄 Sync Results")
    table.add_column("Direction", style="cyan")
    table.add_column("Created", style="green")
    table.add_column("Updated", style="yellow") 
    table.add_column("Skipped", style="blue")
    table.add_column("Errors", style="red")
    
    local_to_obs = results["local_to_obsidian"]
    obs_to_local = results["obsidian_to_local"]
    
    table.add_row(
        "Local → Obsidian",
        str(local_to_obs["created"]),
        str(local_to_obs["updated"]),
        str(local_to_obs["skipped"]),
        str(local_to_obs["errors"])
    )
    
    table.add_row(
        "Obsidian → Local", 
        str(obs_to_local["created"]),
        str(obs_to_local["updated"]),
        str(obs_to_local["skipped"]),
        str(obs_to_local["errors"])
    )
    
    console.print(table)
    
    duration = results.get("duration_seconds", 0)
    rprint(f"⏱️ Completed in {duration:.2f} seconds")
    
    if results.get("backup_path"):
        rprint(f"💾 Backup created: {results['backup_path']}")


def _display_connection_details(config: ProjectConfig, notes: list):
    """Display detailed connection information"""
    table = Table(title="🔌 Connection Details")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("API Host", config.obsidian_api_host)
    table.add_row("API Key", "✓ Configured" if config.obsidian_api_key else "❌ Missing")
    table.add_row("Vault Path", config.vault_project_path)
    table.add_row("Local Notes", str(config.local_notes_dir))
    table.add_row("Notes Found", str(len(notes)))
    
    console.print(table)
    
    if notes:
        rprint("\n📝 [blue]Available notes:[/blue]")
        for note in notes[:10]:  # Show first 10 notes
            name = note.get("name", note.get("path", "Unknown"))
            rprint(f"  • {name}")
        
        if len(notes) > 10:
            rprint(f"  ... and {len(notes) - 10} more")


def _display_config_table(summary: dict):
    """Display configuration as a table"""
    table = Table(title="⚙️ Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    for key, value in summary.items():
        if isinstance(value, bool):
            value = "✓" if value else "✗"
        elif isinstance(value, Path):
            value = str(value)
        table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(table)


def _display_troubleshooting_tips(config: Optional[ProjectConfig]):
    """Display troubleshooting information"""
    panel = Panel.fit(
        """[bold yellow]Troubleshooting Tips:[/bold yellow]

1. [cyan]Check Obsidian Setup:[/cyan]
   • Ensure Obsidian is running
   • Install 'Local REST API' plugin
   • Enable the plugin in Obsidian settings

2. [cyan]Verify API Configuration:[/cyan]
   • Check .env file exists and has correct API_HOST and API_KEY
   • Default host should be: https://localhost:27124
   • API key should match the one in Obsidian plugin settings

3. [cyan]Network Issues:[/cyan]
   • If using remote server, check ngrok tunnel is running
   • Verify firewall isn't blocking the connection
   • Try disabling SSL verification for local development

4. [cyan]Get Help:[/cyan]
   • Run 'obsidian-sync config' to check current settings
   • Check logs in logs/obsidian_sync.log for detailed errors""",
        title="❓ Help",
        border_style="yellow"
    )
    console.print(panel)


if __name__ == "__main__":
    main()