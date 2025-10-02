#!/bin/bash
# HeadlessPM Seamless Installation E2E Test Script
# Tests the complete user experience from UV installation to working API

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TEST_LOG=""

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    TEST_LOG="${TEST_LOG}[INFO] $1\n"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    TEST_LOG="${TEST_LOG}[PASS] $1\n"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    TEST_LOG="${TEST_LOG}[FAIL] $1\n"
    ((TESTS_FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    TEST_LOG="${TEST_LOG}[WARN] $1\n"
}

# Test functions
test_uv_available() {
    log_info "Testing UV availability..."
    if command -v uv >/dev/null 2>&1; then
        local uv_version=$(uv --version)
        log_success "UV is available: $uv_version"
        return 0
    else
        log_error "UV is not installed. Please install UV first: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi
}

test_seamless_installation() {
    log_info "Testing seamless UV installation..."
    
    # Create clean test environment
    local test_dir="/tmp/headlesspm-e2e-test-$(date +%s)"
    mkdir -p "$test_dir"
    cd "$test_dir"
    
    # Test UV virtual environment creation
    log_info "Creating UV virtual environment..."
    if uv venv test-env; then
        log_success "UV virtual environment created"
    else
        log_error "Failed to create UV virtual environment"
        return 1
    fi
    
    # Activate environment
    source test-env/bin/activate
    
    # Test installation from local path
    log_info "Installing HeadlessPM via UV from local repository..."
    local repo_path="$1"  # Passed as parameter
    if uv pip install "file://$repo_path"; then
        log_success "HeadlessPM installed successfully via UV"
    else
        log_error "Failed to install HeadlessPM via UV"
        return 1
    fi
    
    # Test entry points are available
    test_entry_points "$test_dir"
    
    # Clean up
    cd /
    rm -rf "$test_dir"
    
    return 0
}

test_entry_points() {
    local test_dir="$1"
    
    log_info "Testing entry point availability..."
    
    # Test headless-pm command exists
    if which headless-pm >/dev/null 2>&1; then
        log_success "headless-pm entry point available"
    else
        log_error "headless-pm entry point not found"
        return 1
    fi
    
    # Test headless-pm-cli command exists
    if which headless-pm-cli >/dev/null 2>&1; then
        log_success "headless-pm-cli entry point available"
    else
        log_error "headless-pm-cli entry point not found"
        return 1
    fi
    
    # Test CLI help works
    log_info "Testing CLI help functionality..."
    if headless-pm-cli --help >/dev/null 2>&1; then
        log_success "CLI help works correctly"
    else
        log_error "CLI help failed"
        return 1
    fi
    
    return 0
}

test_auto_setup_functionality() {
    log_info "Testing auto-setup functionality..."
    
    # Create clean directory with env-example
    local test_dir="/tmp/headlesspm-autosetup-$(date +%s)"
    mkdir -p "$test_dir"
    cd "$test_dir"
    
    # Copy env-example (required for auto-setup)
    local repo_path="$1"
    cp "$repo_path/env-example" .
    
    # Activate UV environment from previous test
    source /tmp/headlesspm-e2e-test-*/test-env/bin/activate 2>/dev/null || {
        # Create new environment if needed
        uv venv test-env
        source test-env/bin/activate
        uv pip install "file://$repo_path"
    }
    
    log_info "Testing first-run auto-setup..."
    
    # Run headless-pm in background with timeout
    timeout 10s headless-pm >/dev/null 2>&1 &
    local headless_pid=$!
    sleep 3
    
    # Kill the process
    kill $headless_pid 2>/dev/null || true
    wait $headless_pid 2>/dev/null || true
    
    # Check if auto-setup worked
    if [[ -f ".env" ]]; then
        log_success "Auto-setup created .env file"
    else
        log_error "Auto-setup failed to create .env file"
        cd /
        rm -rf "$test_dir"
        return 1
    fi
    
    if [[ -f "headless_pm.db" || -f "headless-pm.db" ]]; then
        log_success "Auto-setup created database"
    else
        log_error "Auto-setup failed to create database"
        cd /
        rm -rf "$test_dir"
        return 1
    fi
    
    # Clean up
    cd /
    rm -rf "$test_dir"
    
    return 0
}

test_api_functionality() {
    log_info "Testing API functionality..."
    
    # Create clean test environment
    local test_dir="/tmp/headlesspm-api-test-$(date +%s)"
    mkdir -p "$test_dir"
    cd "$test_dir"
    
    # Copy env-example
    local repo_path="$1"
    cp "$repo_path/env-example" .
    
    # Create UV environment and install
    uv venv test-env
    source test-env/bin/activate
    uv pip install "file://$repo_path"
    
    log_info "Starting HeadlessPM API server..."
    
    # Start server in background
    headless-pm &
    local server_pid=$!
    
    # Wait for server to start
    sleep 5
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    local health_response
    if health_response=$(curl -s "http://localhost:6969/health" 2>/dev/null); then
        # Check if response contains expected fields
        if echo "$health_response" | grep -q '"status"' && echo "$health_response" | grep -q '"service"'; then
            log_success "Health endpoint returned valid response"
        else
            log_error "Health endpoint returned invalid response: $health_response"
        fi
    else
        log_error "Failed to reach health endpoint"
    fi
    
    # Test root endpoint
    log_info "Testing root endpoint..."
    local root_response
    if root_response=$(curl -s "http://localhost:6969/" 2>/dev/null); then
        if echo "$root_response" | grep -q '"message"' && echo "$root_response" | grep -q '"docs"'; then
            log_success "Root endpoint returned valid response"
        else
            log_error "Root endpoint returned invalid response: $root_response"
        fi
    else
        log_error "Failed to reach root endpoint"
    fi
    
    # Clean up
    kill $server_pid 2>/dev/null || true
    wait $server_pid 2>/dev/null || true
    cd /
    rm -rf "$test_dir"
    
    return 0
}

test_pypi_readiness() {
    log_info "Testing PyPI readiness..."
    
    # Create test environment
    local test_dir="/tmp/headlesspm-build-test-$(date +%s)"
    mkdir -p "$test_dir"
    cd "$test_dir"
    
    # Copy repository files
    local repo_path="$1"
    cp -r "$repo_path"/* .
    
    log_info "Testing UV build process..."
    
    # Test UV build
    if uv build; then
        log_success "UV build completed successfully"
        
        # Check if distributions were created
        if [[ -d "dist" ]]; then
            local wheel_count=$(ls dist/*.whl 2>/dev/null | wc -l)
            local source_count=$(ls dist/*.tar.gz 2>/dev/null | wc -l)
            
            if [[ $wheel_count -gt 0 && $source_count -gt 0 ]]; then
                log_success "Created wheel and source distributions"
                
                # Show file sizes
                local wheel_file=$(ls dist/*.whl 2>/dev/null | head -1)
                local source_file=$(ls dist/*.tar.gz 2>/dev/null | head -1)
                
                if [[ -f "$wheel_file" ]]; then
                    local wheel_size=$(stat -f%z "$wheel_file" 2>/dev/null || stat -c%s "$wheel_file" 2>/dev/null)
                    log_success "Wheel created: $(basename $wheel_file) (${wheel_size} bytes)"
                fi
                
                if [[ -f "$source_file" ]]; then
                    local source_size=$(stat -f%z "$source_file" 2>/dev/null || stat -c%s "$source_file" 2>/dev/null)
                    log_success "Source dist created: $(basename $source_file) (${source_size} bytes)"
                fi
            else
                log_error "Missing wheel or source distribution files"
            fi
        else
            log_error "No dist directory created"
        fi
    else
        log_error "UV build failed"
        cd /
        rm -rf "$test_dir"
        return 1
    fi
    
    # Clean up
    cd /
    rm -rf "$test_dir"
    
    return 0
}

# Main test execution
main() {
    echo -e "${BLUE}====================================${NC}"
    echo -e "${BLUE}HeadlessPM Seamless Installation Test${NC}"
    echo -e "${BLUE}====================================${NC}"
    echo ""
    
    # Get repository path
    local repo_path="${1:-$(pwd)}"
    if [[ ! -f "$repo_path/pyproject.toml" ]]; then
        log_error "Repository path not found or invalid: $repo_path"
        log_error "Usage: $0 [path/to/headless-pm]"
        exit 1
    fi
    
    log_info "Testing repository: $repo_path"
    echo ""
    
    # Run all tests
    test_uv_available || exit 1
    test_seamless_installation "$repo_path"
    test_auto_setup_functionality "$repo_path"
    test_api_functionality "$repo_path"
    test_pypi_readiness "$repo_path"
    
    echo ""
    echo -e "${BLUE}====================================${NC}"
    echo -e "${BLUE}Test Results Summary${NC}"
    echo -e "${BLUE}====================================${NC}"
    
    echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
        echo ""
        echo -e "${RED}❌ E2E TEST SUITE FAILED${NC}"
        echo -e "${YELLOW}Some tests failed. Check the output above for details.${NC}"
        exit 1
    else
        echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
        echo ""
        echo -e "${GREEN}✅ E2E TEST SUITE PASSED${NC}"
        echo -e "${GREEN}HeadlessPM seamless installation is working perfectly!${NC}"
        echo ""
        echo -e "${BLUE}Installation command for users:${NC}"
        echo -e "${YELLOW}uv pip install https://github.com/madviking/headless-pm${NC}"
        echo -e "${YELLOW}headless-pm${NC}"
    fi
}

# Run main function with all arguments
main "$@"