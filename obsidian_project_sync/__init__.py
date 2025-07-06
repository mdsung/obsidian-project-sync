"""
Obsidian Project Sync

Bidirectional synchronization between local project notes and Obsidian vault.
"""

__version__ = "0.1.0"
__author__ = "MinDong Sung"
__email__ = "mdskylover@gmail.com"

from .config import ProjectConfig
from .sync_manager import ObsidianSyncManager
from .conflict_resolver import ConflictResolver, NewerWinsResolver, LocalWinsResolver, ObsidianWinsResolver

__all__ = [
    "ProjectConfig",
    "ObsidianSyncManager", 
    "ConflictResolver",
    "NewerWinsResolver",
    "LocalWinsResolver", 
    "ObsidianWinsResolver",
]