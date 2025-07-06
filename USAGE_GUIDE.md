# Obsidian Project Sync - Usage Guide

## Quick Start

### 1. Installation
```bash
# Install from PyPI (when published)
pip install obsidian-project-sync

# Or install from source
git clone https://github.com/yourusername/obsidian-project-sync.git
cd obsidian-project-sync
pip install -e .
```

### 2. Initialize in Your Project
```bash
cd your-project-directory
obsidian-sync init
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your Obsidian API settings
```

### 4. Test and Sync
```bash
obsidian-sync test    # Test connection
obsidian-sync         # Run sync
```

## Detailed Setup

### Obsidian Configuration

1. **Install Local REST API Plugin**
   - Open Obsidian → Settings → Community Plugins
   - Search for "Local REST API"
   - Install and enable the plugin

2. **Configure API Settings**
   - Go to Plugin Settings → Local REST API
   - Set API key (copy this to your .env file)
   - Note the host/port (default: https://localhost:27124)
   - Enable the API

3. **Create Project Folder**
   - In your Obsidian vault, create: `10-Projects/your-project-name/`
   - This will be your sync target

### Environment Variables

Create `.env` file in your project root:

```bash
# Required
OBSIDIAN_API_HOST=https://localhost:27124
OBSIDIAN_API_KEY=your-api-key-from-obsidian

# Optional (for remote server access)
NGROK_AUTH_TOKEN=your-ngrok-token
NGROK_DOMAIN=your-project.ngrok.io

# Optional (notifications)
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Configuration File

Edit `config/obsidian-sync.yml`:

```yaml
obsidian:
  vault_project_path: "10-Projects/your-project-name"
  local_notes_dir: "notes"

sync:
  interval_seconds: 30
  conflict_resolution: "newer_wins"  # newer_wins, local_wins, obsidian_wins
  create_backup: true

filters:
  include_extensions: [".md"]
  exclude_patterns: [".*", "*.tmp", "*.bak"]

logging:
  level: "INFO"
  file: "logs/obsidian_sync.log"

notifications:
  notify_on_error: true
  notify_on_success: false
```

## Common Use Cases

### Data Science / Research Projects

```yaml
# config/obsidian-sync.yml
obsidian:
  vault_project_path: "10-Projects/2024-research-project"
  local_notes_dir: "notes"

sync:
  conflict_resolution: "newer_wins"
  interval_seconds: 60

filters:
  include_extensions: [".md", ".txt"]
  exclude_patterns: ["*.tmp", "*.log", ".DS_Store"]
```

### Software Development

```yaml
obsidian:
  vault_project_path: "20-Development/my-app"
  local_notes_dir: "docs/notes"

filters:
  exclude_patterns: ["node_modules", ".git", "*.log", "target/"]
```

### Academic Writing

```yaml
obsidian:
  vault_project_path: "30-Research/dissertation-2024"
  local_notes_dir: "notes"

sync:
  conflict_resolution: "obsidian_wins"  # Prioritize Obsidian edits
  create_backup: true

backup:
  max_backups: 20
  cleanup_old_backups: true
```

## Command Reference

### Basic Commands

```bash
# Initialize project
obsidian-sync init [--project-name NAME] [--vault-path PATH]

# Test connection
obsidian-sync test [--verbose]

# Run sync
obsidian-sync [--dry-run] [--log-level DEBUG]

# Watch mode
obsidian-sync --watch [--interval 60]

# Show configuration
obsidian-sync config [--format table|yaml|json]

# Create backup
obsidian-sync backup [--max-backups 10]
```

### Makefile Integration

After initialization, these targets are available:

```bash
make obsidian-setup    # Initialize sync
make obsidian-sync     # Run one-time sync
make obsidian-watch    # Continuous monitoring
make obsidian-test     # Test connection
make obsidian-config   # Show configuration
make obsidian-backup   # Create backup
```

## Conflict Resolution

### Available Strategies

1. **newer_wins** (default): Choose more recently modified content
2. **local_wins**: Always prefer local file content
3. **obsidian_wins**: Always prefer Obsidian vault content
4. **merge**: Attempt to merge changes when possible
5. **interactive**: Ask user to resolve conflicts manually

### Example: Interactive Resolution

```bash
obsidian-sync config
# Set conflict_resolution: "interactive" in config file

obsidian-sync
# Will prompt for manual conflict resolution
```

## Remote Access Setup

For projects running on remote servers:

### 1. Install ngrok
```bash
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

### 2. Setup Authentication
```bash
ngrok authtoken YOUR_NGROK_TOKEN
```

### 3. Create Tunnel
```bash
# Forward Obsidian API port
ngrok http 27124 --domain=your-project.ngrok.io
```

### 4. Update Configuration
```bash
# .env
OBSIDIAN_API_HOST=https://your-project.ngrok.io
```

## Troubleshooting

### Connection Issues

**Problem**: "Connection failed"
**Solutions**:
1. Verify Obsidian is running
2. Check Local REST API plugin is enabled
3. Verify API key matches
4. Test with `curl`:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" https://localhost:27124/
   ```

**Problem**: "SSL certificate verification failed"
**Solutions**:
1. For local development, this is expected (self-signed cert)
2. The tool automatically disables SSL verification for localhost
3. For production, use proper SSL certificates

### Sync Issues

**Problem**: "No files synced"
**Solutions**:
1. Check file extensions in `include_extensions`
2. Verify `exclude_patterns` aren't too restrictive
3. Check vault path exists in Obsidian
4. Run with `--log-level DEBUG` for details

**Problem**: "Conflicts not resolved"
**Solutions**:
1. Check `conflict_resolution` setting
2. Use `interactive` mode for manual resolution
3. Check backup files in `conflicts/` directory

### Performance Issues

**Problem**: "Sync too slow"
**Solutions**:
1. Increase `interval_seconds` for watch mode
2. Add more patterns to `exclude_patterns`
3. Use `--dry-run` to test without actual changes

## Best Practices

### File Organization

```
your-project/
├── notes/                    # Local notes (synced)
│   ├── daily-log.md
│   ├── analysis-notes.md
│   └── meeting-notes.md
├── config/
│   └── obsidian-sync.yml    # Configuration
├── .env                     # API credentials
├── logs/                    # Sync logs
├── notes_backup/           # Automatic backups
└── Makefile               # Convenience targets
```

### Vault Organization

```
Obsidian Vault/
├── 10-Projects/
│   └── your-project/        # Synced notes appear here
│       ├── daily-log.md
│       ├── analysis-notes.md
│       └── meeting-notes.md
├── 00-Inbox/
├── 20-Areas/
└── 30-Archive/
```

### Workflow Recommendations

1. **Create notes locally** for version control
2. **Edit in Obsidian** for rich linking and visualization
3. **Use watch mode** during active work sessions
4. **Regular backups** before major changes
5. **Test connections** after Obsidian updates

### Version Control Integration

```bash
# .gitignore additions
logs/
notes_backup/
conflicts/
.env

# Track important files
git add notes/
git add config/obsidian-sync.yml
git add .env.example
```

## Advanced Usage

### Custom Conflict Resolver

```python
from obsidian_project_sync import ConflictResolver

class MyResolver(ConflictResolver):
    def resolve(self, local_content, obsidian_content, file_path):
        # Custom logic here
        if "IMPORTANT" in local_content:
            return local_content
        return obsidian_content

# Use in configuration
config.conflict_resolver = MyResolver()
```

### Webhook Integration

```python
from obsidian_project_sync import ObsidianSyncManager

def on_sync_complete(results):
    # Custom notification logic
    send_to_monitoring_system(results)

sync_manager = ObsidianSyncManager()
sync_manager.add_webhook(on_sync_complete)
```

### Scheduled Sync

```bash
# Add to crontab for automatic sync
# Sync every 5 minutes during work hours
*/5 9-17 * * 1-5 cd /path/to/project && obsidian-sync >> logs/cron.log 2>&1
```

## Support and Contributing

### Getting Help

1. Check this usage guide
2. Run `obsidian-sync test --verbose` for diagnostics
3. Check logs in `logs/obsidian_sync.log`
4. Open an issue on GitHub

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Setup

```bash
git clone https://github.com/yourusername/obsidian-project-sync.git
cd obsidian-project-sync
make install-dev
make test
```