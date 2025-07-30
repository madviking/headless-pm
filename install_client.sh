#!/bin/bash

# Headless PM Client Installation Script
# Interactive installer for setting up Headless PM client tools

set -e  # Exit on any error

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory (now at root of headless-pm)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HEADLESS_PM_ROOT="$SCRIPT_DIR"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Headless PM Client Installer${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Function to prompt yes/no questions
prompt_yes_no() {
    local prompt="$1"
    local default="$2"
    local response
    
    if [ "$default" = "y" ]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi
    
    read -p "$prompt" response
    response=${response:-$default}
    
    case "$response" in
        [yY][eE][sS]|[yY]) 
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Function to validate directory path
validate_directory() {
    local dir="$1"
    if [ -z "$dir" ]; then
        return 1
    fi
    
    # Expand tilde
    dir="${dir/#\~/$HOME}"
    
    # Create directory if it doesn't exist
    if [ ! -d "$dir" ]; then
        if prompt_yes_no "Directory $dir doesn't exist. Create it?" "y"; then
            mkdir -p "$dir"
        else
            return 1
        fi
    fi
    
    # Return expanded path
    echo "$dir"
}

# 1. Ask for project path
echo -e "${YELLOW}Step 1: Project Path Configuration${NC}"
echo "Where do you want to install the Headless PM client tools?"
echo "This should be your project directory where you'll be working."
read -p "Project path (default: current directory): " PROJECT_PATH

if [ -z "$PROJECT_PATH" ]; then
    PROJECT_PATH="$(pwd)"
fi

PROJECT_PATH=$(validate_directory "$PROJECT_PATH")
if [ $? -ne 0 ]; then
    echo -e "${RED}Invalid project path. Exiting.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Using project path: $PROJECT_PATH${NC}"
echo ""

# Check Python version
echo -e "${BLUE}Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python is not installed. Please install Python 3.11 or higher.${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo -e "${RED}Error: Python 3.11+ is required. Found Python $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"
echo ""

# 2. Ask about auto-commit
echo -e "${YELLOW}Step 2: Auto-commit Configuration${NC}"
ENABLE_AUTOCOMMIT=false
if prompt_yes_no "Do you want to enable git auto-commit on exit?" "n"; then
    ENABLE_AUTOCOMMIT=true
    echo -e "${GREEN}✓ Auto-commit will be enabled${NC}"
    echo -e "${YELLOW}  Note: This will commit and push all changes when Claude Code exits${NC}"
else
    echo -e "${YELLOW}✓ Auto-commit will be disabled${NC}"
fi
echo ""

# 3. Ask about MCP client
echo -e "${YELLOW}Step 3: MCP Client Configuration${NC}"
echo "MCP (Model Context Protocol) provides a natural language interface for Claude Code."
ENABLE_MCP=false
if prompt_yes_no "Do you want to install the MCP client?" "y"; then
    ENABLE_MCP=true
    echo -e "${GREEN}✓ MCP client will be installed${NC}"
else
    echo -e "${YELLOW}✓ MCP client will be skipped${NC}"
fi
echo ""

# 4. Ask for API key
echo -e "${YELLOW}Step 4: API Key Configuration${NC}"
echo "The Headless PM API key is required for client authentication."
read -p "Enter your Headless PM API key: " API_KEY

if [ -z "$API_KEY" ]; then
    echo -e "${YELLOW}⚠ No API key provided. You'll need to configure it manually later.${NC}"
else
    echo -e "${GREEN}✓ API key configured${NC}"
fi
echo ""

# Create directories
echo -e "${BLUE}Creating project structure...${NC}"
mkdir -p "$PROJECT_PATH/headless_pm"

# Copy client files
echo -e "${BLUE}Installing client files...${NC}"

# Copy entire agents/client directory contents to headless_pm
cp -r "$SCRIPT_DIR/agents/client/"* "$PROJECT_PATH/headless_pm/"

# Make Python client executable
chmod +x "$PROJECT_PATH/headless_pm/headless_pm_client.py"

# Create virtual environment for headless_pm
echo -e "${BLUE}Creating isolated Python environment...${NC}"
cd "$PROJECT_PATH/headless_pm"
$PYTHON_CMD -m venv .venv

# Activate the virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    # Windows support
    source .venv/Scripts/activate
fi

# Install required dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install requests python-dotenv typer rich > /dev/null 2>&1

# Deactivate for now
deactivate
cd - > /dev/null

echo -e "${GREEN}✓ Python environment created${NC}"

# Create wrapper script that uses the venv
cat > "$PROJECT_PATH/headless_pm_client.py" << 'EOF'
#!/usr/bin/env python3
"""Wrapper script that runs the actual client with the correct virtual environment."""
import os
import sys
import subprocess

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(script_dir, "headless_pm", ".venv", "bin", "python")
if not os.path.exists(venv_python):
    # Windows support
    venv_python = os.path.join(script_dir, "headless_pm", ".venv", "Scripts", "python.exe")

actual_client = os.path.join(script_dir, "headless_pm", "headless_pm_client.py")

# Run the actual client with the venv Python
subprocess.run([venv_python, actual_client] + sys.argv[1:])
EOF

chmod +x "$PROJECT_PATH/headless_pm_client.py"

# Create .env file inside headless_pm directory
echo -e "${BLUE}Creating .env file...${NC}"
cat > "$PROJECT_PATH/headless_pm/.env" << EOF
# Headless PM Client Configuration
API_KEY="$API_KEY"

# Server Configuration (default: local)
HEADLESS_PM_URL="http://localhost:6969"
EOF

# Create .gitignore to exclude venv
cat > "$PROJECT_PATH/headless_pm/.gitignore" << EOF
# Python virtual environment
.venv/
__pycache__/
*.pyc

# Environment files (contains API keys)
.env

# Agent logs
agent_logs/
EOF

# Install auto-commit if requested
if [ "$ENABLE_AUTOCOMMIT" = true ]; then
    echo -e "${BLUE}Installing auto-commit hook...${NC}"
    
    # Auto-commit script is already copied with the client files
    chmod +x "$PROJECT_PATH/headless_pm/git-auto-commit.sh"
    
    # Create Claude Code settings in target project
    mkdir -p "$PROJECT_PATH/.claude"
    cat > "$PROJECT_PATH/.claude/settings.json" << EOF
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "./headless_pm/git-auto-commit.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
EOF
    echo -e "${GREEN}✓ Auto-commit hook installed${NC}"
fi

# Install MCP client if requested
if [ "$ENABLE_MCP" = true ]; then
    echo -e "${BLUE}Installing MCP client...${NC}"
    
    # Create a temporary directory for MCP installation
    MCP_TEMP_DIR="$PROJECT_PATH/.mcp_install_temp"
    mkdir -p "$MCP_TEMP_DIR"
    
    # Copy MCP files to temporary directory
    cp "$SCRIPT_DIR/agents/claude/headless-pm-mcp-bridge.py" "$MCP_TEMP_DIR/"
    cp "$SCRIPT_DIR/agents/claude/install_client.sh" "$MCP_TEMP_DIR/"
    chmod +x "$MCP_TEMP_DIR/headless-pm-mcp-bridge.py"
    chmod +x "$MCP_TEMP_DIR/install_client.sh"
    
    # Run MCP installer with API key
    if [ -n "$API_KEY" ]; then
        export HEADLESS_PM_API_KEY="$API_KEY"
    fi
    
    cd "$MCP_TEMP_DIR"
    ./install_client.sh
    cd - > /dev/null
    
    # Clean up temporary directory
    rm -rf "$MCP_TEMP_DIR"
    
    echo -e "${GREEN}✓ MCP client installed${NC}"
fi

# Create convenience scripts
echo -e "${BLUE}Creating convenience scripts...${NC}"

# Create register script
cat > "$PROJECT_PATH/register_agent.sh" << 'EOF'
#!/bin/bash
# Quick agent registration script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Agent Registration"
echo "================="
echo ""

# Prompt for agent details
read -p "Agent ID (e.g., dev_001): " AGENT_ID
echo ""
echo "Available roles:"
echo "  - backend_dev"
echo "  - frontend_dev"
echo "  - fullstack_dev"
echo "  - qa"
echo "  - architect"
echo "  - pm"
read -p "Role: " ROLE
echo ""
echo "Skill levels: junior, senior, principal"
read -p "Level (default: senior): " LEVEL
LEVEL=${LEVEL:-senior}

# Register agent using the wrapper
"$SCRIPT_DIR/headless_pm_client.py" register \
    --agent-id "$AGENT_ID" \
    --role "$ROLE" \
    --level "$LEVEL"
EOF

chmod +x "$PROJECT_PATH/register_agent.sh"

# Create get next task script
cat > "$PROJECT_PATH/get_next_task.sh" << 'EOF'
#!/bin/bash
# Quick task fetching script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

read -p "Role (e.g., backend_dev): " ROLE
read -p "Level (default: senior): " LEVEL
LEVEL=${LEVEL:-senior}

"$SCRIPT_DIR/headless_pm_client.py" tasks next \
    --role "$ROLE" \
    --level "$LEVEL"
EOF

chmod +x "$PROJECT_PATH/get_next_task.sh"

# Final summary
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}Installed components:${NC}"
echo -e "  ✓ Python client at: $PROJECT_PATH/headless_pm/headless_pm_client.py"
echo -e "  ✓ Isolated Python environment at: $PROJECT_PATH/headless_pm/.venv/"
echo -e "  ✓ Team role docs at: $PROJECT_PATH/headless_pm/team_roles/"
echo -e "  ✓ Configuration at: $PROJECT_PATH/headless_pm/.env"
echo -e "  ✓ Client wrapper at: $PROJECT_PATH/headless_pm_client.py"

if [ "$ENABLE_AUTOCOMMIT" = true ]; then
    echo -e "  ✓ Auto-commit hook at: $PROJECT_PATH/.claude/settings.json"
fi

if [ "$ENABLE_MCP" = true ]; then
    echo -e "  ✓ MCP client (installed globally in Claude Code)"
fi

echo ""
echo -e "${BLUE}Quick start commands:${NC}"
echo -e "  ${YELLOW}# Register as an agent:${NC}"
echo -e "  ./register_agent.sh"
echo ""
echo -e "  ${YELLOW}# Get next task:${NC}"
echo -e "  ./get_next_task.sh"
echo ""
echo -e "  ${YELLOW}# Or use the client directly:${NC}"
echo -e "  ./headless_pm_client.py --help"
echo ""

if [ "$ENABLE_MCP" = true ]; then
    echo -e "${BLUE}MCP Usage:${NC}"
    echo -e "  In Claude Code, just use natural language:"
    echo -e "  ${YELLOW}'Register me as a backend developer'${NC}"
    echo -e "  ${YELLOW}'Get my next task'${NC}"
    echo -e "  ${YELLOW}'Create a task for the frontend team'${NC}"
    echo ""
fi

if [ -z "$API_KEY" ]; then
    echo -e "${YELLOW}⚠ Important: Don't forget to add your API key to $PROJECT_PATH/headless_pm/.env${NC}"
fi

echo -e "${GREEN}Happy coding!${NC}"