#!/usr/bin/env python3
"""
Obsidian Local REST API synchronization manager
Bidirectional synchronization between notes/ folder and Obsidian vault
"""

import requests
import os
import json
from pathlib import Path
from datetime import datetime
import hashlib
import time
import shutil
from typing import Dict, List, Optional, Union
import logging
import fnmatch

from .config import ProjectConfig
from .conflict_resolver import ConflictResolver, get_conflict_resolver


class ObsidianSyncManager:
    """Obsidian synchronization manager"""
    
    def __init__(self, config: Optional[ProjectConfig] = None, dry_run: bool = False):
        """
        Initialize synchronization manager
        
        Args:
            config: Project configuration (None for auto-creation)
            dry_run: If True, show what would be synced without actual changes
        """
        self.config = config or ProjectConfig()
        self.logger = self.config.setup_logging()
        self.dry_run = dry_run
        
        # API settings
        self.api_host = self.config.obsidian_api_host
        self.api_key = self.config.obsidian_api_key
        self.vault_path = self.config.vault_project_path
        self.local_notes_dir = self.config.local_notes_dir
        
        # Conflict resolver
        self.conflict_resolver = get_conflict_resolver(self.config.conflict_resolution)
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Disable SSL warnings for local development
        requests.packages.urllib3.disable_warnings()
        
        if self.dry_run:
            self.logger.info("🔍 Running in DRY RUN mode - no changes will be made")
        
        self.logger.info(f"Sync manager initialized")
        self.logger.info(f"API Host: {self.api_host}")
        self.logger.info(f"Vault Path: {self.vault_path}")
        self.logger.info(f"Local Notes: {self.local_notes_dir}")
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """API request helper function"""
        url = f"{self.api_host}{endpoint}"
        kwargs.setdefault('headers', self.headers)
        kwargs.setdefault('verify', False)  # For local HTTPS
        kwargs.setdefault('timeout', 30)  # 30 second timeout
        
        try:
            self.logger.debug(f"API request: {method} {endpoint}")
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.logger.error(f"API request failed {method} {endpoint}: {e}")
            raise

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = self._make_request("GET", "/")
            self.logger.info("✅ Obsidian API connection successful")
            return True
        except Exception as e:
            self.logger.error(f"❌ Obsidian API connection failed: {e}")
            return False

    def get_vault_notes(self) -> List[Dict]:
        """Get notes list from Obsidian vault"""
        try:
            # Query project folder directly
            response = self._make_request("GET", f"/vault/{self.vault_path}/")
            
            # Log response details
            self.logger.debug(f"API response status: {response.status_code}")
            self.logger.debug(f"API response headers: {response.headers}")
            self.logger.debug(f"API response content (first 500 chars): {response.text[:500]}")
            
            # Parse JSON response
            try:
                response_data = response.json()
                self.logger.debug(f"JSON parsing successful, type: {type(response_data)}")
                self.logger.debug(f"JSON keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'not a dict'}")
            except ValueError as e:
                self.logger.error(f"JSON parsing failed: {e}")
                self.logger.error(f"Response content: {response.text}")
                return []
            
            # Validate response data structure
            if not isinstance(response_data, dict):
                self.logger.error(f"Unexpected response format: {type(response_data)}")
                self.logger.error(f"Response content: {response_data}")
                return []
            
            # Check for 'files' key
            if "files" not in response_data:
                self.logger.warning(f"'files' key not found in response. Available keys: {list(response_data.keys())}")
                self.logger.info(f"Full response content: {response_data}")
                return []
                
            files = response_data.get("files", [])
            self.logger.debug(f"Total {len(files)} files found")
            
            # Log first few files for debugging
            for i, file_item in enumerate(files[:5]):
                self.logger.debug(f"File {i+1}: {file_item}")
            
            # Filter .md files and convert to full paths
            project_notes = []
            for file_item in files:
                if isinstance(file_item, str):
                    # File name only
                    if self._should_include_file(file_item):
                        full_path = f"{self.vault_path}/{file_item}"
                        project_notes.append({"path": full_path, "name": file_item})
                elif isinstance(file_item, dict):
                    # Dictionary format
                    file_path = file_item.get("path", file_item.get("name", ""))
                    if self._should_include_file(file_path):
                        if not file_path.startswith(self.vault_path):
                            file_path = f"{self.vault_path}/{file_path}"
                        project_notes.append({"path": file_path, "name": file_item.get("name", file_path.split("/")[-1])})
            
            self.logger.info(f"Total {len(files)} files, {len(project_notes)} project notes found")
            self.logger.debug(f"Project notes: {[note.get('path', 'no path') for note in project_notes]}")
            
            return project_notes
        except Exception as e:
            self.logger.error(f"Failed to get vault notes list: {e}")
            return []

    def _should_include_file(self, file_path: str) -> bool:
        """Check if file should be included based on filters"""
        # Check extension
        if not any(file_path.endswith(ext) for ext in self.config.include_extensions):
            return False
        
        # Check exclude patterns
        file_name = Path(file_path).name
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(file_name, pattern):
                return False
                
        return True

    def get_note_content(self, note_path: str) -> Optional[str]:
        """Get specific note content"""
        try:
            response = self._make_request("GET", f"/vault/{note_path}")
            
            # Check response content type
            content_type = response.headers.get('content-type', '').lower()
            
            # Handle JSON response
            if 'application/json' in content_type:
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        content = response_data.get("content", "")
                    else:
                        self.logger.error(f"Unexpected JSON response format ({note_path}): {type(response_data)}")
                        return None
                except ValueError as e:
                    self.logger.error(f"JSON parsing failed ({note_path}): {e}")
                    return None
            # Handle text response (Obsidian API returns content directly)
            else:
                content = response.text
            
            self.logger.debug(f"Note content retrieved successfully: {note_path}")
            return content
        except Exception as e:
            self.logger.error(f"Failed to get note content {note_path}: {e}")
            return None

    def create_or_update_note(self, note_path: str, content: str) -> bool:
        """Create or update note"""
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would update note: {note_path}")
            return True
            
        try:
            # Send text directly in body
            url = f"{self.api_host}/vault/{note_path}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "text/plain; charset=utf-8"
            }
            
            response = requests.put(url, data=content.encode('utf-8'), 
                                  headers=headers, verify=False, timeout=30)
            
            # Handle success status codes: 200, 201, 204
            success = response.status_code in [200, 201, 204]
            
            if success:
                self.logger.debug(f"Note update successful: {note_path} (Status: {response.status_code})")
            else:
                self.logger.warning(f"Note update failed: {note_path} (Status: {response.status_code})")
                self.logger.debug(f"Response content: {response.text}")
            
            return success
        except Exception as e:
            self.logger.error(f"Failed to update note {note_path}: {e}")
            return False

    def delete_note(self, note_path: str) -> bool:
        """Delete note"""
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would delete note: {note_path}")
            return True
            
        try:
            response = self._make_request("DELETE", f"/vault/{note_path}")
            success = response.status_code == 200
            
            if success:
                self.logger.info(f"Note deleted successfully: {note_path}")
            else:
                self.logger.warning(f"Note deletion failed: {note_path}")
            
            return success
        except Exception as e:
            self.logger.error(f"Failed to delete note {note_path}: {e}")
            return False

    def create_backup(self) -> Optional[Path]:
        """Create backup of notes folder"""
        if not self.config.create_backup:
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.config.project_root / "notes_backup" / timestamp
            
            if self.local_notes_dir.exists():
                if not self.dry_run:
                    shutil.copytree(self.local_notes_dir, backup_dir)
                self.logger.info(f"Backup created: {backup_dir}")
                return backup_dir
            else:
                self.logger.warning(f"Backup target notes directory not found: {self.local_notes_dir}")
                return None
                
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            return None

    def cleanup_old_backups(self, max_backups: Optional[int] = None):
        """Clean up old backup files"""
        max_backups = max_backups or self.config.max_backups
        
        backup_root = self.config.project_root / "notes_backup"
        if not backup_root.exists():
            return
            
        # Get all backup directories sorted by modification time
        backup_dirs = [d for d in backup_root.iterdir() if d.is_dir()]
        backup_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove old backups
        for old_backup in backup_dirs[max_backups:]:
            try:
                if not self.dry_run:
                    shutil.rmtree(old_backup)
                self.logger.info(f"Removed old backup: {old_backup.name}")
            except Exception as e:
                self.logger.error(f"Failed to remove old backup {old_backup}: {e}")

    def get_file_hash(self, content: str) -> str:
        """Calculate file content hash"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def sync_local_to_obsidian(self) -> Dict[str, int]:
        """Sync local notes/ → Obsidian vault"""
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
        
        if not self.local_notes_dir.exists():
            self.logger.warning(f"Local notes directory not found: {self.local_notes_dir}")
            return stats
        
        # Get all matching files
        all_files = []
        for ext in self.config.include_extensions:
            all_files.extend(self.local_notes_dir.glob(f"*{ext}"))
        
        # Filter files
        md_files = [f for f in all_files if self._should_include_file(f.name)]
        self.logger.info(f"Found {len(md_files)} local files to sync")
        
        for local_file in md_files:
            try:
                # Read local file
                with open(local_file, 'r', encoding='utf-8') as f:
                    local_content = f.read()
                
                # Construct Obsidian vault path
                vault_note_path = f"{self.vault_path}/{local_file.name}"
                
                # Check current content in Obsidian
                current_content = self.get_note_content(vault_note_path)
                
                if current_content is None:
                    # Create new note
                    if self.create_or_update_note(vault_note_path, local_content):
                        stats["created"] += 1
                        self.logger.info(f"✅ Created: {local_file.name}")
                    else:
                        stats["errors"] += 1
                elif self.get_file_hash(current_content) != self.get_file_hash(local_content):
                    # Handle conflict
                    resolved_content = self.conflict_resolver.resolve(
                        local_content, current_content, local_file
                    )
                    
                    if self.create_or_update_note(vault_note_path, resolved_content):
                        stats["updated"] += 1
                        self.logger.info(f"🔄 Updated: {local_file.name}")
                    else:
                        stats["errors"] += 1
                else:
                    stats["skipped"] += 1
                    self.logger.debug(f"⏭️ Skipped: {local_file.name} (no changes)")
                    
            except Exception as e:
                self.logger.error(f"❌ Error with {local_file.name}: {e}")
                stats["errors"] += 1
                
        return stats

    def sync_obsidian_to_local(self) -> Dict[str, int]:
        """Sync Obsidian vault → local notes/"""
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
        
        # Create local notes directory
        if not self.dry_run:
            self.local_notes_dir.mkdir(parents=True, exist_ok=True)
        
        # Get project notes from Obsidian vault
        vault_notes = self.get_vault_notes()
        
        for note in vault_notes:
            try:
                note_path = note.get("path", "")
                note_name = Path(note_path).name
                
                # Skip non-matching files
                if not self._should_include_file(note_name):
                    continue
                    
                local_file_path = self.local_notes_dir / note_name
                
                # Get note content from Obsidian
                vault_content = self.get_note_content(note_path)
                if vault_content is None:
                    continue
                
                # Check local file
                if local_file_path.exists():
                    with open(local_file_path, 'r', encoding='utf-8') as f:
                        local_content = f.read()
                    
                    if self.get_file_hash(local_content) != self.get_file_hash(vault_content):
                        # Handle conflict
                        resolved_content = self.conflict_resolver.resolve(
                            local_content, vault_content, local_file_path
                        )
                        
                        if not self.dry_run:
                            with open(local_file_path, 'w', encoding='utf-8') as f:
                                f.write(resolved_content)
                        stats["updated"] += 1
                        self.logger.info(f"🔄 Updated: {note_name}")
                    else:
                        stats["skipped"] += 1
                        self.logger.debug(f"⏭️ Skipped: {note_name} (no changes)")
                else:
                    # Create new file
                    if not self.dry_run:
                        with open(local_file_path, 'w', encoding='utf-8') as f:
                            f.write(vault_content)
                    stats["created"] += 1
                    self.logger.info(f"✅ Created: {note_name}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error with {note.get('path', 'unknown')}: {e}")
                stats["errors"] += 1
                
        return stats

    def send_notification(self, message: str, is_error: bool = False):
        """Send notification (Slack, etc.)"""
        if not (self.config.enable_slack and self.config.slack_webhook_url):
            return
            
        try:
            payload = {
                "text": f"{'🚨' if is_error else '📝'} Obsidian Sync: {message}",
                "username": "Obsidian Sync Bot"
            }
            
            response = requests.post(
                self.config.slack_webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.debug("Notification sent successfully")
            else:
                self.logger.warning(f"Notification send failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Notification send error: {e}")

    def bidirectional_sync(self) -> Dict[str, Union[Dict[str, int], float, str]]:
        """Execute bidirectional synchronization"""
        start_time = datetime.now()
        self.logger.info("🔄 Starting bidirectional synchronization...")
        self.logger.info(f"📁 Local: {self.local_notes_dir}")
        self.logger.info(f"🗂️ Vault: {self.vault_path}")
        
        # Create backup
        backup_path = self.create_backup()
        
        try:
            # Test connection
            if not self.test_connection():
                raise Exception("Obsidian API connection failed")
            
            # Local → Obsidian
            self.logger.info("📤 Local → Obsidian synchronization")
            local_to_obsidian = self.sync_local_to_obsidian()
            
            # Obsidian → Local
            self.logger.info("📥 Obsidian → Local synchronization")
            obsidian_to_local = self.sync_obsidian_to_local()
            
            # Display results
            duration = datetime.now() - start_time
            self.logger.info("=" * 50)
            self.logger.info("🎉 Synchronization complete!")
            self.logger.info(f"⏱️ Duration: {duration.total_seconds():.2f}s")
            self.logger.info(f"📤 Local→Obsidian: created {local_to_obsidian['created']}, "
                           f"updated {local_to_obsidian['updated']}, "
                           f"skipped {local_to_obsidian['skipped']}, "
                           f"errors {local_to_obsidian['errors']}")
            self.logger.info(f"📥 Obsidian→Local: created {obsidian_to_local['created']}, "
                           f"updated {obsidian_to_local['updated']}, "
                           f"skipped {obsidian_to_local['skipped']}, "
                           f"errors {obsidian_to_local['errors']}")
            
            # Success notification
            total_changes = (local_to_obsidian['created'] + local_to_obsidian['updated'] + 
                           obsidian_to_local['created'] + obsidian_to_local['updated'])
            
            if total_changes > 0 and self.config.notify_on_success:
                self.send_notification(
                    f"Synchronization complete - {total_changes} files changed "
                    f"(duration: {duration.total_seconds():.1f}s)"
                )
            
            return {
                "local_to_obsidian": local_to_obsidian,
                "obsidian_to_local": obsidian_to_local,
                "duration_seconds": duration.total_seconds(),
                "backup_path": str(backup_path) if backup_path else None
            }
            
        except Exception as e:
            self.logger.error(f"Synchronization failed: {e}")
            if self.config.notify_on_error:
                self.send_notification(f"Synchronization failed: {e}", is_error=True)
            raise

    def watch_mode(self, interval: Optional[int] = None):
        """Continuous monitoring mode"""
        sync_interval = interval or self.config.sync_interval_seconds
        
        self.logger.info(f"👀 Starting continuous monitoring (interval: {sync_interval}s)")
        self.logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                try:
                    self.bidirectional_sync()
                except Exception as e:
                    self.logger.error(f"Synchronization error: {e}")
                
                self.logger.info(f"😴 Waiting {sync_interval}s...")
                time.sleep(sync_interval)
                
        except KeyboardInterrupt:
            self.logger.info("👋 Continuous monitoring stopped")