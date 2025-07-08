#!/bin/bash
# Test single task execution

set -euo pipefail

# Source test helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

# Test configuration
TEST_FILE="test_single_task_output.txt"
TEST_CONTENT="Single task test completed successfully"

# Cleanup test file if exists
[[ -f "$TEST_FILE" ]] && rm -f "$TEST_FILE"

log_info "=== Test: Single Task Execution ==="

# Create test agent
AGENT_ID=$(create_test_agent "backend_dev" "test_single_${TEST_TIMESTAMP}" "junior")

# Create test task
TASK_ID=$(create_test_task \
    "Create $TEST_FILE" \
    "Create a file named '$TEST_FILE' with the content: $TEST_CONTENT" \
    "junior" \
    "minor")

# Run the advanced runner in single-task mode
if run_advanced_runner "backend_dev" "$AGENT_ID" "--single-task" 60; then
    log_success "Runner completed successfully"
else
    log_error "Runner failed"
    exit 1
fi

# Verify task status changed to dev_done
if wait_for_task_status "$TASK_ID" "dev_done" 30; then
    log_success "Task status updated correctly"
else
    log_error "Task status not updated"
    exit 1
fi

# Verify file was created
if verify_file_created "$TEST_FILE" "$TEST_CONTENT"; then
    log_success "Output file created with correct content"
else
    log_error "Output file not created correctly"
    exit 1
fi

# Cleanup test file
rm -f "$TEST_FILE"

log_success "=== Test PASSED: Single Task Execution ==="