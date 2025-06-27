#!/bin/bash

# Universal Claude Agent Runner - works from any directory
# Usage: agent_runner_universal.sh <role> <agent_id> [options]

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
ROLE="${1:-}"
AGENT_ID="${2:-}"
shift 2 || true

if [[ -z "$ROLE" ]] || [[ -z "$AGENT_ID" ]]; then
    echo "Usage: $0 <role> <agent_id> [options]"
    echo "  role: backend_dev, frontend_dev, qa, architect, pm, fullstack_dev"
    echo "  agent_id: e.g., dev_001, qa_001"
    echo ""
    echo "Options:"
    echo "  --one-task-only                Run only one task then exit"
    echo "  --stop-on-sonnet               Stop when Claude switches to Sonnet"
    echo "  --dangerously-skip-permissions Pass through to Claude"
    exit 1
fi

# Get the real directory where this script is located (follow symlinks)
SCRIPT_PATH="${BASH_SOURCE[0]}"

# Resolve symlinks
while [[ -L "$SCRIPT_PATH" ]]; do
    SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    
    # If readlink returned a relative path, make it absolute
    if [[ "$SCRIPT_PATH" != /* ]]; then
        SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
    fi
done

# Get the final directory
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

# Function to find the project root by looking for markers
find_project_root() {
    local current_dir="$PWD"
    
    # Look for common project markers
    while [[ "$current_dir" != "/" ]]; do
        # Check for headless_pm_client.py in various locations
        if [[ -f "$current_dir/headless_pm_client.py" ]] || \
           [[ -f "$current_dir/headless_pm/headless_pm_client.py" ]] || \
           [[ -f "$current_dir/.git/config" && -f "$current_dir/headless_pm/headless_pm_client.py" ]]; then
            echo "$current_dir"
            return 0
        fi
        current_dir="$(dirname "$current_dir")"
    done
    
    # If not found from current directory, try from script location
    current_dir="$SCRIPT_DIR"
    while [[ "$current_dir" != "/" ]]; do
        if [[ -f "$current_dir/headless_pm_client.py" ]] || \
           [[ -f "$current_dir/headless_pm/headless_pm_client.py" ]]; then
            echo "$current_dir"
            return 0
        fi
        current_dir="$(dirname "$current_dir")"
    done
    
    return 1
}

# Function to find headless_pm_client.py
find_client_script() {
    local project_root="$1"
    
    # Check common locations
    local candidates=(
        "$project_root/headless_pm_client.py"
        "$project_root/headless_pm/headless_pm_client.py"
        "$project_root/agents/client/headless_pm_client.py"
        "$PWD/headless_pm_client.py"
        "$PWD/headless_pm/headless_pm_client.py"
    )
    
    for candidate in "${candidates[@]}"; do
        if [[ -f "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    done
    
    return 1
}

# Function to find team_roles directory
find_team_roles() {
    local project_root="$1"
    
    # Primary check: if we're in a copied headless_pm directory structure
    local candidates=(
        "$SCRIPT_DIR/../team_roles"                    # runners/../team_roles
        "$project_root/headless_pm/team_roles"         # project/headless_pm/team_roles
    )
    
    # Also check relative to headless_pm_client.py location
    if [[ -n "${CLIENT_SCRIPT:-}" ]]; then
        local client_dir="$(dirname "$CLIENT_SCRIPT")"
        candidates+=(
            "$client_dir/team_roles"                    # same dir as client
        )
    fi
    
    # Legacy/fallback locations
    candidates+=(
        "$project_root/agents/client/team_roles"       # original structure
        "$project_root/team_roles"                     # root level
        "$PWD/team_roles"                              # current directory
    )
    
    for candidate in "${candidates[@]}"; do
        if [[ -d "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    done
    
    return 1
}

# Find project root
echo -e "${BLUE}🔍 Looking for project root...${NC}"
if PROJECT_ROOT=$(find_project_root); then
    echo -e "${GREEN}✓ Found project root: $PROJECT_ROOT${NC}"
else
    echo -e "${RED}✗ Could not find project root (no headless_pm_client.py found)${NC}"
    echo "Make sure you're running this from within a headless-pm project"
    exit 1
fi

# Find client script
echo -e "${BLUE}🔍 Looking for headless_pm_client.py...${NC}"
if CLIENT_SCRIPT=$(find_client_script "$PROJECT_ROOT"); then
    echo -e "${GREEN}✓ Found client script: $CLIENT_SCRIPT${NC}"
    # Export for agent to use
    export HEADLESS_PM_CLIENT_PATH="$CLIENT_SCRIPT"
else
    echo -e "${RED}✗ Could not find headless_pm_client.py${NC}"
    exit 1
fi

# Find team roles directory
echo -e "${BLUE}🔍 Looking for team roles...${NC}"
if TEAM_ROLES_DIR=$(find_team_roles "$PROJECT_ROOT"); then
    echo -e "${GREEN}✓ Found team roles: $TEAM_ROLES_DIR${NC}"
else
    echo -e "${RED}✗ Could not find team_roles directory${NC}"
    echo ""
    echo "This script is designed for headless-pm projects."
    echo "Current project appears to be: $(basename "$PROJECT_ROOT")"
    echo ""
    echo "Expected team_roles directory structure:"
    echo "  - agents/client/team_roles/"
    echo "  - team_roles/"
    echo ""
    echo "If you're trying to use this in a different project,"
    echo "you may need to copy the team_roles directory or"
    echo "run this from a proper headless-pm project."
    exit 1
fi

# Check if instructions file exists
INSTRUCTIONS_FILE="$TEAM_ROLES_DIR/${ROLE}.md"
if [[ ! -f "$INSTRUCTIONS_FILE" ]]; then
    echo -e "${RED}✗ Role instructions not found: $INSTRUCTIONS_FILE${NC}"
    echo "Available roles:"
    ls -1 "$TEAM_ROLES_DIR" | grep '\.md$' | sed 's/\.md$//' | sed 's/^/  - /'
    exit 1
fi

# Additional flags
ONE_TASK_ONLY=false
STOP_ON_SONNET=false
CLAUDE_FLAGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --one-task-only)
            ONE_TASK_ONLY=true
            shift
            ;;
        --stop-on-sonnet)
            STOP_ON_SONNET=true
            shift
            ;;
        --dangerously-skip-permissions)
            CLAUDE_FLAGS="$CLAUDE_FLAGS --dangerously-skip-permissions"
            shift
            ;;
        *)
            CLAUDE_FLAGS="$CLAUDE_FLAGS $1"
            shift
            ;;
    esac
done

# Create necessary directories
LOG_DIR="$PROJECT_ROOT/agent_logs"
mkdir -p "$LOG_DIR"

# Display configuration
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Configuration:${NC}"
echo -e "  Working Directory: $PWD"
echo -e "  Project Root: $PROJECT_ROOT"
echo -e "  Client Script: $CLIENT_SCRIPT"
echo -e "  Role: $ROLE"
echo -e "  Agent ID: $AGENT_ID"
echo -e "  Instructions: $INSTRUCTIONS_FILE"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Change to project root for execution
cd "$PROJECT_ROOT"

# Find Claude executable
find_claude() {
    local paths=(
        "$HOME/.claude/local/node_modules/.bin/claude"
        "$HOME/.claude/local/claude"
        "/usr/local/bin/claude"
        "claude"
    )
    
    for path in "${paths[@]}"; do
        if [[ -x "$path" ]]; then
            echo "$path"
            return 0
        fi
    done
    
    echo "claude"
}

CLAUDE_CMD=$(find_claude)
echo -e "${GREEN}Using Claude: $CLAUDE_CMD${NC}"

# Set environment for client path
export HEADLESS_PM_CLIENT_PATH="$CLIENT_SCRIPT"

# Main loop
session_count=0
while true; do
    ((session_count++))
    echo -e "\n${GREEN}=== Session $session_count ===${NC}"
    
    # Run Claude directly with full terminal access
    "$SCRIPT_DIR/run_agent.sh" "$INSTRUCTIONS_FILE" "$CLAUDE_CMD" $CLAUDE_FLAGS
    
    # Check if one-task-only
    if [[ "$ONE_TASK_ONLY" == "true" ]]; then
        echo "One-task mode: exiting"
        break
    fi
    
    # Wait before restart
    echo -e "${YELLOW}⏳ Waiting 30 seconds before restart...${NC}"
    echo "Press Ctrl+C to stop"
    
    # Trap Ctrl+C during sleep
    if ! sleep 30; then
        echo -e "${RED}Interrupted${NC}"
        break
    fi
done