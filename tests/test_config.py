#!/usr/bin/env python3
"""
Tests for configuration module
"""

import pytest
import tempfile
import os
from pathlib import Path
from obsidian_project_sync.config import ProjectConfig


class TestProjectConfig:
    """Test ProjectConfig class"""
    
    def test_default_config_creation(self):
        """Test default configuration creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Set required environment variables
            os.environ['OBSIDIAN_API_HOST'] = 'https://localhost:27124'
            os.environ['OBSIDIAN_API_KEY'] = 'test-key'
            
            config = ProjectConfig(project_root)
            
            assert config.project_root == project_root
            assert config.obsidian_api_host == 'https://localhost:27124'
            assert config.obsidian_api_key == 'test-key'
            assert config.local_notes_dir == project_root / 'notes'
    
    def test_yaml_config_loading(self):
        """Test YAML configuration loading"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            config_dir = project_root / 'config'
            config_dir.mkdir()
            
            # Create custom config file
            config_file = config_dir / 'obsidian-sync.yml'
            config_content = """
obsidian:
  vault_project_path: "custom-project"
  local_notes_dir: "custom-notes"
sync:
  interval_seconds: 60
"""
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            # Set required environment variables
            os.environ['OBSIDIAN_API_HOST'] = 'https://localhost:27124'
            os.environ['OBSIDIAN_API_KEY'] = 'test-key'
            
            config = ProjectConfig(project_root)
            
            assert config.vault_project_path == 'custom-project'
            assert config.sync_interval_seconds == 60
    
    def test_missing_env_vars(self):
        """Test behavior with missing environment variables"""
        # Clear environment variables
        if 'OBSIDIAN_API_HOST' in os.environ:
            del os.environ['OBSIDIAN_API_HOST']
        if 'OBSIDIAN_API_KEY' in os.environ:
            del os.environ['OBSIDIAN_API_KEY']
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            with pytest.raises(ValueError, match="Required environment variables missing"):
                ProjectConfig(project_root)
    
    def test_config_summary(self):
        """Test configuration summary"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Set required environment variables
            os.environ['OBSIDIAN_API_HOST'] = 'https://localhost:27124'
            os.environ['OBSIDIAN_API_KEY'] = 'test-key'
            
            config = ProjectConfig(project_root)
            summary = config.get_config_summary()
            
            assert 'project_root' in summary
            assert 'vault_project_path' in summary
            assert 'has_api_key' in summary
            assert summary['has_api_key'] is True