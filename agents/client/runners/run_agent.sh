#!/bin/bash

# Direct Claude runner - bypasses Python to avoid terminal issues
# This is called by agent_runner.sh after setup

set -euo pipefail

# Get arguments
INSTRUCTIONS_FILE="$1"
CLAUDE_CMD="$2"
shift 2
CLAUDE_FLAGS="$@"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Run Claude with proper terminal handling
echo -e "${GREEN}Starting Claude session...${NC}"
echo "Instructions: $INSTRUCTIONS_FILE"
echo "Command: $CLAUDE_CMD $CLAUDE_FLAGS"
echo "-" 

# Run Claude with instructions - direct terminal access with timeout
timeout 600 $CLAUDE_CMD $CLAUDE_FLAGS < "$INSTRUCTIONS_FILE"  # 10 minute timeout

exit_code=$?
echo -e "\n${YELLOW}Session ended with code: $exit_code${NC}"

exit $exit_code