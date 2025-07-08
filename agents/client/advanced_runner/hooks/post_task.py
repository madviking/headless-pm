#!/usr/bin/env python3
"""
Post-task hook - Cleanup and logging after task completion
"""
import sys
import json
import os
from datetime import datetime
from pathlib import Path


def log_task_completion(task_data):
    """Log task completion details"""
    log_dir = Path.home() / ".headless-pm" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "task_completions.jsonl"
    
    # Add timestamp
    task_data['completed_at'] = datetime.now().isoformat()
    
    # Append to log file
    with open(log_file, 'a') as f:
        json.dump(task_data, f)
        f.write('\n')
        
    return True, f"Logged to {log_file}"


def cleanup_temp_files():
    """Clean up any temporary files"""
    # Look for common temp patterns
    temp_patterns = [
        "*.tmp",
        "*.bak",
        ".*.swp"
    ]
    
    cleaned = 0
    # This is a placeholder - in real use you'd be more careful
    # about what files to clean up
    
    return True, f"Cleaned {cleaned} temporary files"


def main():
    """Run post-task operations"""
    # Read task result from stdin
    task_data = {}
    if not sys.stdin.isatty():
        try:
            task_data = json.loads(sys.stdin.read())
        except:
            pass
    
    # Run post-task operations
    operations = [
        log_task_completion(task_data),
        cleanup_temp_files()
    ]
    
    # Collect results
    messages = []
    for success, message in operations:
        messages.append(message)
        
    # Output results
    print("\n".join(messages))
    
    # Always exit 0 - post-task hooks are non-critical
    sys.exit(0)


if __name__ == "__main__":
    main()