# Advanced Claude PM Runner - Focused Implementation Plan

## Overview
Create a new Python-based runner system for continuous Claude agent operation with git worktree support, global hooks, and task persistence.

## Key Design Decisions (Based on Feedback)
1. **Git Worktrees**: Managed by git itself (use `git worktree` commands)
2. **Hooks**: Global system for continuous operation assurance
3. **New Runner**: Fresh `advanced_agent_runner.py` - no backward compatibility needed
4. **UI**: Terminal output only, operator prompts block execution
5. **Recovery**: Immediate restart with task persistence (prevent accidental task switching)
6. **Model Selection**: Based purely on task seniority level (junior→Sonnet, senior→Sonnet, principal→Opus)
7. **Testing**: Real integration tests with actual Claude and database state verification

## Architecture

```
headless-pm/
├── agents/
│   └── client/
│       ├── advanced_runner/
│       │   ├── __init__.py
│       │   ├── advanced_agent_runner.py    # Main entry point
│       │   ├── components/
│       │   │   ├── __init__.py
│       │   │   ├── git_worktree.py        # Git worktree operations
│       │   │   ├── task_persistence.py     # Task locking/persistence
│       │   │   ├── hook_runner.py          # Global hook execution
│       │   │   ├── model_mapper.py         # Seniority→Model mapping
│       │   │   ├── claude_executor.py      # Claude process management
│       │   │   └── terminal_ui.py          # Terminal output/prompts
│       │   ├── hooks/
│       │   │   ├── pre_task.py            # Run before starting task
│       │   │   ├── post_task.py           # Run after task completion
│       │   │   └── health_check.py        # Periodic health verification
│       │   └── config.py                   # Configuration management
│       └── tests/
│           └── integration/
│               ├── __init__.py
│               ├── test_full_workflow.py   # End-to-end task flow
│               ├── test_task_recovery.py   # Crash/restart scenarios
│               └── fixtures.py             # Test task creation
```

## Implementation Phases

### Phase 1: Core Components (Week 1)

#### 1.1 Advanced Agent Runner (Main Entry)
**File**: `agents/client/advanced_runner/advanced_agent_runner.py`
```python
#!/usr/bin/env python3
"""
Advanced Claude PM Runner - Continuous task execution with git worktree support
"""
import argparse
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from headless_pm_client import HeadlessPMClient
from components import (
    GitWorktree, TaskPersistence, HookRunner, 
    ModelMapper, ClaudeExecutor, TerminalUI
)

class AdvancedAgentRunner:
    def __init__(self, role: str, agent_id: str):
        self.role = role
        self.agent_id = agent_id
        self.client = HeadlessPMClient()
        self.persistence = TaskPersistence(agent_id)
        self.ui = TerminalUI()
        
    def run_continuous(self):
        """Main execution loop with task persistence"""
        while True:
            # Check for locked task first (crash recovery)
            task = self.persistence.get_locked_task()
            
            if not task:
                # Get new task
                task = self.get_next_task()
                if not task:
                    self.ui.info("No tasks available, waiting...")
                    time.sleep(30)
                    continue
                    
                # Lock task
                self.persistence.lock_task(task)
                
            # Execute task
            self.execute_task(task)
```

#### 1.2 Task Persistence
**File**: `agents/client/advanced_runner/components/task_persistence.py`
```python
"""
Ensures task continuity across crashes/restarts
Stores: task_id, agent_id, lock_time, worktree_path
"""
import json
from pathlib import Path

class TaskPersistence:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.lock_file = Path.home() / f".headless-pm-lock-{agent_id}.json"
        
    def lock_task(self, task: dict):
        """Persist task lock to filesystem"""
        
    def get_locked_task(self) -> dict:
        """Retrieve previously locked task if exists"""
        
    def release_lock(self):
        """Clean up lock file"""
```

#### 1.3 Model Mapper
**File**: `agents/client/advanced_runner/components/model_mapper.py`
```python
"""
Maps task seniority to Claude model
Note: Claude Code only supports Opus and Sonnet
"""
class ModelMapper:
    MAPPING = {
        'junior': 'claude-3-5-sonnet-20241022',
        'senior': 'claude-3-5-sonnet-20241022', 
        'principal': 'claude-3-opus-20240229'
    }
    
    def get_model(self, seniority: str) -> str:
        return self.MAPPING.get(seniority, 'claude-3-5-sonnet-20241022')
```

### Phase 2: Git and Hook Integration (Week 1-2)

#### 2.1 Git Worktree Manager
**File**: `agents/client/advanced_runner/components/git_worktree.py`
```python
"""
Manages git worktrees for feature branches
"""
import subprocess
from pathlib import Path

class GitWorktree:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.worktrees_dir = base_path / '.worktrees'
        
    def create_for_task(self, task_id: int, branch_name: str) -> Path:
        """Create worktree for feature branch"""
        worktree_path = self.worktrees_dir / f"task-{task_id}"
        
        # git worktree add <path> <branch>
        subprocess.run([
            'git', 'worktree', 'add', 
            str(worktree_path), branch_name
        ], check=True)
        
        return worktree_path
        
    def cleanup(self, task_id: int):
        """Remove worktree after task completion"""
        worktree_path = self.worktrees_dir / f"task-{task_id}"
        
        # git worktree remove <path>
        subprocess.run([
            'git', 'worktree', 'remove', str(worktree_path)
        ], check=True)
```

#### 2.2 Global Hook Runner
**File**: `agents/client/advanced_runner/components/hook_runner.py`
```python
"""
Executes global hooks for continuous operation assurance
"""
class HookRunner:
    def __init__(self, hooks_dir: Path):
        self.hooks_dir = hooks_dir
        
    def run_pre_task(self, task: dict) -> bool:
        """Run pre-task hooks, return False to skip task"""
        
    def run_post_task(self, task: dict, success: bool):
        """Run post-task hooks for cleanup/validation"""
        
    def run_health_check(self) -> bool:
        """Periodic health verification"""
```

### Phase 3: Claude Execution and UI (Week 2)

#### 3.1 Claude Executor
**File**: `agents/client/advanced_runner/components/claude_executor.py`
```python
"""
Manages Claude subprocess with proper model selection
"""
import subprocess
from pathlib import Path

class ClaudeExecutor:
    def __init__(self, model_mapper: ModelMapper):
        self.model_mapper = model_mapper
        
    def execute_task(self, task: dict, worktree_path: Path, 
                    instructions_path: Path) -> bool:
        """
        Run Claude with task-specific configuration
        Returns True if task completed successfully
        """
        model = self.model_mapper.get_model(task['skill_level'])
        
        # Build Claude command
        cmd = [
            'claude',
            '--model', model,
            '--dangerously-skip-permissions'
        ]
        
        # Execute with timeout and capture output
        result = subprocess.run(
            cmd,
            stdin=open(instructions_path),
            cwd=worktree_path,
            timeout=600  # 10 minutes
        )
        
        return result.returncode == 0
```

#### 3.2 Terminal UI
**File**: `agents/client/advanced_runner/components/terminal_ui.py`
```python
"""
Terminal output with operator prompts (blocking)
"""
import sys
from datetime import datetime

class TerminalUI:
    # Color codes
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    
    def info(self, message: str):
        """Standard info output"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"{self.BLUE}[{timestamp}]{self.RESET} {message}")
        
    def success(self, message: str):
        """Success message"""
        print(f"{self.GREEN}✓{self.RESET} {message}")
        
    def error(self, message: str):
        """Error message"""
        print(f"{self.RED}✗{self.RESET} {message}")
        
    def prompt_operator(self, message: str, options: list) -> str:
        """
        Blocking prompt for operator intervention
        Returns selected option
        """
        print(f"\n{self.YELLOW}⚠ Operator Intervention Required{self.RESET}")
        print(f"{message}\n")
        
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
            
        while True:
            choice = input("\nSelect option: ")
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                return options[int(choice) - 1]
            print("Invalid choice, try again")
```

### Phase 4: Integration Testing (Week 3)

#### 4.1 Full Workflow Test
**File**: `agents/client/tests/integration/test_full_workflow.py`
```python
"""
Real integration test with Claude and database
"""
import pytest
import time
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))
from headless_pm_client import HeadlessPMClient
from advanced_runner.advanced_agent_runner import AdvancedAgentRunner

class TestFullWorkflow:
    @pytest.fixture
    def setup_test_environment(self):
        """Create test task and agents"""
        client = HeadlessPMClient()
        
        # Register test agents
        dev_agent = client.register_agent(
            agent_id="test_dev_001",
            role="backend_dev",
            skill_level="junior"
        )
        
        qa_agent = client.register_agent(
            agent_id="test_qa_001",
            role="qa",
            skill_level="junior"
        )
        
        # Create simple test task
        epic = client.create_epic(
            name="Test Epic",
            description="Integration test epic"
        )
        
        feature = client.create_feature(
            epic_id=epic['id'],
            name="Test Feature",
            description="Integration test feature"
        )
        
        task = client.create_task(
            feature_id=feature['id'],
            title="Create hello.txt with 'Hello World'",
            description="Simple test task - create hello.txt file containing 'Hello World'",
            skill_level="junior",
            complexity="minor"
        )
        
        yield {
            'client': client,
            'task': task,
            'dev_agent': dev_agent,
            'qa_agent': qa_agent
        }
        
        # Cleanup
        client.delete_task(task['id'])
        client.delete_feature(feature['id'])
        client.delete_epic(epic['id'])
        client.delete_agent(dev_agent['id'])
        client.delete_agent(qa_agent['id'])
        
    def test_dev_to_qa_flow(self, setup_test_environment):
        """Test complete task flow from dev to QA to done"""
        env = setup_test_environment
        client = env['client']
        task = env['task']
        
        # Start dev runner (with timeout)
        dev_runner = AdvancedAgentRunner(
            role="backend_dev",
            agent_id="test_dev_001"
        )
        
        # Run one task
        dev_runner.run_single_task()
        
        # Verify task moved to dev_done
        updated_task = client.get_task(task['id'])
        assert updated_task['status'] == 'dev_done'
        
        # Verify file was created
        assert Path('hello.txt').exists()
        assert Path('hello.txt').read_text() == 'Hello World'
        
        # Start QA runner
        qa_runner = AdvancedAgentRunner(
            role="qa",
            agent_id="test_qa_001"
        )
        
        # Run QA verification
        qa_runner.run_single_task()
        
        # Verify task completed
        final_task = client.get_task(task['id'])
        assert final_task['status'] == 'completed'
        
        # Cleanup test file
        Path('hello.txt').unlink()
```

#### 4.2 Recovery Test
**File**: `agents/client/tests/integration/test_task_recovery.py`
```python
"""
Test crash recovery and task persistence
"""
class TestTaskRecovery:
    def test_crash_recovery(self, setup_test_environment):
        """Simulate crash and verify task persistence"""
        env = setup_test_environment
        
        # Start runner
        runner = AdvancedAgentRunner(
            role="backend_dev", 
            agent_id="test_dev_recovery"
        )
        
        # Get task and lock it
        task = runner.get_next_task()
        runner.persistence.lock_task(task)
        
        # Simulate crash (create new runner instance)
        new_runner = AdvancedAgentRunner(
            role="backend_dev",
            agent_id="test_dev_recovery"
        )
        
        # Should recover same task
        recovered_task = new_runner.persistence.get_locked_task()
        assert recovered_task['id'] == task['id']
```

## Hook Examples

### Pre-Task Hook
**File**: `agents/client/advanced_runner/hooks/pre_task.py`
```python
#!/usr/bin/env python3
"""Check system health before starting task"""
import sys
import shutil

# Check git is clean
# Check disk space
# Check Claude is available

if shutil.disk_usage('.').free < 1_000_000_000:  # 1GB
    print("ERROR: Low disk space")
    sys.exit(1)
    
sys.exit(0)  # All good
```

### Post-Task Hook  
**File**: `agents/client/advanced_runner/hooks/post_task.py`
```python
#!/usr/bin/env python3
"""Cleanup and validation after task"""
import sys
import json

# Read task result from stdin
task_result = json.loads(sys.stdin.read())

# Cleanup any temp files
# Validate git state
# Check for common issues

sys.exit(0)
```

## Configuration

### Environment Variables
```bash
# Required
export HEADLESS_PM_API_KEY="your-key"
export HEADLESS_PM_API_URL="http://localhost:6969"

# Optional
export HEADLESS_PM_WORKTREE_BASE="/tmp/headless-pm-worktrees"
export HEADLESS_PM_HOOK_TIMEOUT=30
export HEADLESS_PM_CLAUDE_TIMEOUT=600
```

### Usage
```bash
# Activate virtual environment
source venv/bin/activate

# Run continuous mode
python agents/client/advanced_runner/advanced_agent_runner.py \
    --role backend_dev \
    --agent-id dev_001

# Run single task (for testing)
python agents/client/advanced_runner/advanced_agent_runner.py \
    --role backend_dev \
    --agent-id dev_001 \
    --single-task

# With custom hooks directory
python agents/client/advanced_runner/advanced_agent_runner.py \
    --role backend_dev \
    --agent-id dev_001 \
    --hooks-dir /path/to/custom/hooks
```

## Key Implementation Details

### Task Persistence Format
```json
{
    "task_id": 123,
    "agent_id": "dev_001",
    "locked_at": "2024-01-01T12:00:00Z",
    "worktree_path": "/tmp/headless-pm-worktrees/task-123",
    "branch_name": "feature/task-123"
}
```

### Model Selection Logic
- Task has `skill_level` field: junior, senior, principal
- Direct mapping to Claude models (Claude Code supports only Opus and Sonnet)
- Junior and Senior tasks use Sonnet, Principal tasks use Opus
- No dynamic switching or escalation

### Error Handling
- Immediate restart on Claude crash
- Task lock prevents picking up different task
- Operator prompts for manual intervention when needed
- No exponential backoff - immediate retry

### Monitoring
- Terminal output only
- Clear status messages with timestamps
- Color coding for different message types
- Progress indicators for long operations

## Success Criteria

1. **Reliability**: Zero task loss on crashes
2. **Simplicity**: Single Python entry point
3. **Observability**: Clear terminal output
4. **Testability**: Full integration tests with real systems
5. **Performance**: Minimal overhead vs direct Claude execution

## Next Steps

1. Implement core components with TaskPersistence first
2. Add git worktree support
3. Integrate hook system
4. Build comprehensive integration tests
5. Document deployment and usage