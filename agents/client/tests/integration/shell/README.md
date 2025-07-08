# Shell Integration Tests

Shell-based integration tests for the Advanced Agent Runner that test real interactions with Claude CLI and the PM system.

## Prerequisites

1. **Running PM System**: Headless PM must be running at `localhost:6969`
2. **API Key**: Set `HEADLESS_PM_API_KEY` or `API_KEY` environment variable
3. **Claude CLI**: Claude command should be available in PATH
4. **Python Dependencies**: `psutil` package for health checks
5. **Git Repository**: Tests should run from within a git repository

## Running Tests

### Setup Environment
```bash
# Run setup first to verify environment
./setup_test_env.sh
```

### Run All Tests
```bash
# Run complete test suite
./run_all_tests.sh
```

### Run Individual Tests
```bash
# Single task execution test
./test_single_task.sh

# Complete dev to QA workflow
./test_dev_to_qa_flow.sh

# Task recovery after crash
./test_task_recovery.sh

# Continuous mode operation
./test_continuous_mode.sh
```

## Test Descriptions

### `test_single_task.sh`
- Creates a simple file creation task
- Runs advanced runner in single-task mode
- Verifies task status changes to `dev_done`
- Verifies expected file is created with correct content

### `test_dev_to_qa_flow.sh`
- Creates dev and QA agents
- Creates a task and runs dev agent first
- Verifies task moves to `dev_done` status
- Runs QA agent on the same task
- Verifies task reaches `completed` status

### `test_task_recovery.sh`
- Simulates a crash by creating a lock file manually
- Starts runner to test recovery mechanism
- Verifies runner detects and recovers the locked task
- Verifies lock file is cleaned up after completion

### `test_continuous_mode.sh`
- Starts runner in continuous mode (background process)
- Verifies process stays running
- Tests graceful shutdown with SIGTERM

## Test Data Management

All tests use the `test_helpers.sh` library which:
- Automatically creates unique agent IDs and task titles using timestamps
- Tracks created resources (agents, tasks, features, epics)
- Automatically cleans up test data on exit via trap
- Provides helper functions for common operations

## Environment Variables

- `HEADLESS_PM_API_KEY`: API key for PM system authentication
- `HEADLESS_PM_API_URL`: PM API URL (default: http://localhost:6969)
- `TEST_TIMESTAMP`: Automatically set unique timestamp for test isolation

## Troubleshooting

### Tests Fail with "API key not found"
Set the environment variable:
```bash
export HEADLESS_PM_API_KEY="your-key-here"
```

### Tests Fail with "PM API not accessible"
Ensure the PM system is running:
```bash
curl http://localhost:6969/health
```

### Tests Fail with "Claude not found"
Install Claude CLI or ensure it's in your PATH:
```bash
which claude
claude --version
```

### Tests Leave Artifacts
Tests automatically clean up via EXIT trap, but if interrupted forcefully:
```bash
# Manual cleanup using the PM client
python3 ../../../headless_pm_client.py agents list | grep test_
```

## Test Philosophy

These tests follow the principle of:
1. **Real Integration**: Use actual Claude CLI and PM database
2. **No Mocking**: Test the real execution path
3. **Isolated**: Each test cleans up after itself
4. **Fast**: Tests complete in under 60 seconds each
5. **Observable**: Verify database state changes, not just process exit codes