#!/bin/bash

# Setup script to install headless-pm client in another project
# Run this FROM the headless-pm repository to copy client to another project
# Usage: ./agents/client/setup_in_project.sh /path/to/your/other/project

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get target directory
TARGET_PROJECT="${1:-}"

if [[ -z "$TARGET_PROJECT" ]]; then
    echo "Usage: $0 /path/to/your/other/project"
    echo ""
    echo "Run this FROM the headless-pm repository to copy the client"
    echo "to another project. It will create:"
    echo "  your-other-project/headless_pm/"
    echo ""
    echo "Example:"
    echo "  cd /path/to/headless-pm"
    echo "  ./agents/client/setup_in_project.sh ~/dev/my-awesome-project"
    exit 1
fi

# Validate target
if [[ ! -d "$TARGET_PROJECT" ]]; then
    echo -e "${RED}Error: Target directory does not exist: $TARGET_PROJECT${NC}"
    exit 1
fi

# Get the source directory - this should be the agents/client directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR"  # We're already in agents/client

# Verify we're in the right place
if [[ ! -f "$SOURCE_DIR/headless_pm_client.py" ]]; then
    echo -e "${RED}Error: Cannot find headless_pm_client.py${NC}"
    echo "Make sure you're running this from the headless-pm repository"
    exit 1
fi

# Target directory will be headless_pm in the other project
TARGET_DIR="$TARGET_PROJECT/headless_pm"

# Check if already exists
if [[ -d "$TARGET_DIR" ]]; then
    echo -e "${YELLOW}Warning: $TARGET_DIR already exists${NC}"
    echo -n "Do you want to overwrite it? (y/N) "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 0
    fi
    rm -rf "$TARGET_DIR"
fi

echo -e "${BLUE}🔧 Setting up headless-pm client in your project...${NC}"

# Copy the entire client directory
echo "Copying client files..."
cp -r "$SOURCE_DIR" "$TARGET_DIR"

# Make scripts executable
echo "Setting permissions..."
chmod +x "$TARGET_DIR/headless_pm_client.py"
chmod +x "$TARGET_DIR/runners/agent_runner.sh"
chmod +x "$TARGET_DIR/runners/install.sh"

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "The headless-pm client has been installed to:"
echo "  $TARGET_DIR"
echo ""
echo "Next steps:"
echo ""
echo "1. Install the agent runner globally (optional):"
echo "   cd $TARGET_PROJECT"
echo "   ./headless_pm/runners/install.sh"
echo ""
echo "2. Run agents from your project:"
echo "   cd $TARGET_PROJECT"
echo "   ./headless_pm/runners/agent_runner.sh backend_dev dev_001"
echo ""
echo "3. Or if globally installed:"
echo "   headless-agent backend_dev dev_001"
echo ""
echo "The client will automatically find:"
echo "  - headless_pm_client.py at: $TARGET_DIR/headless_pm_client.py"
echo "  - team_roles at: $TARGET_DIR/team_roles/"
echo ""
echo -e "${YELLOW}⚠️  Remember to review the security implications before using --dangerously-skip-permissions${NC}"