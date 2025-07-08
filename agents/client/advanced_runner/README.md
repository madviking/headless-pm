# Advanced Claude PM Runner

A Python-based continuous task execution system for Headless PM with git worktree support, task persistence, and global hooks.

## Features

- **Continuous Operation**: Automatically picks up and executes tasks in a loop
- **Crash Recovery**: Persists task state to disk for seamless recovery after crashes
- **Git Worktree Support**: Creates isolated worktrees for major tasks
- **Model Selection**: Automatically selects Claude model based on task seniority
- **Global Hooks**: Pre/post task hooks for validation and cleanup
- **Terminal UI**: Clean, colored terminal output with operator prompts
- **Health Monitoring**: Periodic health checks for system stability

## Installation

1. Ensure you're in a virtual environment:
```bash
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install psutil  # Required for health checks
```

3. Set up environment variables:
```bash
export HEADLESS_PM_API_KEY="your-api-key"
export HEADLESS_PM_API_URL="http://localhost:6969"  # Optional, defaults to localhost
```

## Usage

### Basic Usage

Run continuously, picking up tasks as they become available:
```bash
python agents/client/advanced_runner/advanced_agent_runner.py \
    --role backend_dev \
    --agent-id dev_001
```

### Single Task Mode

Run one task and exit (useful for testing):
```bash
python agents/client/advanced_runner/advanced_agent_runner.py \
    --role backend_dev \
    --agent-id dev_001 \
    --single-task
```

### Custom Hooks Directory

Use custom hook scripts:
```bash
python agents/client/advanced_runner/advanced_agent_runner.py \
    --role qa \
    --agent-id qa_001 \
    --hooks-dir /path/to/custom/hooks
```

## Configuration

### Environment Variables

- `HEADLESS_PM_API_KEY`: API key for authentication (required)
- `HEADLESS_PM_API_URL`: PM API URL (default: http://localhost:6969)
- `HEADLESS_PM_WORKTREE_BASE`: Base directory for git worktrees (default: /tmp/headless-pm-worktrees)
- `HEADLESS_PM_HOOK_TIMEOUT`: Hook execution timeout in seconds (default: 30)
- `HEADLESS_PM_CLAUDE_TIMEOUT`: Claude execution timeout in seconds (default: 600)
- `HEADLESS_PM_HEALTH_CHECK_INTERVAL`: Health check interval in seconds (default: 300)

### Model Selection

The runner automatically selects the appropriate Claude model based on task seniority:
- **Junior tasks**: Claude 3.5 Sonnet
- **Senior tasks**: Claude 3.5 Sonnet
- **Principal tasks**: Claude 3 Opus

## Hooks

The runner supports three types of hooks:

### Pre-Task Hook (`pre_task.py`)
- Runs before starting a task
- Can block task execution if checks fail
- Use for system health checks, disk space, etc.

### Post-Task Hook (`post_task.py`)
- Runs after task completion
- Non-blocking (failures don't affect task status)
- Use for cleanup, logging, metrics

### Health Check Hook (`health_check.py`)
- Runs periodically during continuous operation
- Checks system health, API connectivity, etc.

## Task Persistence

The runner automatically persists task state to handle crashes:
- Lock files stored in `~/.headless-pm/locks/`
- Contains task ID, agent ID, worktree path, and timestamp
- Automatically recovered on restart

## Git Worktree Management

For major tasks (complexity = "major"):
- Creates dedicated git worktree in `.worktrees/task-{id}/`
- Isolates changes from main repository
- Automatically cleaned up after task completion

## Testing

Run integration tests with:
```bash
pytest agents/client/tests/integration/ -v
```

Tests require:
- Running Headless PM instance at localhost:6969
- Valid API key in environment
- Claude CLI installed and accessible

## Architecture

```
advanced_runner/
├── advanced_agent_runner.py    # Main entry point
├── config.py                   # Configuration management
├── components/
│   ├── task_persistence.py     # Task lock management
│   ├── model_mapper.py         # Seniority to model mapping
│   ├── terminal_ui.py          # Terminal output and prompts
│   ├── git_worktree.py         # Git worktree operations
│   ├── claude_executor.py      # Claude subprocess management
│   └── hook_runner.py          # Hook script execution
└── hooks/
    ├── pre_task.py            # Pre-task validation
    ├── post_task.py           # Post-task cleanup
    └── health_check.py        # System health monitoring
```

## Troubleshooting

### Runner won't start
- Check API key is set: `echo $HEADLESS_PM_API_KEY`
- Verify PM API is running: `curl http://localhost:6969/health`
- Ensure Claude CLI is installed: `claude --version`

### Tasks not being picked up
- Check agent is registered with correct role
- Verify tasks exist for your role/skill level
- Check PM API logs for errors

### Worktree errors
- Ensure you're in a git repository
- Check git version supports worktrees: `git worktree --help`
- Verify sufficient disk space in worktree base directory

### Hook failures
- Make hook scripts executable: `chmod +x hooks/*.py`
- Check hook script dependencies are installed
- Review hook output in terminal for specific errors