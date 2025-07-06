# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of obsidian-project-sync
- Bidirectional synchronization between local notes and Obsidian vault
- Support for Obsidian Local REST API
- Multiple conflict resolution strategies
- Automatic backup creation
- Watch mode for continuous synchronization
- Rich CLI interface with progress indicators
- Configurable file filtering and exclusion patterns
- Notification support (Slack, Discord)
- Project initialization command
- Makefile integration

### Features
- **Sync Modes**: One-time sync and continuous monitoring
- **Conflict Resolution**: newer_wins, local_wins, obsidian_wins, merge, interactive
- **Backup System**: Automatic backups before sync operations
- **Filtering**: Include/exclude files by extension and patterns
- **Logging**: Configurable logging with rotation
- **Notifications**: Success/error notifications via webhooks
- **Remote Access**: ngrok support for server deployments

### Configuration
- YAML-based configuration with environment variable overrides
- Auto-detection of project structure
- Flexible vault path configuration
- Customizable sync intervals and behavior

## [0.1.0] - 2024-12-XX

### Added
- Initial package structure
- Core synchronization functionality
- CLI interface
- Documentation and examples