#!/bin/bash
# Run all integration tests

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
FAILED_TEST_NAMES=()

# Header
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}    Advanced Agent Runner - Integration Test Suite${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# First run setup
echo -e "${BLUE}Running test environment setup...${NC}"
if "$SCRIPT_DIR/setup_test_env.sh"; then
    echo ""
else
    echo -e "${RED}Setup failed, cannot continue${NC}"
    exit 1
fi

# Function to run a test
run_test() {
    local test_script="$1"
    local test_name=$(basename "$test_script" .sh)
    
    ((TOTAL_TESTS++))
    
    echo -e "${YELLOW}Running: $test_name${NC}"
    echo -e "${YELLOW}────────────────────────────────────────${NC}"
    
    if bash "$test_script"; then
        ((PASSED_TESTS++))
        echo -e "${GREEN}✓ PASSED: $test_name${NC}"
    else
        ((FAILED_TESTS++))
        FAILED_TEST_NAMES+=("$test_name")
        echo -e "${RED}✗ FAILED: $test_name${NC}"
    fi
    
    echo ""
}

# Run all test scripts
for test_script in "$SCRIPT_DIR"/test_*.sh; do
    if [[ -f "$test_script" && -x "$test_script" ]]; then
        run_test "$test_script"
    fi
done

# Summary
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}                    Test Summary${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "Total tests:  ${TOTAL_TESTS}"
echo -e "Passed:       ${GREEN}${PASSED_TESTS}${NC}"
echo -e "Failed:       ${RED}${FAILED_TESTS}${NC}"
echo ""

if [[ ${FAILED_TESTS} -eq 0 ]]; then
    echo -e "${GREEN}All tests passed! 🎉${NC}"
    exit 0
else
    echo -e "${RED}Failed tests:${NC}"
    for test_name in "${FAILED_TEST_NAMES[@]}"; do
        echo -e "  - $test_name"
    done
    exit 1
fi