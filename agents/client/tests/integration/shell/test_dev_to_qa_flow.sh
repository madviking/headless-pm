#!/bin/bash
# Test complete workflow from dev to QA

set -euo pipefail

# Source test helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

# Test configuration
TEST_FILE="test_workflow_output.txt"
TEST_CONTENT="Workflow test completed"

# Cleanup test file if exists
[[ -f "$TEST_FILE" ]] && rm -f "$TEST_FILE"

log_info "=== Test: Dev to QA Workflow ==="

# Create test agents
DEV_AGENT=$(create_test_agent "backend_dev" "test_dev_wf_${TEST_TIMESTAMP}" "junior")
QA_AGENT=$(create_test_agent "qa" "test_qa_wf_${TEST_TIMESTAMP}" "junior")

# Create test task for dev
TASK_ID=$(create_test_task \
    "Implement $TEST_FILE creation" \
    "Create a file named '$TEST_FILE' with the content: $TEST_CONTENT" \
    "junior" \
    "minor")

log_info "Running dev agent..."
# Run dev agent
if run_advanced_runner "backend_dev" "$DEV_AGENT" "--single-task" 60; then
    log_success "Dev agent completed"
else
    log_error "Dev agent failed"
    exit 1
fi

# Verify task moved to dev_done
if wait_for_task_status "$TASK_ID" "dev_done" 30; then
    log_success "Task moved to dev_done"
else
    log_error "Task not in dev_done status"
    exit 1
fi

# Verify file was created
if verify_file_created "$TEST_FILE" "$TEST_CONTENT"; then
    log_success "Dev created the file correctly"
else
    log_error "File not created by dev"
    exit 1
fi

log_info "Running QA agent..."
# Run QA agent
if run_advanced_runner "qa" "$QA_AGENT" "--single-task" 60; then
    log_success "QA agent completed"
else
    log_error "QA agent failed"
    exit 1
fi

# Verify task completed
if wait_for_task_status "$TASK_ID" "completed" 30; then
    log_success "Task marked as completed"
else
    log_error "Task not completed"
    exit 1
fi

# Cleanup test file
rm -f "$TEST_FILE"

log_success "=== Test PASSED: Dev to QA Workflow ==="