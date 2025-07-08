#!/bin/bash
# Test helper functions for integration tests

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test configuration
export TEST_API_URL="${HEADLESS_PM_API_URL:-http://localhost:6969}"
export TEST_API_KEY="${HEADLESS_PM_API_KEY:-${API_KEY:-}}"
export TEST_TIMESTAMP=$(date +%s)

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../../../.." && pwd)"
CLIENT_PATH="$PROJECT_ROOT/headless_pm_client.py"
RUNNER_PATH="$PROJECT_ROOT/agents/client/advanced_runner/advanced_agent_runner.py"

# Test data tracking
TEST_AGENTS=()
TEST_TASKS=()
TEST_EPICS=()
TEST_FEATURES=()

# Helper functions
log_info() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# API wrapper using headless_pm_client.py
pm_client() {
    python3 "$CLIENT_PATH" "$@"
}

# Create test agent
create_test_agent() {
    local role="${1:-backend_dev}"
    local agent_id="${2:-test_${role}_${TEST_TIMESTAMP}}"
    local skill_level="${3:-junior}"
    
    log_info "Creating test agent: $agent_id"
    
    if pm_client register \
        --agent-id "$agent_id" \
        --role "$role" \
        --skill-level "$skill_level" > /dev/null; then
        
        TEST_AGENTS+=("$agent_id")
        log_success "Created agent: $agent_id"
        echo "$agent_id"
        return 0
    else
        log_error "Failed to create agent: $agent_id"
        return 1
    fi
}

# Create test task
create_test_task() {
    local title="${1:-Test Task $TEST_TIMESTAMP}"
    local description="${2:-Create test_output.txt with 'Test completed'}"
    local skill_level="${3:-junior}"
    local complexity="${4:-minor}"
    
    log_info "Creating test task: $title"
    
    # First create epic and feature
    local epic_response=$(pm_client epics create \
        --name "Test Epic $TEST_TIMESTAMP" \
        --description "Integration test epic" 2>/dev/null)
    
    local epic_id=$(echo "$epic_response" | grep -oP '"id":\s*\K\d+' | head -1)
    TEST_EPICS+=("$epic_id")
    
    local feature_response=$(pm_client features create \
        --epic-id "$epic_id" \
        --name "Test Feature $TEST_TIMESTAMP" \
        --description "Integration test feature" 2>/dev/null)
    
    local feature_id=$(echo "$feature_response" | grep -oP '"id":\s*\K\d+' | head -1)
    TEST_FEATURES+=("$feature_id")
    
    # Create task
    local task_response=$(pm_client tasks create \
        --feature-id "$feature_id" \
        --title "$title" \
        --description "$description" \
        --skill-level "$skill_level" \
        --complexity "$complexity" 2>/dev/null)
    
    local task_id=$(echo "$task_response" | grep -oP '"id":\s*\K\d+' | head -1)
    
    if [[ -n "$task_id" ]]; then
        TEST_TASKS+=("$task_id")
        log_success "Created task: $task_id - $title"
        echo "$task_id"
        return 0
    else
        log_error "Failed to create task"
        return 1
    fi
}

# Get task status
get_task_status() {
    local task_id="$1"
    
    local response=$(pm_client tasks get "$task_id" 2>/dev/null)
    echo "$response" | grep -oP '"status":\s*"\K[^"]+' | head -1
}

# Wait for task status
wait_for_task_status() {
    local task_id="$1"
    local expected_status="$2"
    local timeout="${3:-60}"
    
    log_info "Waiting for task $task_id to reach status: $expected_status"
    
    local start_time=$(date +%s)
    while true; do
        local current_status=$(get_task_status "$task_id")
        
        if [[ "$current_status" == "$expected_status" ]]; then
            log_success "Task reached status: $expected_status"
            return 0
        fi
        
        local elapsed=$(($(date +%s) - start_time))
        if [[ $elapsed -gt $timeout ]]; then
            log_error "Timeout waiting for status. Current: $current_status"
            return 1
        fi
        
        sleep 2
    done
}

# Run advanced runner
run_advanced_runner() {
    local role="$1"
    local agent_id="$2"
    local mode="${3:---single-task}"
    local timeout="${4:-30}"
    
    log_info "Running advanced runner: $role/$agent_id $mode"
    
    timeout "$timeout" python3 "$RUNNER_PATH" \
        --role "$role" \
        --agent-id "$agent_id" \
        $mode || {
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            log_info "Runner timed out (expected for continuous mode)"
            return 0
        else
            log_error "Runner failed with exit code: $exit_code"
            return $exit_code
        fi
    }
}

# Cleanup test data
cleanup_test_data() {
    log_info "Cleaning up test data..."
    
    # Delete tasks
    for task_id in "${TEST_TASKS[@]}"; do
        pm_client tasks delete "$task_id" 2>/dev/null || true
    done
    
    # Delete features
    for feature_id in "${TEST_FEATURES[@]}"; do
        pm_client features delete "$feature_id" 2>/dev/null || true
    done
    
    # Delete epics
    for epic_id in "${TEST_EPICS[@]}"; do
        pm_client epics delete "$epic_id" 2>/dev/null || true
    done
    
    # Delete agents
    for agent_id in "${TEST_AGENTS[@]}"; do
        pm_client agents delete "$agent_id" 2>/dev/null || true
    done
    
    log_success "Cleanup completed"
}

# Verify file created
verify_file_created() {
    local filepath="$1"
    local expected_content="${2:-}"
    
    if [[ ! -f "$filepath" ]]; then
        log_error "File not found: $filepath"
        return 1
    fi
    
    if [[ -n "$expected_content" ]]; then
        local actual_content=$(cat "$filepath")
        if [[ "$actual_content" == *"$expected_content"* ]]; then
            log_success "File contains expected content"
            return 0
        else
            log_error "File content mismatch. Expected: $expected_content, Got: $actual_content"
            return 1
        fi
    else
        log_success "File exists: $filepath"
        return 0
    fi
}

# Setup trap for cleanup
trap cleanup_test_data EXIT