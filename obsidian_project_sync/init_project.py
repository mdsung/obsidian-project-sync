#!/usr/bin/env python3
"""
Project initialization module for Obsidian sync
"""

import shutil
from pathlib import Path
from typing import Optional
import yaml


class ProjectInitializer:
    """Initialize Obsidian sync in a project"""
    
    def __init__(self):
        self.package_root = Path(__file__).parent
        self.templates_dir = self.package_root / "templates"
    
    def initialize_project(
        self,
        project_root: Optional[Path] = None,
        project_name: Optional[str] = None,
        vault_path: Optional[str] = None,
        notes_dir: str = "notes",
        force: bool = False
    ) -> bool:
        """
        Initialize Obsidian sync in a project
        
        Args:
            project_root: Project root directory (default: current directory)
            project_name: Project name for vault path
            vault_path: Custom vault path
            notes_dir: Local notes directory name
            force: Overwrite existing files
            
        Returns:
            True if successful, False otherwise
        """
        try:
            project_root = project_root or Path.cwd()
            project_name = project_name or project_root.name
            
            # Create configuration
            success = self._create_config_file(
                project_root, project_name, vault_path, notes_dir, force
            )
            if not success:
                return False
            
            # Create environment template
            success = self._create_env_template(project_root, force)
            if not success:
                return False
            
            # Create notes directory
            notes_path = project_root / notes_dir
            notes_path.mkdir(exist_ok=True)
            
            # Add Makefile targets
            self._add_makefile_targets(project_root, force)
            
            # Create example note
            self._create_example_note(notes_path, project_name)
            
            print(f"✅ Obsidian sync initialized in {project_root}")
            print(f"📁 Notes directory: {notes_dir}/")
            print(f"⚙️ Configuration: config/obsidian-sync.yml")
            print(f"🔧 Environment: .env (copy from .env.example)")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize project: {e}")
            return False
    
    def _create_config_file(
        self,
        project_root: Path,
        project_name: str,
        vault_path: Optional[str],
        notes_dir: str,
        force: bool
    ) -> bool:
        """Create configuration file"""
        config_dir = project_root / "config"
        config_file = config_dir / "obsidian-sync.yml"
        
        if config_file.exists() and not force:
            print(f"⚠️ Configuration already exists: {config_file}")
            print("Use --force to overwrite")
            return False
        
        # Create configuration
        vault_project_path = vault_path or f"10-Projects/{project_name}"
        
        config = {
            'obsidian': {
                'vault_project_path': vault_project_path,
                'local_notes_dir': notes_dir
            },
            'sync': {
                'interval_seconds': 30,
                'conflict_resolution': 'newer_wins',
                'create_backup': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/obsidian_sync.log',
                'max_file_size_mb': 10,
                'backup_count': 5
            },
            'filters': {
                'include_extensions': ['.md'],
                'exclude_patterns': ['.*', '*.tmp', '*.bak']
            },
            'backup': {
                'max_backups': 10,
                'cleanup_old_backups': True,
                'backup_before_sync': True
            },
            'notifications': {
                'enable_slack': False,
                'enable_discord': False,
                'notify_on_success': False,
                'notify_on_error': True
            }
        }
        
        # Create config directory and file
        config_dir.mkdir(exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"📄 Created configuration: {config_file}")
        return True
    
    def _create_env_template(self, project_root: Path, force: bool) -> bool:
        """Create .env.example file"""
        env_example = project_root / ".env.example"
        
        if env_example.exists() and not force:
            print(f"⚠️ Environment template already exists: {env_example}")
            return True
        
        env_content = """# Obsidian Local REST API Configuration
# Copy this file to .env and configure your settings

# Required: Obsidian Local REST API settings
OBSIDIAN_API_HOST=https://localhost:27124
OBSIDIAN_API_KEY=your-api-key-here

# Optional: Notification webhooks
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
# DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Optional: Development settings
# DEBUG=true
# LOG_LEVEL=DEBUG
"""
        
        with open(env_example, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"📄 Created environment template: {env_example}")
        return True
    
    def _add_makefile_targets(self, project_root: Path, force: bool):
        """Add Makefile targets for Obsidian sync"""
        makefile = project_root / "Makefile"
        
        targets = """
# Obsidian sync targets
.PHONY: obsidian-setup obsidian-sync obsidian-watch obsidian-test obsidian-config obsidian-backup

obsidian-setup:
	@echo "🔧 Setting up Obsidian sync..."
	@obsidian-sync init

obsidian-sync:
	@echo "🔄 Running Obsidian synchronization..."
	@obsidian-sync

obsidian-watch:
	@echo "👀 Starting continuous Obsidian monitoring..."
	@obsidian-sync --watch

obsidian-test:
	@echo "🔌 Testing Obsidian API connection..."
	@obsidian-sync test

obsidian-config:
	@echo "⚙️ Showing Obsidian sync configuration..."
	@obsidian-sync config

obsidian-backup:
	@echo "💾 Creating notes backup..."
	@obsidian-sync backup
"""
        
        if makefile.exists():
            # Check if targets already exist
            with open(makefile, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "obsidian-sync:" in content and not force:
                print("⚠️ Makefile targets already exist")
                return
            
            # Append targets
            with open(makefile, 'a', encoding='utf-8') as f:
                f.write(targets)
            print("📄 Added Makefile targets")
        else:
            # Create new Makefile
            makefile_content = f"""# Project Makefile
.PHONY: help

help:
	@echo "Available targets:"
	@echo "  obsidian-setup  - Initialize Obsidian sync"
	@echo "  obsidian-sync   - Run one-time synchronization"
	@echo "  obsidian-watch  - Start continuous monitoring"
	@echo "  obsidian-test   - Test API connection"
	@echo "  obsidian-config - Show configuration"
	@echo "  obsidian-backup - Create manual backup"
{targets}"""
            
            with open(makefile, 'w', encoding='utf-8') as f:
                f.write(makefile_content)
            print(f"📄 Created Makefile: {makefile}")
    
    def _create_example_note(self, notes_dir: Path, project_name: str):
        """Create an example note"""
        example_note = notes_dir / f"{project_name}.md"
        
        if example_note.exists():
            return
        
        content = f"""# {project_name}

## Overview
This is the main project hub for {project_name}.

## Setup
1. Configure Obsidian Local REST API plugin
2. Copy `.env.example` to `.env` and configure API settings
3. Run `make obsidian-test` to verify connection
4. Run `make obsidian-sync` to start synchronization

## Notes Structure
- This notes/ folder syncs bidirectionally with Obsidian vault
- Create new notes here or in Obsidian - they will sync automatically
- Use Markdown format (.md files)

## Quick Commands
- `make obsidian-sync` - One-time sync
- `make obsidian-watch` - Continuous monitoring
- `make obsidian-test` - Test connection
- `make obsidian-backup` - Create backup

## Tags
#project-hub #sync-enabled

---
*Created: {yaml.safe_load("!!timestamp")or "today"}*
*Auto-generated by obsidian-project-sync*
"""
        
        with open(example_note, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📝 Created example note: {example_note}")


def main():
    """CLI entry point for project initialization"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize Obsidian sync in project')
    parser.add_argument('--project-name', '-n', help='Project name')
    parser.add_argument('--vault-path', '-v', help='Custom vault path')
    parser.add_argument('--notes-dir', '-d', default='notes', help='Notes directory name')
    parser.add_argument('--force', '-f', action='store_true', help='Overwrite existing files')
    
    args = parser.parse_args()
    
    initializer = ProjectInitializer()
    success = initializer.initialize_project(
        project_name=args.project_name,
        vault_path=args.vault_path,
        notes_dir=args.notes_dir,
        force=args.force
    )
    
    if not success:
        exit(1)


if __name__ == '__main__':
    main()