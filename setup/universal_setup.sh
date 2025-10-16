#!/bin/bash
# Universal setup script that works for both ARM64 and x86_64

set -e

echo "==================================="
echo "Universal Environment Setup"
echo "==================================="

# Detect architecture
ARCH=$(uname -m)
echo "Detected architecture: $ARCH"

# Determine which venv to use
if [[ "$ARCH" == "arm64" ]]; then
    VENV_NAME="venv"
    echo "Using standard venv for ARM64"
else
    VENV_NAME="claude_venv"
    echo "Using claude_venv for x86_64"
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Determine project root (parent of setup directory)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"
echo "Working from: $(pwd)"

# Create appropriate virtual environment
if [ ! -d "$VENV_NAME" ]; then
    echo "Creating virtual environment: $VENV_NAME"
    python3 -m venv $VENV_NAME
fi

# Activate the environment
source $VENV_NAME/bin/activate

# Upgrade pip
pip install --upgrade pip

# Clear pip cache on macOS ARM64 to prevent cached x86_64 pydantic-core wheels
# Without this: ImportError: mach-o file, but is an incompatible architecture (have 'x86_64', need 'arm64')
# Root cause: pip caches x86_64 wheels from Rosetta Python, installs wrong architecture on native ARM64 Python
# Solution: Clear cache + --no-cache-dir forces fresh ARM64 wheel download
# See: https://github.com/pydantic/pydantic/discussions/3736
if [[ "$ARCH" == "arm64" && "$(uname -s)" == "Darwin" ]]; then
    pip cache purge >/dev/null 2>&1 || true
fi

# Install packages based on architecture
if [[ "$ARCH" == "arm64" ]]; then
    # Standard installation for ARM64
    echo "Installing packages for ARM64..."
    pip install --no-cache-dir -r setup/requirements.txt
else
    # Install for x86_64 (specific pydantic versions for compatibility)
    echo "Installing packages for x86_64..."

    # First, install pydantic with specific versions for x86_64 environments
    pip install pydantic==2.11.7 pydantic-core==2.33.2

    # Then install the rest of the requirements
    pip install -r setup/requirements.txt
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ] && [ -f "env-example" ]; then
    echo "Creating .env from env-example..."
    cp env-example .env
fi

echo ""
echo "==================================="
echo "Setup complete!"
echo "==================================="
echo ""
echo "Environment: $VENV_NAME"
echo "Architecture: $ARCH"
echo ""
echo "To activate this environment:"
echo "  source $VENV_NAME/bin/activate"
echo ""
echo "To run the application:"
echo "  ./start.sh"
echo ""
echo "To run tests:"
echo "  python -m pytest tests/"