#!/usr/bin/env python3
"""
Health check hook - Periodic system health verification
"""
import sys
import psutil
import subprocess


def check_memory_usage(max_percent=90):
    """Check system memory usage"""
    memory = psutil.virtual_memory()
    
    if memory.percent > max_percent:
        return False, f"High memory usage: {memory.percent}%"
    return True, f"Memory usage OK: {memory.percent}%"


def check_api_connectivity():
    """Check if PM API is reachable"""
    try:
        # Try to reach the API endpoint
        import urllib.request
        api_url = "http://localhost:6969/health"
        
        with urllib.request.urlopen(api_url, timeout=5) as response:
            if response.status == 200:
                return True, "PM API is reachable"
            else:
                return False, f"PM API returned status {response.status}"
                
    except Exception as e:
        return False, f"Cannot reach PM API: {e}"


def check_process_count(max_processes=5):
    """Check for runaway processes"""
    # Count Claude processes
    claude_count = 0
    
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if 'claude' in proc.info['name'].lower() or \
               any('claude' in arg for arg in (proc.info['cmdline'] or [])):
                claude_count += 1
        except:
            pass
            
    if claude_count > max_processes:
        return False, f"Too many Claude processes: {claude_count}"
    return True, f"Process count OK: {claude_count} Claude processes"


def main():
    """Run health checks"""
    checks = [
        check_memory_usage(),
        check_api_connectivity(),
        check_process_count()
    ]
    
    # Collect results
    all_healthy = True
    messages = []
    
    for healthy, message in checks:
        messages.append(message)
        if not healthy:
            all_healthy = False
            
    # Output results
    print("\n".join(messages))
    
    # Exit with appropriate code
    sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()