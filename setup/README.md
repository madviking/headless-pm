# Setup Directory

This directory contains installation and setup scripts for Headless PM.

## Quick Start

```bash
# From project root, run:
./setup/universal_setup.sh
```

This handles everything automatically based on your platform.

## Scripts

### universal_setup.sh (Recommended)
Universal setup that works for both architectures:
- Automatically detects architecture (ARM64 vs x86_64)
- Creates appropriate venv (`venv` for ARM64, `claude_venv` for x86_64)
- Installs correct pydantic versions for platform compatibility
- Creates .env from env-example if needed

### create_claude_venv.sh
Legacy script for Claude Code environment. Use `universal_setup.sh` instead.

### setup_dev_env.sh
Legacy development environment setup. Use `universal_setup.sh` instead.

## Requirements Files

### requirements.txt
Core dependencies for the project:
- Production dependencies
- Platform-specific notes for pydantic versions

### requirements-dev.txt
Optional development dependencies:
- Code formatting (black, ruff)
- Type checking (mypy)
- Documentation tools
- Additional testing utilities

Install with: `pip install -r setup/requirements-dev.txt`

## Platform Compatibility

The project handles platform differences automatically:

- **ARM64 (Native Mac)**: Uses standard `venv` with normal installations
- **x86_64 (Claude Code)**: Uses `claude_venv` with specific pydantic versions

The universal_setup.sh script detects and configures everything automatically.

## Environment Configuration

After setup, a `.env` file will be created from `env-example`. Edit it with your configuration:

```env
# API Configuration
API_KEY_HEADLESS_PM=your_api_key
SERVICE_PORT=6969
MCP_PORT=6968
DASHBOARD_PORT=3001

# Database
DATABASE_URL=sqlite:///headless_pm.db
# Or for MySQL:
# DATABASE_URL=mysql://user:password@localhost/headless_pm
```

## Troubleshooting

If you encounter issues:

1. **Wrong architecture packages**: Delete the venv and run `universal_setup.sh`
2. **Import errors**: Ensure you're using the correct venv for your platform
3. **Permission errors**: Make scripts executable with `chmod +x setup/*.sh`