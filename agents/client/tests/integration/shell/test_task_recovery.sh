#!/bin/bash
# Test task recovery after simulated crash

set -euo pipefail

# Source test helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

# Test configuration
AGENT_ID="test_recovery_${TEST_TIMESTAMP}"
LOCK_DIR="$HOME/.headless-pm/locks"
LOCK_FILE="$LOCK_DIR/agent-${AGENT_ID}.lock"

log_info "=== Test: Task Recovery After Crash ==="

# Create test agent
create_test_agent "backend_dev" "$AGENT_ID" "junior" > /dev/null

# Create test task
TASK_ID=$(create_test_task \
    "Recovery test task" \
    "This task will test crash recovery" \
    "junior" \
    "minor")

log_info "Simulating task lock..."
# Create lock file manually (simulating crash during task)
mkdir -p "$LOCK_DIR"
cat > "$LOCK_FILE" <<EOF
{
  "task_id": $TASK_ID,
  "task_title": "Recovery test task",
  "agent_id": "$AGENT_ID",
  "locked_at": "$(date -u +"%Y-%m-%dT%H:%M:%S")",
  "worktree_path": null,
  "branch_name": null,
  "task_data": {
    "id": $TASK_ID,
    "title": "Recovery test task",
    "status": "created",
    "skill_level": "junior"
  }
}
EOF

log_success "Lock file created"

# Verify lock file exists
if [[ -f "$LOCK_FILE" ]]; then
    log_success "Lock file verified: $LOCK_FILE"
else
    log_error "Lock file not found"
    exit 1
fi

log_info "Starting runner to test recovery..."
# Run the runner - it should recover the locked task
if timeout 30 python3 "$RUNNER_PATH" \
    --role "backend_dev" \
    --agent-id "$AGENT_ID" \
    --single-task 2>&1 | grep -q "Recovering previously locked task"; then
    
    log_success "Runner detected and recovered locked task"
else
    log_error "Runner did not recover locked task"
    exit 1
fi

# Verify lock file was cleaned up
if [[ ! -f "$LOCK_FILE" ]]; then
    log_success "Lock file cleaned up after completion"
else
    log_error "Lock file still exists"
    exit 1
fi

log_success "=== Test PASSED: Task Recovery ==="