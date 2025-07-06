# Obsidian Project Sync

🔄 Bidirectional synchronization tool between local project notes and Obsidian vault using Local REST API.

## Features

- ✅ **Bidirectional Sync**: Local `notes/` folder ↔ Obsidian vault
- 🔄 **Real-time Monitoring**: Watch mode for continuous synchronization
- 🛡️ **Conflict Resolution**: Smart handling of simultaneous edits
- 💾 **Auto Backup**: Create backups before sync operations
- 🔔 **Notifications**: Slack/Discord integration for sync status
- 🌐 **Remote Access**: Optional ngrok tunnel for server-based projects
- ⚙️ **Configurable**: YAML + environment variables configuration

## Quick Setup

### 1. Install the Package

#### For Development (this repository)
```bash
git clone https://github.com/yourusername/obsidian-project-sync.git
cd obsidian-project-sync
uv sync  # Creates .venv in this directory
uv run obsidian-sync --help
```

#### For Use in Other Projects
```bash
# Method 1: Add as dependency with uv (recommended)
uv add git+https://github.com/yourusername/obsidian-project-sync.git

# Method 2: Install globally with uv
uv tool install git+https://github.com/yourusername/obsidian-project-sync.git

# Method 3: Install from local path (for development)
uv add --editable /path/to/obsidian-project-sync

# Method 4: Traditional pip install
pip install git+https://github.com/yourusername/obsidian-project-sync.git
```

#### When Published to PyPI
```bash
uv add obsidian-project-sync
# or
pip install obsidian-project-sync
```

### 2. Initialize in Your Project
```bash
cd your-project-directory
# If installed with uv
uv run obsidian-sync init

# If installed with pip
obsidian-sync init
```

This creates:
- `config/obsidian-sync.yml` - Configuration file
- `.env.example` - Environment variables template
- `Makefile` additions - Convenience commands

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your Obsidian API settings
```

### 4. Setup Obsidian Local REST API
1. Install [Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api) in Obsidian
2. Configure API key and host in plugin settings
3. (Optional) Setup ngrok for remote access if needed

### 5. Test Connection
```bash
make obsidian-test
# or with uv
uv run obsidian-sync test
# or with pip
obsidian-sync test
```

## Configuration

### Environment Variables (.env)
```bash
# Required
OBSIDIAN_API_HOST=https://localhost:27124
OBSIDIAN_API_KEY=your-api-key-here

# Optional (notifications)
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Configuration File (config/obsidian-sync.yml)
```yaml
# Obsidian vault settings
obsidian:
  vault_project_path: "10-Projects/your-project-name"
  local_notes_dir: "notes"

# Sync behavior
sync:
  interval_seconds: 30
  conflict_resolution: "newer_wins"  # newer_wins, local_wins, obsidian_wins
  create_backup: true

# File filtering
filters:
  include_extensions: [".md"]
  exclude_patterns: 
    - ".*"      # Hidden files
    - "*.tmp"
    - "*.bak"

# Logging
logging:
  level: "INFO"
  file: "logs/obsidian_sync.log"
  max_file_size_mb: 10
  backup_count: 5

# Notifications
notifications:
  enable_slack: false
  enable_discord: false
  notify_on_success: false
  notify_on_error: true
```

## Usage

### Command Line Interface
```bash
# With uv (recommended for development)
uv run obsidian-sync                    # One-time sync
uv run obsidian-sync --watch            # Continuous monitoring
uv run obsidian-sync test               # Test connection
uv run obsidian-sync config             # Check configuration
uv run obsidian-sync init [project-name] # Initialize new project

# With pip installation
obsidian-sync                    # One-time sync
obsidian-sync --watch            # Continuous monitoring
obsidian-sync test               # Test connection
obsidian-sync config             # Check configuration
obsidian-sync init [project-name] # Initialize new project
```

### Makefile Integration
After running `obsidian-sync init`, these targets are added to your Makefile:

```bash
make obsidian-setup    # Initial setup and configuration
make obsidian-sync     # One-time bidirectional sync
make obsidian-watch    # Continuous monitoring mode
make obsidian-test     # Test API connection
make obsidian-backup   # Create manual backup
make obsidian-config   # Show current configuration
```

### Python API
```python
from obsidian_project_sync import ObsidianSyncManager, ProjectConfig

# Basic usage
config = ProjectConfig()
sync_manager = ObsidianSyncManager(config)

# Test connection
if sync_manager.test_connection():
    # Perform sync
    results = sync_manager.bidirectional_sync()
    print(f"Synced {results['local_to_obsidian']['updated']} files")

# Watch mode
sync_manager.watch_mode(interval=60)  # Check every 60 seconds
```

## Project Integration Examples

### Data Science / Research Projects
```yaml
obsidian:
  vault_project_path: "10-Projects/2022-scrna-sepsis"
  local_notes_dir: "notes"

sync:
  conflict_resolution: "newer_wins"
  create_backup: true

notifications:
  enable_slack: true
  notify_on_error: true
```

### Software Development
```yaml
obsidian:
  vault_project_path: "20-Development/my-app"
  local_notes_dir: "docs/notes"

filters:
  include_extensions: [".md", ".txt"]
  exclude_patterns: ["node_modules", ".git", "*.log"]
```

### Academic Writing
```yaml
obsidian:
  vault_project_path: "30-Research/thesis-2024"
  local_notes_dir: "notes"

sync:
  conflict_resolution: "obsidian_wins"  # Prioritize Obsidian edits
  interval_seconds: 60

backup:
  max_backups: 20
  cleanup_old_backups: true
```

## Architecture

```
Your Project                 Obsidian Vault
├── notes/                  ↔ 10-Projects/your-project/
│   ├── daily-log.md       ↔   ├── daily-log.md
│   ├── analysis.md        ↔   ├── analysis.md
│   └── ideas.md           ↔   └── ideas.md
├── config/
│   └── obsidian-sync.yml
├── .env
└── Makefile (enhanced)
```

### Sync Flow
1. **Local → Obsidian**: Upload new/modified files from `notes/`
2. **Obsidian → Local**: Download changes from Obsidian vault
3. **Conflict Resolution**: Handle simultaneous edits based on configuration
4. **Backup**: Create timestamped backups before major changes
5. **Notification**: Send status updates to configured channels

## Advanced Features

### Remote Server Integration
For projects running on remote servers, use ngrok for secure tunneling:

```bash
# Setup ngrok tunnel
ngrok http 27124 --domain=your-project.ngrok.io

# Configure in .env
OBSIDIAN_API_HOST=https://your-project.ngrok.io
```

### Custom Conflict Resolution
```python
from obsidian_project_sync import ConflictResolver

class MyConflictResolver(ConflictResolver):
    def resolve(self, local_content, obsidian_content, file_path):
        # Custom logic here
        if "IMPORTANT" in local_content:
            return local_content
        return obsidian_content

config.conflict_resolver = MyConflictResolver()
```

### Webhook Integration
Monitor sync events in your preferred tools:

```python
# Custom webhook handler
def on_sync_complete(results):
    # Send to your monitoring system
    post_to_monitoring_api(results)

sync_manager.add_webhook(on_sync_complete)
```

## Troubleshooting

### Common Issues

**Connection Failed**
- Check Obsidian Local REST API plugin is enabled
- Verify API key and host in `.env`
- Ensure Obsidian is running

**Sync Conflicts**
- Review `conflict_resolution` setting
- Check backup files in `notes_backup/`
- Manually resolve conflicted files

**Permission Errors**
- Check file permissions on `notes/` directory
- Verify Obsidian vault is writable

### Debug Mode
```bash
# With uv
uv run obsidian-sync --watch --log-level DEBUG
uv run obsidian-sync test --verbose

# With pip
obsidian-sync --watch --log-level DEBUG
obsidian-sync test --verbose
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Related Projects

- [Obsidian Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api)
- [ngrok](https://ngrok.com/) - Secure tunneling
- [Obsidian](https://obsidian.md/) - Knowledge management app

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.