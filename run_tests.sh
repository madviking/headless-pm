#!/bin/bash
# Universal test runner that uses the correct venv for the platform

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Running Tests${NC}"
echo "================="

# Detect architecture
ARCH=$(uname -m)
echo -e "${BLUE}Detected architecture: $ARCH${NC}"

# Determine which venv to use
if [[ "$ARCH" == "arm64" ]]; then
    VENV_NAME="venv"
else
    VENV_NAME="claude_venv"
fi

# Check if the venv exists
if [ ! -d "$VENV_NAME" ]; then
    echo -e "${YELLOW}Virtual environment $VENV_NAME not found!${NC}"
    echo "Please run ./setup/universal_setup.sh first"
    exit 1
fi

# Activate the appropriate venv
echo -e "${BLUE}Using virtual environment: $VENV_NAME${NC}"
source $VENV_NAME/bin/activate

# Run tests
echo -e "${BLUE}Running pytest...${NC}"
python -m pytest tests/ -v "$@"

echo -e "${GREEN}✅ Tests completed${NC}"