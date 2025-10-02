# Testing HeadlessPM MCP Integration with Claude Code

**Purpose**: Step-by-step guide to test HeadlessPM MCP integration with Claude Code
**Audience**: Developers, QA, contributors
**Prerequisites**: HeadlessPM installed, Claude Code CLI, byobu/tmux

---

## Overview

This guide demonstrates end-to-end testing of HeadlessPM's MCP (Model Context Protocol) integration, showing how Claude Code can:
1. Auto-connect to HeadlessPM via MCP
2. Register as an agent
3. Retrieve tasks from HeadlessPM database
4. Execute tasks autonomously

---

## Prerequisites

### Required Software

```bash
# 1. HeadlessPM (this project)
git clone https://github.com/madviking/headless-pm.git
cd headless-pm
./setup/universal_setup.sh

# 2. Claude Code CLI
# Download from: https://claude.ai/code

# 3. UV package manager (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 4. Byobu/tmux (for automated testing)
brew install byobu  # macOS
# or: apt install byobu  # Linux
```

### Environment Variables

Create `.env` in your test project:
```env
DATABASE_URL=sqlite:///headless-pm.db
API_KEY_HEADLESS_PM=XXXXXX
SERVICE_PORT=6969
HEADLESS_PM_AUTO_DASHBOARD=false
```

---

## Step 1: Verify MCP Server Works

### Test MCP Server Starts

```bash
cd /path/to/headless-pm
source venv/bin/activate  # or: . venv/bin/activate

# Test MCP server can start (will exit after connecting to API)
uv run python -m src.mcp

# Expected output:
# [MCP] Starting MCP server, connecting to API at http://localhost:6969
# [MCP] ✅ Connected to existing HeadlessPM API
# (or starts new API if none exists)
```

### Verify Dependencies

```bash
# Check all required packages installed
python -c "import fasteners, psutil, mcp; print('✅ All MCP dependencies present')"

# Check MCP version
pip show mcp | grep Version
# Expected: Version: 1.15.0

# Check protocol version
python -c "from mcp.types import LATEST_PROTOCOL_VERSION; print(f'Protocol: {LATEST_PROTOCOL_VERSION}')"
# Expected: Protocol: 2025-06-18
```

---

## Step 2: Configure Project for MCP

### Create .mcp.json

In your test project directory, create `.mcp.json`:

```json
{
  "mcpServers": {
    "headlesspm": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/headless-pm",
        "python",
        "-m",
        "src.mcp"
      ],
      "cwd": "/absolute/path/to/headless-pm",
      "env": {
        "HEADLESS_PM_BASE_URL": "http://localhost:6969",
        "UV_NO_CONFIG": "1"
      }
    }
  }
}
```

**Important**: Use absolute paths, not relative!

---

## Step 3: Create Test Task in HeadlessPM

### Initialize Database

```bash
cd /path/to/test-project
source /path/to/headless-pm/venv/bin/activate
export DATABASE_URL="sqlite:///$(pwd)/headless-pm.db"

# Initialize database
python -m src.cli.main init
```

### Create Task Structure via API

```bash
# Start HeadlessPM API (MCP will auto-start, but manual is clearer for testing)
# In one terminal:
export DATABASE_URL="sqlite:///$(pwd)/headless-pm.db"
python -m src.main

# In another terminal, create task:
curl -X POST http://localhost:6969/api/v1/register \
  -H "X-API-Key: XXXXXX" \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"pm1","role":"pm","level":"senior"}'

curl -X POST "http://localhost:6969/api/v1/epics?agent_id=pm1" \
  -H "X-API-Key: XXXXXX" \
  -H "Content-Type: application/json" \
  -d '{"name":"Calculator Library","description":"Python calculator"}'

# Note the epic ID from response, use it for feature:
curl -X POST "http://localhost:6969/api/v1/features?agent_id=pm1" \
  -H "X-API-Key: XXXXXX" \
  -H "Content-Type: application/json" \
  -d '{"epic_id":1,"name":"Add Function","description":"Implement add()"}'

# Create task:
curl -X POST "http://localhost:6969/api/v1/tasks/create?agent_id=pm1" \
  -H "X-API-Key: XXXXXX" \
  -H "Content-Type: application/json" \
  -d '{
    "feature_id":1,
    "title":"Implement add() calculator",
    "description":"Create math_utils/calculator.py with add(a,b) function, tests/test_calculator.py with pytest tests, update README.md",
    "target_role":"backend_dev",
    "difficulty":"junior",
    "complexity":"minor",
    "branch":"feat/calculator"
  }'
```

---

## Step 4: Test MCP with Claude Code

### Interactive Method

```bash
cd /path/to/test-project
claude --model claude-sonnet-4-5-20250929

# Claude starts, then type:
> Use HeadlessPM MCP to register as backend_dev, get the next task, and implement it.

# Claude will:
# 1. Call headlesspm - register_agent (MCP)
# 2. Call headlesspm - get_next_task (MCP)
# 3. Retrieve: "Task 1: Implement add() calculator"
# 4. Call headlesspm - lock_task (MCP)
# 5. Create files and implement
```

### Automated Method (via Byobu)

```bash
# Create detached byobu session with Claude
byobu new-session -d -s headless-pm-test \
  -c "/path/to/test-project" \
  "claude --model claude-sonnet-4-5-20250929"

# Wait for Claude to initialize
sleep 5

# Approve external imports (if prompted)
byobu send-keys -t headless-pm-test Enter

# Send instruction to Claude
sleep 2
byobu send-keys -t headless-pm-test -l \
  "Use HeadlessPM MCP to register as backend_dev, get next task, and implement it."
byobu send-keys -t headless-pm-test Enter

# Auto-approve MCP tool calls (option 2 = don't ask again)
sleep 5
byobu send-keys -t headless-pm-test "2"
byobu send-keys -t headless-pm-test Enter

# Monitor progress
sleep 10
byobu capture-pane -t headless-pm-test -p | tail -50

# Or attach to watch live:
byobu attach -t headless-pm-test
# Detach with: Ctrl+B, then D
```

---

## Step 5: Verify MCP Capabilities

### Check MCP Status in Claude

```bash
# Inside Claude Code session:
> /mcp

# Expected output:
╭────────────────────────────────────────────────────────────────────╮
│ Manage MCP servers                                                 │
│                                                                    │
│ ❯ 1. headlesspm            ✔ connected · Enter to view details     │
│                                                                    │
│ Capabilities: tools · resources                                    │
│ Tools: 12 tools                                                    │
╰────────────────────────────────────────────────────────────────────╯
```

**If you see**:
- ✅ `✔ connected` - MCP server connected
- ✅ `Capabilities: tools · resources` - Tools exposed
- ✅ `Tools: 12 tools` - All tools available
- ❌ `Capabilities: none` - MCP server broken (pre-v1.15 bug)

### View Available Tools

Press Enter on headlesspm server to see:
- register_agent
- get_project_context
- get_next_task
- create_task
- lock_task
- update_task_status
- create_document
- get_mentions
- register_service
- send_heartbeat
- poll_changes
- get_token_usage

---

## Step 6: Verify Task Execution

### Check Files Created

```bash
cd /path/to/test-project

# Claude should have created:
ls -la math_utils/calculator.py      # add() function
ls -la tests/test_calculator.py      # pytest tests
cat README.md                          # Updated docs
```

### Run Tests

```bash
# If Claude added pytest:
uv run pytest -v

# Expected:
# tests/test_calculator.py::test_add_positive PASSED
# tests/test_calculator.py::test_add_negative PASSED
# ...
```

### Check Task Status in HeadlessPM

```bash
curl -s "http://localhost:6969/api/v1/tasks/1" \
  -H "X-API-Key: XXXXXX" | python3 -m json.tool

# Check status field:
# "status": "dev_done"  ← Task completed by Claude
```

---

## Troubleshooting

### Issue: "Capabilities: none"

**Cause**: Using pre-v1.15 HeadlessPM or MCP bugs not fixed

**Fix**:
```bash
cd /path/to/headless-pm
git pull origin uv-integration-setup  # Get fixes
pip install --upgrade mcp             # Upgrade to v1.15.0
```

### Issue: "401 Unauthorized"

**Cause**: API key mismatch

**Fix**:
```bash
# Check .env has correct key
grep API_KEY .env

# Ensure it matches what API expects
```

### Issue: MCP server fails to start

**Cause**: Missing dependencies

**Fix**:
```bash
pip install fasteners psutil mcp requests
# Or with UV:
uv pip install fasteners psutil mcp requests
```

### Issue: "No tasks available"

**Cause**: No tasks in database or wrong role

**Solution**:
```bash
# Check tasks exist:
curl -s "http://localhost:6969/api/v1/tasks" \
  -H "X-API-Key: XXXXXX"

# Check target_role matches (backend_dev, frontend_dev, etc)
```

---

## Expected Results

### Successful MCP Integration Test

**Claude Code Output**:
```
⏺ headlesspm - register_agent (MCP)
  ⎿ Agent claude-backend-dev-1 registered as backend_dev (senior) ✅

⏺ headlesspm - get_next_task (MCP)
  ⎿ Task 1: Implement add() calculator ✅
     Complexity: minor
     Create math_utils/calculator.py with add(a,b) function...

⏺ headlesspm - lock_task (MCP)(task_id: 1)
  ⎿ Task 1 locked ✅

✻ Creating math_utils/calculator.py...
✻ Creating tests/test_calculator.py...
✻ Updating README.md...

⏺ headlesspm - update_task_status (MCP)(task_id: 1, status: "dev_done")
  ⎿ Task 1 status: dev_done ✅
```

**Files Created**:
- ✅ `math_utils/__init__.py`
- ✅ `math_utils/calculator.py` (with add function)
- ✅ `tests/__init__.py`
- ✅ `tests/test_calculator.py` (with pytest tests)
- ✅ `README.md` (updated with usage)

**Tests Pass**:
```bash
$ uv run pytest -v
===================== 5 passed in 0.02s =====================
```

---

## Cleanup

```bash
# Kill byobu session
byobu kill-session -t headless-pm-test

# Stop HeadlessPM API (if started manually)
pkill -f "python -m src.main"

# Or use specific PID
ps aux | grep "python -m src.main"
kill <PID>
```

---

## Running Tests Programmatically

### Quick MCP Test

```bash
cd /path/to/headless-pm

# Just MCP tests (fast)
python -m pytest tests/unit/test_mcp_server.py -v

# Expected: 25 passed
```

### Full Test Suite

**Note**: Some tests may hang due to known issues with coordination tests.

For reliable testing, use:
```bash
# Run non-MCP tests
python -m pytest tests/ -k "not mcp" --tb=short

# Run MCP unit tests separately
python -m pytest tests/unit/test_mcp_server.py -v
```

---

## MCP Integration Checklist

Before declaring MCP integration working, verify:

- [ ] MCP server starts without ModuleNotFoundError
- [ ] MCP shows `✔ connected` in Claude Code
- [ ] MCP shows `Capabilities: tools · resources` (not "none")
- [ ] MCP shows `Tools: 12 tools`
- [ ] register_agent works (agent registers successfully)
- [ ] get_next_task works (retrieves task from database)
- [ ] lock_task works (task locks)
- [ ] Claude can create files based on task
- [ ] update_task_status works (task marked complete)
- [ ] All 25 MCP unit tests pass

---

## Reference Information

### MCP SDK Details

- **GitHub**: https://github.com/modelcontextprotocol/python-sdk
- **SDK Version**: v1.15.0 (latest as of 2025-10-01)
- **Protocol Version**: 2025-06-18 (date-based versioning)
- **Protocol Spec**: https://modelcontextprotocol.io

### MCP Server Configuration

HeadlessPM MCP server configuration in `.mcp.json`:
- **Command**: `uv run python -m src.mcp`
- **Auto-start**: Yes (starts HeadlessPM API if not running)
- **Multi-client**: Yes (multiple Claude instances can share one API)
- **Reference counting**: API stays alive until last MCP client disconnects

### HeadlessPM API Endpoints Used by MCP

- `POST /api/v1/register` - Register agent
- `GET /api/v1/tasks/next` - Get next task
- `POST /api/v1/tasks/{id}/lock` - Lock task
- `PUT /api/v1/tasks/{id}/status` - Update status
- `GET /api/v1/context` - Get project context
- And more...

---

## Troubleshooting Test Hangs

If tests hang during MCP testing:

1. **Kill hanging processes**:
   ```bash
   pkill -f "python -m src.mcp"
   pkill -f "uvicorn.*6969"
   ```

2. **Clean coordination files**:
   ```bash
   rm -f /tmp/headless_pm_mcp_clients_*.json
   rm -f ~/.headless-pm/mcp_coordination.json
   ```

3. **Run tests with timeout**:
   ```bash
   timeout 60s python -m pytest tests/unit/test_mcp_server.py -v
   ```

---

## Success Criteria

✅ **MCP integration is working when**:

1. Claude Code shows MCP as connected with capabilities
2. Claude can register as agent via MCP
3. Claude retrieves actual task from HeadlessPM database
4. Claude locks task via MCP
5. Claude creates files matching task description
6. Claude updates task status via MCP
7. All MCP unit tests pass (25/25)

---

**End of Testing Guide**
