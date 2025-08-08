# SuperMon Scripts

This directory contains modular Python scripts for managing the SuperMon SDLC Automation Platform.

## Structure

- `__init__.py` - Package initialization file
- `utils.py` - Utility functions for all scripts
- `environment.py` - Environment and dependency management
- `database.py` - Database service management
- `services.py` - Backend, frontend, and MCP server management

## Usage

These scripts are used by the main `supermon.py` script in the project root. You should not need to run these scripts directly.

Instead, use the main script or the `start_all.sh` wrapper:

```bash
# Using the Python script directly
python supermon.py [command]

# Using the shell wrapper
./start_all.sh [command]
```

Where `[command]` is one of:
- `start` - Start all services (default)
- `stop` - Stop all services
- `restart` - Restart all services
- `status` - Show service status
- `setup` - Setup dependencies only
- `test` - Run tests
- `format` - Format code
- `lint` - Lint code
- `quality` - Run all quality checks

## Development

If you need to modify the startup behavior, you can modify the appropriate script in this directory. The modular design makes it easy to update specific components without affecting others.