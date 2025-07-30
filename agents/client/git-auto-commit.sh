#!/bin/bash

# Git Auto-commit Script
# Adds all changes, commits with timestamp, and pushes to remote

set -e  # Exit on any error

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Check if there are any changes to commit
if git diff-index --quiet HEAD --; then
    echo "No changes to commit"
    exit 0
fi

# Add all files
echo "Adding all files to git..."
git add .

# Create commit message with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_MSG="Auto-commit: $TIMESTAMP

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Commit changes
echo "Committing changes..."
git commit -m "$COMMIT_MSG"

# Push to remote
echo "Pushing to remote..."
git push

echo "✅ Successfully committed and pushed changes"