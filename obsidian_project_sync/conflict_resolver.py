#!/usr/bin/env python3
"""
Conflict resolution strategies for Obsidian sync
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Union
from abc import ABC, abstractmethod


class ConflictResolver(ABC):
    """Abstract base class for conflict resolution strategies"""
    
    @abstractmethod
    def resolve(self, local_content: str, obsidian_content: str, file_path: Union[str, Path]) -> str:
        """
        Resolve conflict between local and Obsidian content
        
        Args:
            local_content: Content from local file
            obsidian_content: Content from Obsidian vault
            file_path: Path to the conflicted file
            
        Returns:
            Resolved content to use
        """
        pass


class NewerWinsResolver(ConflictResolver):
    """Resolve conflicts by choosing the more recently modified content"""
    
    def resolve(self, local_content: str, obsidian_content: str, file_path: Union[str, Path]) -> str:
        """Choose content based on modification time"""
        try:
            local_path = Path(file_path)
            
            # If local file doesn't exist, use Obsidian content
            if not local_path.exists():
                return obsidian_content
            
            # Get local file modification time
            local_mtime = local_path.stat().st_mtime
            current_time = datetime.now().timestamp()
            
            # If local file was modified within the last 5 minutes, prefer local
            # Otherwise, this is likely an older file, so prefer Obsidian
            time_diff = current_time - local_mtime
            
            if time_diff < 300:  # 5 minutes
                return local_content
            else:
                return obsidian_content
                
        except Exception:
            # If we can't determine modification time, fall back to local content
            return local_content


class LocalWinsResolver(ConflictResolver):
    """Always prefer local content in conflicts"""
    
    def resolve(self, local_content: str, obsidian_content: str, file_path: Union[str, Path]) -> str:
        """Always return local content"""
        return local_content


class ObsidianWinsResolver(ConflictResolver):
    """Always prefer Obsidian content in conflicts"""
    
    def resolve(self, local_content: str, obsidian_content: str, file_path: Union[str, Path]) -> str:
        """Always return Obsidian content"""
        return obsidian_content


class MergeResolver(ConflictResolver):
    """Attempt to merge changes when possible"""
    
    def resolve(self, local_content: str, obsidian_content: str, file_path: Union[str, Path]) -> str:
        """
        Attempt simple merge by combining unique lines
        Falls back to newer wins if merge is not possible
        """
        try:
            local_lines = set(local_content.splitlines())
            obsidian_lines = set(obsidian_content.splitlines())
            
            # If one is a subset of the other, use the larger set
            if local_lines.issubset(obsidian_lines):
                return obsidian_content
            elif obsidian_lines.issubset(local_lines):
                return local_content
            
            # Otherwise, fall back to newer wins
            fallback = NewerWinsResolver()
            return fallback.resolve(local_content, obsidian_content, file_path)
            
        except Exception:
            # If merge fails, fall back to newer wins
            fallback = NewerWinsResolver()
            return fallback.resolve(local_content, obsidian_content, file_path)


class InteractiveResolver(ConflictResolver):
    """Ask user to resolve conflicts interactively"""
    
    def resolve(self, local_content: str, obsidian_content: str, file_path: Union[str, Path]) -> str:
        """Present conflict to user for manual resolution"""
        print(f"\n🔥 CONFLICT DETECTED: {file_path}")
        print("=" * 60)
        print("LOCAL CONTENT:")
        print("-" * 30)
        print(local_content[:500] + ("..." if len(local_content) > 500 else ""))
        print("\nOBSIDIAN CONTENT:")
        print("-" * 30)
        print(obsidian_content[:500] + ("..." if len(obsidian_content) > 500 else ""))
        print("\n" + "=" * 60)
        
        while True:
            choice = input("Choose resolution [L]ocal / [O]bsidian / [M]erge / [E]dit: ").strip().lower()
            
            if choice == 'l':
                return local_content
            elif choice == 'o':
                return obsidian_content
            elif choice == 'm':
                # Attempt merge
                merger = MergeResolver()
                return merger.resolve(local_content, obsidian_content, file_path)
            elif choice == 'e':
                # Open editor (simplified - would need proper editor integration)
                print("📝 Please manually edit the file and press Enter when done.")
                input("Press Enter to continue...")
                
                # Re-read local file if it exists
                try:
                    local_path = Path(file_path)
                    if local_path.exists():
                        with open(local_path, 'r', encoding='utf-8') as f:
                            return f.read()
                except Exception:
                    pass
                
                return local_content
            else:
                print("Invalid choice. Please enter L, O, M, or E.")


class BackupAndResolveResolver(ConflictResolver):
    """Create backup before resolving conflict"""
    
    def __init__(self, base_resolver: ConflictResolver):
        self.base_resolver = base_resolver
    
    def resolve(self, local_content: str, obsidian_content: str, file_path: Union[str, Path]) -> str:
        """Create backup and then resolve using base resolver"""
        try:
            # Create conflict backup
            self._create_conflict_backup(local_content, obsidian_content, file_path)
        except Exception as e:
            print(f"Warning: Could not create conflict backup: {e}")
        
        # Delegate to base resolver
        return self.base_resolver.resolve(local_content, obsidian_content, file_path)
    
    def _create_conflict_backup(self, local_content: str, obsidian_content: str, file_path: Union[str, Path]):
        """Create backup files for both versions"""
        file_path = Path(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create conflicts directory
        conflicts_dir = file_path.parent / "conflicts" / timestamp
        conflicts_dir.mkdir(parents=True, exist_ok=True)
        
        # Save both versions
        local_backup = conflicts_dir / f"{file_path.stem}_local{file_path.suffix}"
        obsidian_backup = conflicts_dir / f"{file_path.stem}_obsidian{file_path.suffix}"
        
        with open(local_backup, 'w', encoding='utf-8') as f:
            f.write(local_content)
            
        with open(obsidian_backup, 'w', encoding='utf-8') as f:
            f.write(obsidian_content)
        
        print(f"📁 Conflict backup created in: {conflicts_dir}")


def get_conflict_resolver(strategy: str) -> ConflictResolver:
    """
    Factory function to get conflict resolver by strategy name
    
    Args:
        strategy: Strategy name ('newer_wins', 'local_wins', 'obsidian_wins', 'merge', 'interactive')
        
    Returns:
        ConflictResolver instance
    """
    resolvers = {
        'newer_wins': NewerWinsResolver,
        'local_wins': LocalWinsResolver,
        'obsidian_wins': ObsidianWinsResolver,
        'merge': MergeResolver,
        'interactive': InteractiveResolver,
    }
    
    resolver_class = resolvers.get(strategy, NewerWinsResolver)
    resolver = resolver_class()
    
    # Wrap with backup resolver for safety
    return BackupAndResolveResolver(resolver)