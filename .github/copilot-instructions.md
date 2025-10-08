# RSportal CLI Copilot Instructions

## Project Overview
RSportal CLI is a Python command-line tool for interacting with the RSportal platform offline. The project uses a modular command structure with argparse for CLI handling and keyring for secure credential storage.

## Architecture Patterns

### CLI Command Structure
- **Entry Point**: `main.py` → `rsportal/cli.py` → command handlers
- **Command Pattern**: Each command lives in `rsportal/commands/` with a `handle(args)` function
- **Dual Interface**: Commands support both subcommand syntax (`rsportal auth login`) and flag syntax (`rsportal auth --login`) for backward compatibility

Example from `auth_cmd.py`:
```python
def handle(args):
    # Route subcommands if provided
    if getattr(args, "auth_cmd", None) == "login":
        login()
    # Backward compatibility: flags still work  
    if getattr(args, "login", False):
        login()
```

### Authentication & Storage
- **Credentials**: Stored via `keyring` system service + local JSON file at `~/.rsportal/auth.json`
- **Auth Pattern**: Commands use `utils.require_auth()` to enforce authentication
- **Session Management**: Active user stored in JSON, password in keyring for security

### File Organization
- `rsportal/cli.py`: Argparse setup and command routing
- `rsportal/commands/`: Individual command modules with `handle(args)` functions
- `utils.py`: Shared utilities (currently auth helpers)
- `main.py`: Simple entry point script

## Development Conventions

### Adding New Commands
1. Create `rsportal/commands/new_cmd.py` with `handle(args)` function
2. Add subparser in `cli.py` following the auth command pattern
3. Set `parser.set_defaults(func=new_cmd.handle)`
4. Import the command module in `cli.py`

### Showing Help
- Use `show_help()` function in command modules to print usage
- Help flags (`-h`, `--help`) are automatically handled by argparse

### Error Handling
- Use `exit(1)` for authentication failures (see `utils.require_auth()`)
- Print user-friendly messages with newlines: `print("\nMessage\n")`
- Handle JSON corruption gracefully in auth functions

### Credential Management
- Never store passwords in plain text - use keyring
- Store non-sensitive user data in `~/.rsportal/auth.json`
- Use `SERVICE_NAME = "rsportal"` constant for keyring operations

### Testing & Development
- Project uses `.venv` for virtual environment
- `.rsportal/` directory is git-ignored for local auth data
- Empty `pyproject.toml` suggests manual dependency management

## Key Integration Points
- **Keyring**: Cross-platform credential storage
- **Pathlib**: Used consistently for file operations (`Path.home()`)
- **JSON**: Local configuration and session storage
- **Argparse**: CLI parsing with subcommands and backward-compatible flags

## Incomplete Implementation Notes
- README mentions commands not yet implemented: `time_cmd.py`, `commit_cmd.py`, `log_cmd.py`, `tasks_cmd.py`, `push_cmd.py`
- `pyproject.toml` is empty - packaging configuration needed
- Only auth functionality is currently implemented