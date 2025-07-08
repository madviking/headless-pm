#!/bin/bash
# Setup test environment for integration tests

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Setting up test environment ===${NC}"

# Check for required environment variables
if [[ -z "${HEADLESS_PM_API_KEY:-}" ]] && [[ -z "${API_KEY:-}" ]]; then
    echo -e "${RED}Error: No API key found${NC}"
    echo "Set one of: HEADLESS_PM_API_KEY, API_KEY"
    exit 1
fi

# Check if PM API is accessible
API_URL="${HEADLESS_PM_API_URL:-http://localhost:6969}"
echo -e "${YELLOW}Checking PM API at: $API_URL${NC}"

if curl -s -f "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PM API is accessible${NC}"
else
    echo -e "${RED}✗ PM API is not accessible at $API_URL${NC}"
    echo "Please ensure the Headless PM server is running"
    exit 1
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
fi

# Check for Claude CLI
if command -v claude &> /dev/null; then
    echo -e "${GREEN}✓ Claude CLI found${NC}"
else
    echo -e "${YELLOW}⚠ Claude CLI not found in PATH${NC}"
    echo "The advanced runner will try to find it in common locations"
fi

# Check for required Python packages
echo -e "${YELLOW}Checking Python dependencies...${NC}"
MISSING_PACKAGES=()

if ! python3 -c "import psutil" 2>/dev/null; then
    MISSING_PACKAGES+=("psutil")
fi

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo -e "${YELLOW}Missing packages: ${MISSING_PACKAGES[*]}${NC}"
    echo "Install with: pip install ${MISSING_PACKAGES[*]}"
else
    echo -e "${GREEN}✓ All Python dependencies satisfied${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}Creating test directories...${NC}"
mkdir -p "$HOME/.headless-pm/locks"
mkdir -p "$HOME/.headless-pm/logs"

# Check git repository
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${GREEN}✓ In git repository${NC}"
    
    # Check for uncommitted changes
    if [[ -n $(git status --porcelain) ]]; then
        echo -e "${YELLOW}⚠ Warning: Repository has uncommitted changes${NC}"
    fi
else
    echo -e "${RED}✗ Not in a git repository${NC}"
    echo "Git worktree features will not work"
fi

# Make test scripts executable
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR"/*.sh

echo -e "${GREEN}=== Test environment ready ===${NC}"
echo ""
echo "You can now run tests with:"
echo "  ./run_all_tests.sh     # Run all tests"
echo "  ./test_single_task.sh  # Run individual test"