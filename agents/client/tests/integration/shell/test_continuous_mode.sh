#!/bin/bash
# Test continuous mode operation

set -euo pipefail

# Source test helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

log_info "=== Test: Continuous Mode Operation ==="

# Create test agent
AGENT_ID=$(create_test_agent "backend_dev" "test_continuous_${TEST_TIMESTAMP}" "junior")

log_info "Starting runner in continuous mode..."
# Start runner in background
python3 "$RUNNER_PATH" \
    --role "backend_dev" \
    --agent-id "$AGENT_ID" &

RUNNER_PID=$!
log_info "Runner started with PID: $RUNNER_PID"

# Let it run for a few seconds
sleep 5

# Check if process is still running
if kill -0 $RUNNER_PID 2>/dev/null; then
    log_success "Runner is running in continuous mode"
else
    log_error "Runner exited unexpectedly"
    exit 1
fi

# Send SIGTERM to test graceful shutdown
log_info "Sending SIGTERM for graceful shutdown..."
kill -TERM $RUNNER_PID

# Wait for process to exit (max 10 seconds)
WAIT_COUNT=0
while kill -0 $RUNNER_PID 2>/dev/null && [ $WAIT_COUNT -lt 10 ]; do
    sleep 1
    ((WAIT_COUNT++))
done

if ! kill -0 $RUNNER_PID 2>/dev/null; then
    log_success "Runner shut down gracefully"
else
    log_error "Runner did not shut down gracefully, forcing..."
    kill -9 $RUNNER_PID
    exit 1
fi

log_success "=== Test PASSED: Continuous Mode ==="