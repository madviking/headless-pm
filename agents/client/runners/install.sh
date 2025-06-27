#!/bin/bash

# Install script for agent runner
# This adds the agent runner to your PATH

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_NAME="headless-agent"

echo "📦 Installing Headless PM Agent Runner..."
echo ""
echo "⚠️  SECURITY WARNING:"
echo "    This tool can execute code and modify files automatically."
echo "    Always review agent instructions and run in controlled environments."
echo "    NEVER use --dangerously-skip-permissions without understanding the risks."
echo ""

# Check if already in PATH
if command -v "$INSTALL_NAME" &> /dev/null; then
    echo "⚠️  $INSTALL_NAME is already installed"
    echo "   Location: $(which $INSTALL_NAME)"
    echo ""
    echo "To reinstall, first remove the existing installation:"
    echo "  rm $(which $INSTALL_NAME)"
    exit 1
fi

# Determine install location
if [[ -d "$HOME/.local/bin" ]]; then
    INSTALL_DIR="$HOME/.local/bin"
elif [[ -d "/usr/local/bin" ]] && [[ -w "/usr/local/bin" ]]; then
    INSTALL_DIR="/usr/local/bin"
else
    INSTALL_DIR="$HOME/bin"
    mkdir -p "$INSTALL_DIR"
fi

# Create symlink
echo "Installing to: $INSTALL_DIR/$INSTALL_NAME"
ln -sf "$SCRIPT_DIR/agent_runner.sh" "$INSTALL_DIR/$INSTALL_NAME"
chmod +x "$INSTALL_DIR/$INSTALL_NAME"

# Check if install directory is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo "⚠️  $INSTALL_DIR is not in your PATH"
    echo ""
    echo "Add it to your shell configuration:"
    
    if [[ -f "$HOME/.zshrc" ]]; then
        echo "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.zshrc"
        echo "  source ~/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        echo "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.bashrc"
        echo "  source ~/.bashrc"
    else
        echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
    fi
    echo ""
fi

echo "✅ Installation complete!"
echo ""
echo "Usage:"
echo "  $INSTALL_NAME <role> <agent_id> [options]"
echo ""
echo "Safe Examples (Recommended):"
echo "  $INSTALL_NAME backend_dev dev_001"
echo "  $INSTALL_NAME qa qa_001 --one-task-only"
echo "  $INSTALL_NAME frontend_dev dev_002 --stop-on-sonnet"
echo ""
echo "⚠️  DANGEROUS (use with extreme caution):"
echo "  $INSTALL_NAME backend_dev dev_001 --dangerously-skip-permissions"
echo ""
echo "This will work from any directory within a headless-pm project."
echo "For full documentation and security guidelines, see:"
echo "  $(dirname "$SCRIPT_DIR")/runners/README.md"