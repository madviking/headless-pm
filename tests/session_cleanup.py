"""
Session-level cleanup to prevent resource accumulation across tests.
Based on empirical observation that tests pass individually but fail in full suite.
"""

import pytest
import psutil
import os
import signal
import time
from pathlib import Path


@pytest.fixture(scope="class", autouse=True)
def global_test_cleanup():
    """Aggressive session-level cleanup between test classes."""
    yield
    
    # Post-class cleanup to prevent resource accumulation
    print("\n[SESSION CLEANUP] Executing aggressive inter-class cleanup...")
    
    # 1. Kill any processes containing headless-pm or mcp keywords
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'cmdline', 'name']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            name = proc.info['name'] or ''
            
            # Target processes that might be test artifacts
            if any(keyword in cmdline.lower() or keyword in name.lower() for keyword in [
                'headless-pm', 'mcp', 'uvicorn', 'src.main', 'src.mcp'
            ]):
                # Don't kill our own test process
                if proc.pid != os.getpid():
                    try:
                        proc.terminate()
                        proc.wait(timeout=3)
                        killed_count += 1
                    except (psutil.TimeoutExpired, psutil.NoSuchProcess, psutil.AccessDenied):
                        try:
                            proc.kill()
                            killed_count += 1
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if killed_count > 0:
        print(f"[SESSION CLEANUP] Terminated {killed_count} stray processes")
    
    # 2. Clean up coordination files
    temp_dir = Path("/tmp")
    cleaned_files = 0
    for pattern in ["headless_pm_mcp_*.json", "headless_pm_mcp_coordination.json", "*.lock"]:
        for file_path in temp_dir.glob(pattern):
            try:
                file_path.unlink()
                cleaned_files += 1
            except FileNotFoundError:
                pass
    
    if cleaned_files > 0:
        print(f"[SESSION CLEANUP] Removed {cleaned_files} coordination files")
    
    # 3. Wait for port cleanup
    time.sleep(1)
    
    print("[SESSION CLEANUP] Global cleanup complete")


def cleanup_session_resources():
    """Manual session cleanup function for critical test transitions."""
    # Kill test-related processes
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            if 'test' in cmdline and any(kw in cmdline for kw in ['mcp', 'headless', 'uvicorn']):
                if proc.pid != os.getpid():  # Don't kill ourselves
                    proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Clean coordination files
    for file_path in Path("/tmp").glob("headless_pm_*.json"):
        try:
            file_path.unlink()
        except FileNotFoundError:
            pass