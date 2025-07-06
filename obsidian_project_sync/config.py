#!/usr/bin/env python3
"""
Project configuration management module
Environment variables (.env) + YAML configuration (config.yml) integrated management
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler


class ProjectConfig:
    """Project configuration management class"""
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        """
        Initialize configuration
        
        Args:
            project_root: Project root path (None for auto-detection)
        """
        # Set project root
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Auto-detect project root (current working directory)
            self.project_root = Path.cwd()
        
        # Configuration file paths
        self.env_file = self.project_root / ".env"
        self.config_file = self.project_root / "config" / "obsidian-sync.yml"
        
        # Fallback config file path (for backward compatibility)
        if not self.config_file.exists():
            self.config_file = self.project_root / "obsidian-sync.yml"
        
        # Load environment variables
        self._load_env()
        
        # Load YAML configuration
        self._load_yaml_config()
        
        # Validate configuration
        self._validate_config()
    
    def _load_env(self):
        """Load environment variables"""
        if self.env_file.exists():
            load_dotenv(self.env_file)
        else:
            # Try to load from parent directories
            current = self.project_root
            for _ in range(3):  # Check up to 3 levels up
                env_path = current / ".env"
                if env_path.exists():
                    load_dotenv(env_path)
                    break
                current = current.parent
    
    def _load_yaml_config(self):
        """Load YAML configuration file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.yaml_config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            # Create default configuration
            self.yaml_config = self._get_default_config()
            # Optionally create the config file
            self._create_default_config_file()
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error in {self.config_file}: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        project_name = self.project_root.name
        return {
            'obsidian': {
                'vault_project_path': f'10-Projects/{project_name}',
                'local_notes_dir': 'notes'
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
    
    def _create_default_config_file(self):
        """Create default configuration file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.yaml_config, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
        except Exception:
            # Silent fail - not critical
            pass
    
    def _get_yaml_value(self, key_path: str, default: Any = None) -> Any:
        """Get nested key value from YAML configuration"""
        keys = key_path.split('.')
        value = self.yaml_config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def _validate_config(self):
        """Validate configuration"""
        required_env_vars = ['OBSIDIAN_API_HOST', 'OBSIDIAN_API_KEY']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(
                f"Required environment variables missing: {', '.join(missing_vars)}\n"
                f"Please create a .env file with these variables or set them in your environment."
            )
    
    # Security settings (from environment variables)
    @property
    def obsidian_api_host(self) -> str:
        return os.getenv('OBSIDIAN_API_HOST', 'https://localhost:27124')
    
    @property
    def obsidian_api_key(self) -> str:
        return os.getenv('OBSIDIAN_API_KEY', '')
    
    @property
    def slack_webhook_url(self) -> str:
        return os.getenv('SLACK_WEBHOOK_URL', '')
    
    @property
    def discord_webhook_url(self) -> str:
        return os.getenv('DISCORD_WEBHOOK_URL', '')
    
    @property
    def ngrok_auth_token(self) -> str:
        return os.getenv('NGROK_AUTH_TOKEN', '')
    
    @property
    def ngrok_domain(self) -> str:
        return os.getenv('NGROK_DOMAIN', '')
    
    # General settings (from YAML)
    @property
    def vault_project_path(self) -> str:
        return self._get_yaml_value('obsidian.vault_project_path', f'10-Projects/{self.project_root.name}')
    
    @property
    def local_notes_dir(self) -> Path:
        notes_dir = self._get_yaml_value('obsidian.local_notes_dir', 'notes')
        return self.project_root / notes_dir
    
    @property
    def sync_interval_seconds(self) -> int:
        return self._get_yaml_value('sync.interval_seconds', 30)
    
    @property
    def conflict_resolution(self) -> str:
        return self._get_yaml_value('sync.conflict_resolution', 'newer_wins')
    
    @property
    def create_backup(self) -> bool:
        return self._get_yaml_value('sync.create_backup', True)
    
    @property
    def log_level(self) -> str:
        return self._get_yaml_value('logging.level', 'INFO')
    
    @property
    def log_file(self) -> Path:
        log_file = self._get_yaml_value('logging.file', 'logs/obsidian_sync.log')
        return self.project_root / log_file
    
    @property
    def max_file_size_mb(self) -> int:
        return self._get_yaml_value('logging.max_file_size_mb', 10)
    
    @property
    def backup_count(self) -> int:
        return self._get_yaml_value('logging.backup_count', 5)
    
    @property
    def include_extensions(self) -> list:
        return self._get_yaml_value('filters.include_extensions', ['.md'])
    
    @property
    def exclude_patterns(self) -> list:
        return self._get_yaml_value('filters.exclude_patterns', ['.*', '*.tmp', '*.bak'])
    
    @property
    def max_backups(self) -> int:
        return self._get_yaml_value('backup.max_backups', 10)
    
    @property
    def cleanup_old_backups(self) -> bool:
        return self._get_yaml_value('backup.cleanup_old_backups', True)
    
    @property
    def backup_before_sync(self) -> bool:
        return self._get_yaml_value('backup.backup_before_sync', True)
    
    @property
    def enable_slack(self) -> bool:
        return self._get_yaml_value('notifications.enable_slack', False)
    
    @property
    def enable_discord(self) -> bool:
        return self._get_yaml_value('notifications.enable_discord', False)
    
    @property
    def notify_on_success(self) -> bool:
        return self._get_yaml_value('notifications.notify_on_success', False)
    
    @property
    def notify_on_error(self) -> bool:
        return self._get_yaml_value('notifications.notify_on_error', True)
    
    def setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        # Create log directory
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        logger = logging.getLogger('obsidian_sync')
        logger.setLevel(getattr(logging, self.log_level.upper()))
        
        # Remove existing handlers to prevent duplicates
        if logger.handlers:
            logger.handlers.clear()
        
        # File handler (rotating log)
        file_handler = RotatingFileHandler(
            self.log_file, 
            maxBytes=self.max_file_size_mb * 1024 * 1024, 
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary information"""
        return {
            'project_root': str(self.project_root),
            'vault_project_path': self.vault_project_path,
            'local_notes_dir': str(self.local_notes_dir),
            'sync_interval_seconds': self.sync_interval_seconds,
            'conflict_resolution': self.conflict_resolution,
            'create_backup': self.create_backup,
            'log_level': self.log_level,
            'log_file': str(self.log_file),
            'has_api_key': bool(self.obsidian_api_key),
            'has_api_host': bool(self.obsidian_api_host),
            'enable_slack': self.enable_slack,
            'enable_discord': self.enable_discord,
            'include_extensions': self.include_extensions,
            'exclude_patterns': self.exclude_patterns,
        }
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration and save to file"""
        # Deep merge updates into yaml_config
        def deep_merge(base: dict, updates: dict) -> dict:
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
            return base
        
        deep_merge(self.yaml_config, updates)
        
        # Save to file
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.yaml_config, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
        except Exception as e:
            raise ValueError(f"Failed to save configuration: {e}")