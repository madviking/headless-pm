# Advanced Agent Runner - Implementation Guide

## Overview

The Advanced Agent Runner is a Python-based continuous task execution system designed to enhance the original shell-based runners with sophisticated features like crash recovery, git worktree management, and intelligent model selection.

## Implementation Architecture

### Core Design Principles

1. **Task Persistence**: All task state is persisted to disk to handle crashes gracefully
2. **Component Isolation**: Each feature is implemented as a separate, testable component
3. **No Mocking**: All tests use real implementations and integrations
4. **Shell Integration**: Designed to work seamlessly with shell-based workflows
5. **Backward Compatibility**: Does not replace existing runners, adds new capabilities

### Component Architecture

```
AdvancedAgentRunner
├── TaskPersistence     # Crash recovery via lock files
├── ModelMapper         # Seniority → Claude model mapping
├── TerminalUI          # Colored output and operator prompts
├── GitWorktree         # Git worktree management
├── ClaudeExecutor      # Claude subprocess execution
├── HookRunner          # Global hook system
└── Config              # Environment-based configuration
```

## Key Components

### 1. TaskPersistence (`components/task_persistence.py`)

**Purpose**: Ensures task continuity across crashes and restarts.

**Implementation Details**:
- Stores lock files in `~/.headless-pm/locks/agent-{id}.lock`
- JSON format with task data, timestamps, and worktree paths
- Automatic cleanup on successful completion
- Age tracking for debugging stale locks

**Key Methods**:
```python
def lock_task(task, worktree_path=None, branch_name=None)
def get_locked_task() -> Optional[Dict]
def release_lock()
def is_locked() -> bool
```

### 2. ModelMapper (`components/model_mapper.py`)

**Purpose**: Maps task seniority levels to appropriate Claude models.

**Model Selection**:
- Junior tasks → Claude 3.5 Sonnet
- Senior tasks → Claude 3.5 Sonnet  
- Principal tasks → Claude 3 Opus

**Rationale**: Claude Code only supports Sonnet and Opus, so we use Sonnet for most tasks and reserve Opus for the most complex (principal) work.

### 3. GitWorktree (`components/git_worktree.py`)

**Purpose**: Manages isolated git worktrees for major tasks.

**Implementation**:
- Creates worktrees in `.worktrees/task-{id}/` 
- Uses native `git worktree` commands
- Automatic cleanup after task completion
- Branch creation for new features

**Workflow**:
```bash
# For major tasks
git worktree add .worktrees/task-123 feature/task-123
# ... work in isolated directory ...
git worktree remove .worktrees/task-123
```

### 4. HookRunner (`components/hook_runner.py`)

**Purpose**: Execute validation and cleanup scripts at key points.

**Hook Types**:
- `pre_task.py` - System validation before starting
- `post_task.py` - Cleanup and logging after completion  
- `health_check.py` - Periodic system health monitoring

**Hook Interface**:
- Input: JSON data via stdin
- Output: Messages to stdout
- Exit code: 0 = success, non-zero = failure

### 5. ClaudeExecutor (`components/claude_executor.py`)

**Purpose**: Manage Claude subprocess execution with proper model selection.

**Features**:
- Automatic Claude CLI discovery
- Model selection based on task seniority
- Timeout handling (default 10 minutes)
- Environment variable passthrough

### 6. TerminalUI (`components/terminal_ui.py`)

**Purpose**: Provide clean, informative terminal output.

**Features**:
- Color-coded messages (info, success, error, warning)
- Progress indicators
- Task information display
- Blocking operator prompts for manual intervention

## Configuration System

### Environment Variables

```bash
# Required
HEADLESS_PM_API_KEY="your-api-key"

# Optional
HEADLESS_PM_API_URL="http://localhost:6969"
HEADLESS_PM_WORKTREE_BASE="/tmp/headless-pm-worktrees"
HEADLESS_PM_HOOK_TIMEOUT=30
HEADLESS_PM_CLAUDE_TIMEOUT=600
HEADLESS_PM_HEALTH_CHECK_INTERVAL=300
```

### Configuration Discovery

The `Config` class automatically discovers:
- Team roles directory (searches multiple locations)
- API keys (multiple environment variable names)
- Claude CLI location (common installation paths)

## Task Execution Flow

### 1. Startup Sequence
```python
1. Load configuration and validate environment
2. Verify Claude CLI availability
3. Register agent with PM system
4. Initialize all components
5. Enter main execution loop
```

### 2. Task Processing
```python
1. Check for previously locked task (crash recovery)
2. If no locked task, get next task from API
3. Lock task locally and in PM system
4. Run pre-task hooks
5. Set up git worktree if needed (major tasks)
6. Execute Claude with appropriate model
7. Update task status in PM system
8. Run post-task hooks
9. Clean up worktree
10. Release lock
```

### 3. Error Handling
- **Claude crashes**: Immediate restart with same task
- **Hook failures**: Operator prompt for decision
- **API errors**: Retry with backoff
- **Git errors**: Continue without worktree

## Testing Strategy

### Shell-Based Integration Tests

**Philosophy**: Test the actual CLI interface with real components.

**Test Structure**:
```bash
tests/integration/shell/
├── test_helpers.sh       # Common functions and cleanup
├── setup_test_env.sh     # Environment validation
├── run_all_tests.sh      # Test runner
├── test_single_task.sh   # Basic task execution
├── test_dev_to_qa_flow.sh # Complete workflow
├── test_task_recovery.sh # Crash recovery
└── test_continuous_mode.sh # Background operation
```

**Test Pattern**:
1. Create test agents and tasks using PM API
2. Run actual Claude CLI via advanced runner
3. Verify database state changes
4. Check file system artifacts
5. Automatic cleanup via EXIT traps

### Why Shell Tests?

- **Real Integration**: Tests actual subprocess execution
- **No Mocking**: Uses real Claude CLI and PM database
- **Observable**: Can verify file creation and DB state
- **Shell Native**: Natural for testing CLI tools
- **Fast Feedback**: Complete in under 60 seconds

## Implementation Decisions

### Task Persistence Format

**Choice**: JSON files in home directory
**Rationale**: 
- Simple to implement and debug
- Survives process crashes
- Human-readable for troubleshooting
- Per-agent isolation

### Model Selection Strategy

**Choice**: Direct mapping without escalation
**Rationale**:
- Predictable behavior
- No complex retry logic needed
- Clear cost implications
- Matches Claude Code capabilities

### Git Worktree Usage

**Choice**: Only for major tasks
**Rationale**:
- Minor tasks don't need isolation
- Reduces complexity for simple changes
- Matches existing Git workflow patterns
- Automatic cleanup easier to manage

### Hook System Design

**Choice**: Global, not per-role
**Rationale**:
- Simpler to maintain
- Consistent behavior across agents
- System-wide health checks
- User requested global approach

## Deployment Considerations

### Development Environment
```bash
# Single task for testing
python advanced_agent_runner.py --role backend_dev --agent-id dev_001 --single-task

# Continuous development
python advanced_agent_runner.py --role backend_dev --agent-id dev_001
```

### Production Environment
```bash
# Run in background with logging
nohup python advanced_agent_runner.py \
    --role backend_dev --agent-id prod_dev_001 \
    > agent.log 2>&1 &

# Monitor with tail
tail -f agent.log
```

### Health Monitoring
- Lock file ages (detect stuck agents)
- Hook execution success rates
- Task completion times
- API response times

## Future Enhancements

### Planned Features
1. **Metrics Collection**: Task timing, success rates, model usage
2. **Advanced Recovery**: Partial task state restoration
3. **Multi-Agent Coordination**: Resource conflict detection
4. **Dynamic Hook Loading**: Custom hooks per project
5. **Web Dashboard Integration**: Real-time agent monitoring

### Extension Points
- **Custom Executors**: Support for other LLMs
- **Alternative Persistence**: Database-backed locks
- **Advanced Git Integration**: Automatic PR creation
- **Notification System**: Slack/Discord integration

## Troubleshooting

### Common Issues

**Agent won't start**:
- Check API key: `echo $HEADLESS_PM_API_KEY`
- Verify PM API: `curl localhost:6969/health`
- Check Claude CLI: `claude --version`

**Tasks not picked up**:
- Verify agent registration
- Check task availability for role/skill
- Review PM API logs

**Worktree errors**:
- Ensure git repository
- Check disk space
- Verify git version supports worktrees

**Hook failures**:
- Make scripts executable: `chmod +x hooks/*.py`
- Check Python dependencies
- Review hook output for errors

### Debug Mode
```bash
# Enable verbose logging
PYTHONPATH=. python -v advanced_agent_runner.py \
    --role backend_dev --agent-id debug_001 --single-task
```

## Security Considerations

### Lock File Security
- Stored in user home directory
- Contains task data but no secrets
- Readable only by user (file permissions)

### Hook Execution
- Scripts run with same privileges as runner
- No input sanitization (trusted environment)
- Can execute arbitrary commands

### Claude Integration
- Passes through environment variables
- Runs in working directory
- Has access to git repository

### Mitigation Strategies
1. Run in isolated containers
2. Use read-only git checkouts
3. Monitor hook script changes
4. Regular security audits of instructions

## Contributing

### Development Setup
1. Create virtual environment
2. Install dependencies: `pip install psutil`
3. Set environment variables
4. Run tests: `./tests/integration/shell/run_all_tests.sh`

### Adding Components
1. Create component in `components/`
2. Add to `__init__.py` imports
3. Write unit tests (if applicable)
4. Add integration test coverage
5. Update documentation

### Testing Guidelines
- All shell tests must clean up automatically
- Use real PM API and database
- Test both success and failure cases
- Verify observable behavior (files, DB state)
- Keep test execution under 60 seconds