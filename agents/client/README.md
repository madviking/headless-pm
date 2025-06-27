# Python Client Agent Instructions for Headless PM

This directory contains role-specific instructions for agents using the Python client integration.

## ⚠️ IMPORTANT SECURITY WARNING ⚠️

**These agent tools can execute code and modify files automatically. Always:**
- Review agent instructions before running
- Run in controlled development environments only
- Use version control and maintain backups
- Understand the risks of `--dangerously-skip-permissions` mode

## 🚀 Agent Runner

For automated agent execution, use the agent runner system:

### Global Installation
```bash
# Install agent runner to your PATH
./runners/install.sh

# Run from anywhere in your project
headless-agent backend_dev dev_001
```

### Direct Usage
```bash
# Run agent runner directly
./runners/agent_runner.sh backend_dev dev_001

# Safe mode (asks for permission)
./runners/agent_runner.sh qa qa_001 --one-task-only

# ⚠️ DANGEROUS - only in trusted environments
./runners/agent_runner.sh backend_dev dev_001 --dangerously-skip-permissions
```

See [Agent Runner Documentation](runners/README.md) for detailed security guidelines and usage.

## Installation in Your Own Projects

To use headless-pm agents in your own projects, you need to copy the client system:

### Method 1: Using Setup Script (Recommended)

```bash
# FROM the headless-pm repository:
cd /path/to/headless-pm
./agents/client/setup_in_project.sh /path/to/your/other/project

# This creates: your-project/headless_pm/ with everything needed
```

### Method 2: Manual Copy

```bash
# Copy the entire client directory to your project
cp -r /path/to/headless-pm/agents/client /path/to/your/project/headless_pm
```

### What Gets Installed

Your project will have:
```
your-project/
└── headless_pm/
    ├── headless_pm_client.py   # API client
    ├── team_roles/             # Agent instructions
    │   ├── backend_dev.md
    │   ├── frontend_dev.md
    │   └── ...
    └── runners/                # Agent automation
        ├── agent_runner.sh
        ├── agent_monitor.py
        └── install.sh
```

## Using Agents in Your Project

After installation:

```bash
cd /path/to/your/project

# Run directly
./headless_pm/runners/agent_runner.sh backend_dev dev_001

# Or install globally (recommended)
./headless_pm/runners/install.sh
headless-agent backend_dev dev_001
```

## Overview

The Python client provides a programmatic interface to Headless PM, allowing you to integrate task management directly into your code workflow.


## Troubleshooting

- **Connection Refused**: Ensure the API server is running on port 6969
- **Task Not Found**: The task may be locked by another agent
- **Registration Failed**: Check that your role is valid
- **Import Errors**: Ensure you're importing from the correct path

