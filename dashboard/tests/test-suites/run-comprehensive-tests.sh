#!/bin/bash

# Comprehensive Dashboard Test Runner
# This script runs the complete test suite for the dashboard

set -e

echo "🚀 Starting Comprehensive Dashboard Tests"
echo "=========================================="

# Configuration
DASHBOARD_URL="${DASHBOARD_URL:-http://localhost:3000}"
API_URL="${API_URL:-http://localhost:6969}"
TEST_FILE="tests/test-suites/comprehensive-final-dashboard-test.spec.ts"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the dashboard directory
if [ ! -f "package.json" ]; then
    print_error "Please run this script from the dashboard directory"
    exit 1
fi

# Check if Playwright is installed
if ! npx playwright --version > /dev/null 2>&1; then
    print_warning "Playwright not found. Installing..."
    npm install --save-dev @playwright/test
    npx playwright install
fi

# Check if API is running
print_status "Checking API availability at $API_URL..."
if curl -s "$API_URL/health" > /dev/null 2>&1; then
    print_success "API is accessible"
else
    print_warning "API not accessible at $API_URL. Some tests may fail."
fi

# Check if dashboard is running
print_status "Checking dashboard availability at $DASHBOARD_URL..."
if curl -s "$DASHBOARD_URL" > /dev/null 2>&1; then
    print_success "Dashboard is accessible"
else
    print_error "Dashboard not accessible at $DASHBOARD_URL"
    print_status "Starting dashboard server..."
    
    # Try to start the dashboard
    if [ -f "package.json" ]; then
        npm run dev &
        DASHBOARD_PID=$!
        print_status "Started dashboard server (PID: $DASHBOARD_PID)"
        
        # Wait for server to start
        print_status "Waiting for dashboard to start..."
        for i in {1..30}; do
            if curl -s "$DASHBOARD_URL" > /dev/null 2>&1; then
                print_success "Dashboard is now accessible"
                break
            fi
            sleep 2
        done
        
        # Check if it's actually running
        if ! curl -s "$DASHBOARD_URL" > /dev/null 2>&1; then
            print_error "Failed to start dashboard"
            exit 1
        fi
    else
        print_error "No package.json found. Cannot start dashboard."
        exit 1
    fi
fi

# Set environment variables for tests
export DASHBOARD_URL="$DASHBOARD_URL"
export API_URL="$API_URL"

print_status "Running comprehensive test suite..."
print_status "Dashboard URL: $DASHBOARD_URL"
print_status "API URL: $API_URL"
print_status "Test file: $TEST_FILE"

echo ""
echo "=========================================="
echo "🧪 Test Execution Starting..."
echo "=========================================="

# Run the tests with different configurations
echo ""
print_status "Running tests in headless mode..."

# Main test run
if npx playwright test "$TEST_FILE" --reporter=html --reporter=line; then
    print_success "All tests passed!"
    TEST_RESULT=0
else
    print_error "Some tests failed!"
    TEST_RESULT=1
fi

# Generate test report
print_status "Generating test report..."
if [ -f "playwright-report/index.html" ]; then
    print_success "Test report generated at: playwright-report/index.html"
    print_status "To view the report, run: npx playwright show-report"
fi

# Take screenshots on failure
if [ $TEST_RESULT -ne 0 ]; then
    print_status "Taking debug screenshots..."
    npx playwright test "$TEST_FILE" --headed --project=chromium --max-failures=1 --reporter=line || true
fi

# Cleanup
if [ ! -z "$DASHBOARD_PID" ]; then
    print_status "Stopping dashboard server (PID: $DASHBOARD_PID)..."
    kill $DASHBOARD_PID > /dev/null 2>&1 || true
fi

echo ""
echo "=========================================="
echo "📊 Test Summary"
echo "=========================================="

if [ $TEST_RESULT -eq 0 ]; then
    print_success "✅ All tests completed successfully!"
    print_success "🎉 Dashboard is fully functional and tested!"
else
    print_error "❌ Some tests failed. Check the report for details."
    print_status "Run 'npx playwright show-report' to view detailed results"
fi

echo ""
print_status "Test execution completed."

exit $TEST_RESULT