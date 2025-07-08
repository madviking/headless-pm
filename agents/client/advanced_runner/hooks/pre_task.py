#!/usr/bin/env python3
"""
Pre-task hook - Check system health before starting task
"""
import sys
import json
import shutil
import subprocess


def check_disk_space(min_gb=1):
    """Check if enough disk space is available"""
    usage = shutil.disk_usage('.')
    free_gb = usage.free / (1024**3)
    
    if free_gb < min_gb:
        return False, f"Low disk space: {free_gb:.1f}GB free (need {min_gb}GB)"
    return True, f"Disk space OK: {free_gb:.1f}GB free"


def check_git_status():
    """Check if git is in a clean state"""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return False, "Git status check failed"
            
        if result.stdout.strip():
            # Has uncommitted changes - might be OK depending on workflow
            return True, "Warning: Git has uncommitted changes"
            
        return True, "Git status clean"
        
    except Exception as e:
        return False, f"Failed to check git status: {e}"


def check_claude_available():
    """Verify Claude CLI is accessible"""
    try:
        result = subprocess.run(
            ['claude', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return True, "Claude CLI available"
        else:
            return False, "Claude CLI not responding"
            
    except FileNotFoundError:
        return False, "Claude CLI not found in PATH"
    except Exception as e:
        return False, f"Failed to check Claude: {e}"


def main():
    """Run pre-task checks"""
    # Read task data from stdin if provided
    task_data = {}
    if not sys.stdin.isatty():
        try:
            task_data = json.loads(sys.stdin.read())
        except:
            pass
    
    # Run checks
    checks = [
        check_disk_space(),
        check_git_status(),
        check_claude_available()
    ]
    
    # Collect results
    all_passed = True
    messages = []
    
    for passed, message in checks:
        messages.append(message)
        if not passed:
            all_passed = False
            
    # Output results
    print("\n".join(messages))
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()