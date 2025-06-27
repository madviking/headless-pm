# Claude Agent Runner

Intelligent monitoring and management system for Claude Code agents in the Headless PM system.

## ⚠️ IMPORTANT SECURITY WARNING ⚠️

**NEVER run agents with `--dangerously-skip-permissions` in production or with untrusted code!**

The `--dangerously-skip-permissions` flag bypasses Claude's safety checks and allows agents to:
- Execute ANY command without confirmation
- Modify or delete ANY file without warning
- Access sensitive data without restrictions
- Run potentially destructive operations

**Only use this flag when:**
- You are in a controlled development environment
- You fully trust the codebase and instructions
- You have backups of important data
- You understand and accept the risks

**We strongly recommend:**
- Running agents WITHOUT this flag in most cases
- Using version control (git) to track changes
- Running in isolated environments or containers when possible

## Installation

### Global Installation (Recommended)

Install the agent runner to your system PATH for easy access from any project:

```bash
# Navigate to your headless-pm project
cd /path/to/your/headless-pm-project

# Run the installation script
./agents/client/runners/install.sh
```

This will:
- Create a `headless-agent` command in your PATH
- Allow you to run agents from any directory within any headless-pm project
- Automatically detect the correct project structure and paths

**After installation, you can run:**
```bash
# From anywhere in your project
headless-agent backend_dev dev_001
headless-agent qa qa_001 --one-task-only
headless-agent frontend_dev dev_002
```

### Manual PATH Setup

If the installer can't automatically configure your PATH:

```bash
# For bash users
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# For zsh users  
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Direct Usage (Without Installation)

```bash
# From project root
./agents/client/runners/agent_runner.sh backend_dev dev_001

# From any directory
/path/to/headless-pm/agents/client/runners/agent_runner.sh backend_dev dev_001
```

## Features

- **Universal Path Detection**: Automatically finds `headless_pm_client.py` from any directory
- **Automatic Restart**: Restarts Claude sessions with 30-second cooldown
- **Multiple Claude Versions**: Detects and uses the best Claude installation (local or global)
- **Full Output Visibility**: See everything Claude does in real-time
- **Environment Support**: Loads `.env` files from project and headless_pm directories
- **Flexible Installation**: Run directly or install to PATH for global access

## Usage

### Basic Syntax
```bash
headless-agent <role> <agent_id> [options]

# OR (without global installation)
./agents/client/runners/agent_runner.sh <role> <agent_id> [options]
```

### Arguments

- `role`: Agent role (backend_dev, frontend_dev, qa, architect, pm, fullstack_dev)
- `agent_id`: Unique identifier for the agent (e.g., dev_001, qa_001)

### Options

- `--one-task-only`: Complete only one task then exit
- `--stop-on-sonnet`: Stop immediately when Claude switches to Sonnet
- `--dangerously-skip-permissions`: ⚠️ **DANGEROUS** - Skip all permission prompts

### Safe Examples (Recommended)
```bash
# Normal operation - Claude will ask for permission before making changes
headless-agent backend_dev dev_001
headless-agent qa qa_001 --one-task-only
headless-agent frontend_dev dev_002 --stop-on-sonnet
```

### ⚠️ Dangerous Examples (Use with Extreme Caution)
```bash
# ONLY use in trusted, controlled environments with backups!
headless-agent backend_dev dev_001 --dangerously-skip-permissions

# Example of combining flags (DANGEROUS)
headless-agent qa qa_001 --one-task-only --dangerously-skip-permissions
```

**Remember:** The `--dangerously-skip-permissions` flag allows agents to modify your codebase without asking. Only use it when you fully trust the code and have proper backups!

## Environment Setup

The runner automatically loads API configuration from:
1. `./.env` (project root)
2. `./headless_pm/.env` (if exists, overrides root settings)

Required environment variables:
- `API_KEY` or `HEADLESS_PM_API_KEY`: API authentication key
- `API_BASE_URL`: API endpoint (defaults to http://localhost:6969)

## How It Works

### Path Resolution
The runner automatically detects your project structure:

1. **Finds Project Root** by looking for:
   - `headless_pm_client.py` in current or parent directories
   - `.git/config` with headless_pm subdirectory
   - Common project markers

2. **Locates Client Script** in order:
   - `./headless_pm_client.py` (root level)
   - `./headless_pm/headless_pm_client.py` (subdirectory)
   - `./agents/client/headless_pm_client.py` (agents directory)

3. **Sets Environment**:
   - `HEADLESS_PM_CLIENT_PATH` - full path to client script
   - Agents can use `$HEADLESS_PM_CLIENT_PATH` in their commands

### Execution Flow
1. Runner detects all paths and validates setup
2. Python monitor manages Claude sessions
3. Claude runs with full terminal access (no buffering)
4. Sessions restart automatically after exit

## Output Features

### Live Status Updates
```
📊 Session: 15m | Tasks: 2 | State: task_locked | Current: #123
```

### Terminal Title
```
[backend_dev - dev_001] Task #123
```

### Session Reports
```
📊 Session Report
================
Duration: 45.2 minutes
Tasks completed: 3
Total API calls: 27

Call Summary:
  - register: 1
  - next_task: 4
  - lock_task: 3
  - complete_task: 3
  - create_document: 16

⚠️  Warnings:
  - Task 122 was not completed before locking new task
```

## Monitoring Patterns

The monitor detects:
- Client API calls (`headless_pm_client.py` commands)
- Model switches ("now using Claude Sonnet")
- Task lifecycle events
- Error conditions
- Inactivity periods

## Logs

Detailed session logs are saved to:
```
./agent_logs/<agent_id>_<timestamp>.json
```

Each log contains:
- Complete call sequence with timestamps
- Session metrics and warnings
- Task completion analysis

## Interactive Features

### Sending Prompts Mid-Flight

While an agent is running, you can send additional prompts to Claude:

1. **Press Enter twice** in the terminal where the agent is running
2. You'll see: `📝 Enter your prompt (press Ctrl+D when done):`
3. Type your prompt (can be multiple lines)
4. Press **Ctrl+D** to send it to Claude
5. Claude will respond to your prompt and continue with the task

Example:
```
[Agent output continues...]

[Press Enter twice]

📝 Enter your prompt (press Ctrl+D when done):
Hey Claude, can you also add error handling to this function?
[Press Ctrl+D]

✅ Sent to Claude: Hey Claude, can you also add error handling...

[Claude responds and continues working]
```

## Advanced Usage

### Running Multiple Agents
```bash
# In separate terminals (from runners directory)
./agent_runner.sh backend_dev dev_001
./agent_runner.sh frontend_dev dev_002
./agent_runner.sh qa qa_001
```

### Debugging
Monitor the output for:
- ⚠️ Warning symbols for issues
- 📊 Status bars for current state
- ⏸️ Pause indicators when waiting
- ✅ Success messages

## Troubleshooting

### Agent keeps restarting
- Check if tasks are available in the system
- Verify API connectivity and authentication
- Look for errors in the output

### Model switching issues
- Ensure `/model` endpoint is accessible
- Check API key has proper permissions
- Verify Opus availability in your environment

### No output visible
- Ensure terminal supports ANSI escape codes
- Check file permissions on scripts
- Verify Claude is installed and accessible