"""
Test Resource Manager - Single Source of Truth for Process and Detection Management

Central manager for ALL test process and resource management:
- Process lifecycle management with robust cleanup patterns (terminate-wait-kill)
- Comprehensive leak detection using superior process tree tracking
- Port occupation detection for comprehensive resource monitoring
- MCP server failure diagnostics with detailed context
- Integration with real system port allocation (src.main.get_port)

Easy to use correctly, hard to use incorrectly.
Single authoritative manager for all test resource needs.
"""

import hashlib
import os
import psutil
import socket
import subprocess
import time
from typing import Dict, List, Set, Optional, Any
from pathlib import Path


class ProcessTreeLeakDetective:
    """
    Central manager for ALL test process and resource management.
    Handles process lifecycle, leak detection, cleanup coordination.
    Uses real system port allocation (src.main.get_port) for consistency.
    """
    
    def __init__(self):
        self.test_pid = os.getpid()
        self.initial_children: Set[int] = set()
        self.tracked_processes: Dict[int, Dict[str, Any]] = {}  # Enhanced process tracking
        self.allocated_ports: Set[int] = set()  # Track ports for cleanup verification
        self.test_identifier: Optional[str] = None
        
    def capture_baseline(self):
        """Capture baseline of child processes at test start."""
        try:
            current_process = psutil.Process(self.test_pid)
            self.initial_children = {child.pid for child in current_process.children(recursive=True)}
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.initial_children = set()
    
    def detect_leaks(self, test_name: str) -> Dict:
        """Detect and report process leaks using process tree tracking."""
        print(f"\n[TREE DETECTIVE] Investigating {test_name} (PID: {self.test_pid})")
        
        try:
            current_process = psutil.Process(self.test_pid)
            current_children = {child.pid for child in current_process.children(recursive=True)}
            leaked_pids = current_children - self.initial_children
            
            if not leaked_pids:
                print(f"[TREE DETECTIVE] ✅ {test_name}: No child process leaks detected")
                return {'leaks_found': 0, 'processes_killed': 0, 'leaked_processes': []}
            
            # Get detailed info about leaked processes
            leaked_processes = []
            for pid in leaked_pids:
                try:
                    proc = psutil.Process(pid)
                    leaked_processes.append({
                        'pid': pid,
                        'name': proc.name(),
                        'cmdline': ' '.join(proc.cmdline()),
                        'status': proc.status()
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    leaked_processes.append({
                        'pid': pid,
                        'name': 'unknown',
                        'cmdline': 'access denied',
                        'status': 'unknown'
                    })
            
            print(f"[TREE DETECTIVE] ❌ {test_name}: {len(leaked_processes)} child process leaks detected")
            for proc_info in leaked_processes:
                print(f"  PID {proc_info['pid']}: {proc_info['name']} - {proc_info['cmdline'][:80]}")
            
            # Attempt cleanup
            killed_count = 0
            for proc_info in leaked_processes:
                if self._terminate_process(proc_info['pid']):
                    killed_count += 1
            
            if killed_count > 0:
                time.sleep(1)  # Wait for cleanup
                print(f"[TREE DETECTIVE] SUMMARY {test_name}: Killed {killed_count}/{len(leaked_processes)} leaked child processes")
            
            return {
                'leaks_found': len(leaked_processes),
                'processes_killed': killed_count,
                'leaked_processes': leaked_processes
            }
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print(f"[TREE DETECTIVE] ⚠️ {test_name}: Cannot access test process tree")
            return {'leaks_found': 0, 'processes_killed': 0, 'leaked_processes': []}
    
    def _terminate_process(self, pid: int) -> bool:
        """Terminate a specific process safely."""
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=3)
            return True
        except (psutil.TimeoutExpired, psutil.NoSuchProcess, psutil.AccessDenied):
            try:
                proc.kill()
                return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False
        except Exception:
            return False
    
    def start_managed_process(self, command: List[str], port: int = None, 
                            test_name: str = "unknown", timeout: float = 30.0) -> subprocess.Popen:
        """
        Start and track a process with full lifecycle management.
        Integrates best practices from ProcessLifecycleManager and ServerManager.
        
        Args:
            command: Command to execute
            port: Port the process will use (if any)
            test_name: Test name for attribution
            timeout: Startup timeout
            
        Returns:
            Started process handle
        """
        try:
            # Start process with robust configuration
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Always capture stderr for diagnostics
                stdin=subprocess.PIPE,   # MCP servers need stdin
                text=True,
                bufsize=1  # Line buffering
            )
            
            # Track process for cleanup
            self.tracked_processes[proc.pid] = {
                'process': proc,
                'command': command,
                'port': port,
                'test_name': test_name,
                'start_time': time.time()
            }
            
            print(f"[PROCESS MANAGER] Started {test_name} process {proc.pid}" + 
                  (f" on port {port}" if port else ""))
            
            return proc
            
        except Exception as e:
            print(f"[PROCESS MANAGER] ❌ Failed to start {test_name}: {e}")
            raise
    
    def stop_managed_process(self, proc: subprocess.Popen, timeout: float = 10.0) -> bool:
        """
        Stop process with robust terminate-wait-kill pattern.
        
        Args:
            proc: Process to stop
            timeout: Graceful termination timeout
            
        Returns:
            True if successfully stopped
        """
        if proc.poll() is not None:
            # Process already terminated
            return True
            
        try:
            proc_info = self.tracked_processes.get(proc.pid, {})
            test_name = proc_info.get('test_name', 'unknown')
            
            print(f"[PROCESS MANAGER] Stopping {test_name} process {proc.pid}...")
            
            # 1. Close stdin first to signal graceful shutdown for MCP servers
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()
                
            # 2. Send SIGTERM to trigger signal handlers and coordination cleanup
            proc.terminate()
            
            try:
                proc.wait(timeout=timeout)
                print(f"[PROCESS MANAGER] ✅ Process {proc.pid} terminated gracefully")
                return True
            except subprocess.TimeoutExpired:
                # Force kill if graceful termination fails
                print(f"[PROCESS MANAGER] ⚠️ Process {proc.pid} timeout, force killing...")
                proc.kill()
                try:
                    proc.wait(timeout=2)
                    print(f"[PROCESS MANAGER] ✅ Process {proc.pid} force-killed")
                    return True
                except subprocess.TimeoutExpired:
                    print(f"[PROCESS MANAGER] ❌ Process {proc.pid} could not be killed")
                    return False
                    
        except Exception as e:
            print(f"[PROCESS MANAGER] ❌ Error stopping process {proc.pid}: {e}")
            return False
        finally:
            # Remove from tracking
            self.tracked_processes.pop(proc.pid, None)
    
    def cleanup_all_managed_processes(self, test_name: str = "unknown") -> Dict[str, Any]:
        """
        Clean up all tracked processes with comprehensive reporting.
        
        Returns:
            Cleanup statistics and results
        """
        cleanup_stats = {
            'test_name': test_name,
            'processes_cleaned': 0,
            'processes_killed': 0,
            'cleanup_failures': [],
            'ports_verified': 0
        }
        
        print(f"[PROCESS MANAGER] Cleaning up {len(self.tracked_processes)} tracked processes for {test_name}")
        
        # Stop all tracked processes
        for pid, info in list(self.tracked_processes.items()):
            proc = info['process']
            if self.stop_managed_process(proc):
                if proc.returncode == 0:
                    cleanup_stats['processes_cleaned'] += 1
                else:
                    cleanup_stats['processes_killed'] += 1
            else:
                cleanup_stats['cleanup_failures'].append({
                    'pid': pid,
                    'test_name': info['test_name'],
                    'command': info['command']
                })
        
        # Verify allocated ports are released
        for port in self.allocated_ports:
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result != 0:  # Port is free
                    cleanup_stats['ports_verified'] += 1
                else:
                    print(f"[PROCESS MANAGER] ⚠️ Port {port} still occupied after cleanup")
            except Exception:
                pass
        
        print(f"[PROCESS MANAGER] Cleanup complete: {cleanup_stats['processes_cleaned']} graceful, "
              f"{cleanup_stats['processes_killed']} killed, {cleanup_stats['ports_verified']} ports freed")
        
        return cleanup_stats


# Global instance for test coordination
_tree_detective = ProcessTreeLeakDetective()


def setup_process_tree_tracking():
    """Call at the beginning of test class to establish baseline."""
    _tree_detective.capture_baseline()
    print(f"[TREE DETECTIVE] Baseline captured for PID {_tree_detective.test_pid}")


def detect_and_cleanup_process_tree_leaks(test_name: str) -> Dict:
    """
    DRY function for process tree leak detection and cleanup.
    
    Usage in test teardown:
        def tearDown(self):
            detect_and_cleanup_process_tree_leaks("TestClassName.test_method_name")
    
    Args:
        test_name: Name of test for attribution
        
    Returns:
        Cleanup statistics dict
    """
    return _tree_detective.detect_leaks(test_name)


def check_for_orphaned_ports(test_ports: Set[int] = None) -> List[Dict]:
    """
    Check if any CHILD PROCESSES of the test are occupying ports (process ancestry approach).
    Uses same superior methodology as process tree tracking - no system-wide scanning.
    """
    global _tree_detective
    
    test_ports = test_ports or {6969, 6968, 3001}  # Default HeadlessPM ports
    orphaned_ports = []
    
    # Get current child processes (same approach as process tree detection)
    try:
        current_process = psutil.Process(_tree_detective.test_pid)
        current_children = current_process.children(recursive=True)
        
        # For each child process, check if it's occupying any test ports
        for child in current_children:
            try:
                # Check all connections of this child process
                for conn in child.connections():
                    if conn.laddr and conn.laddr.port in test_ports:
                        # This child process is occupying a test port
                        orphaned_ports.append({
                            'port': conn.laddr.port,
                            'pid': child.pid,
                            'name': child.name(),
                            'cmdline': ' '.join(child.cmdline())
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process may have terminated or denied access - skip
                continue
                
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        # Test process itself is gone or denied - skip port check
        pass
    
    if orphaned_ports:
        print(f"[PORT DETECTIVE] Found {len(orphaned_ports)} child processes on test ports:")
        for port_info in orphaned_ports:
            print(f"  Port {port_info['port']}: PID {port_info['pid']} - {port_info['cmdline'][:80]}")
    
    return orphaned_ports



def comprehensive_leak_detection(test_name: str, test_ports: Set[int] = None) -> Dict:
    """
    Comprehensive leak detection combining process tree and port checking.
    
    Usage:
        def tearDown(self):
            comprehensive_leak_detection("TestClass.test_method", {6969, 8080})
    """
    print(f"\n[COMPREHENSIVE DETECTIVE] Starting investigation for {test_name}")
    
    # Process tree leak detection
    tree_results = detect_and_cleanup_process_tree_leaks(test_name)
    
    # Port-based orphan detection
    orphaned_ports = check_for_orphaned_ports(test_ports)
    
    total_leaks = tree_results['leaks_found'] + len(orphaned_ports)
    
    if total_leaks == 0:
        print(f"[COMPREHENSIVE DETECTIVE] ✅ {test_name}: No leaks detected")
    else:
        print(f"[COMPREHENSIVE DETECTIVE] ❌ {test_name}: {total_leaks} total leaks detected")
        print(f"  - Child process leaks: {tree_results['leaks_found']}")
        print(f"  - Orphaned port processes: {len(orphaned_ports)}")
    
    return {
        'test_name': test_name,
        'total_leaks': total_leaks,
        'child_process_leaks': tree_results['leaks_found'],
        'orphaned_ports': len(orphaned_ports),
        'processes_killed': tree_results['processes_killed'],
        'leaked_processes': tree_results['leaked_processes'],
        'port_processes': orphaned_ports
    }


def log_mcp_server_failure_context(server_manager, test_name: str = "Unknown") -> str:
    """
    Log comprehensive MCP server failure context for debugging.
    Integrated from resource_leak_detector.py - this function was uniquely valuable.
    """
    report = [f"\n=== MCP SERVER FAILURE CONTEXT: {test_name} (Port {server_manager.port}) ==="]
    
    # Check if port is actually free
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', server_manager.port))
        sock.close()
        
        if result == 0:
            report.append(f"❌ Port {server_manager.port} is OCCUPIED (not free as expected)")
        else:
            report.append(f"✅ Port {server_manager.port} is free")
    except Exception as e:
        report.append(f"⚠️ Port check failed: {e}")
    
    # Check for running API processes
    api_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            if any(keyword in cmdline for keyword in ['uvicorn', 'src.main', f':{server_manager.port}']):
                api_processes.append(f"PID {proc.info['pid']}: {cmdline[:80]}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if api_processes:
        report.append(f"❌ Found {len(api_processes)} potentially conflicting API processes:")
        for proc_info in api_processes:
            report.append(f"  {proc_info}")
    else:
        report.append("✅ No conflicting API processes found")
    
    # Check MCP coordination files
    try:
        mcp_files = list(Path("/tmp").glob("*mcp_coordination*"))
        if mcp_files:
            report.append(f"⚠️ Found {len(mcp_files)} MCP coordination files:")
            for f in mcp_files[:5]:  # Limit to first 5
                report.append(f"  {f.name}")
        else:
            report.append("✅ No MCP coordination files in /tmp")
    except Exception as e:
        report.append(f"⚠️ File check failed: {e}")
    
    failure_context = "\n".join(report)
    print(failure_context)
    return failure_context


def robust_process_cleanup(process_list: List[subprocess.Popen], test_name: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Implement robust terminate-wait-kill pattern for process cleanup.
    This prevents the source-level leaks identified in the analysis.
    """
    cleanup_report = {
        "test_name": test_name,
        "processes_cleaned": 0,
        "processes_killed": 0,
        "cleanup_failures": []
    }
    
    for proc in process_list:
        if proc and proc.poll() is None:
            try:
                print(f"[ROBUST CLEANUP] Terminating process {proc.pid} for {test_name}...")
                proc.terminate()
                
                try:
                    # Wait up to timeout seconds for graceful exit
                    proc.wait(timeout=timeout)
                    print(f"[ROBUST CLEANUP] ✅ Process {proc.pid} terminated gracefully")
                    cleanup_report["processes_cleaned"] += 1
                except subprocess.TimeoutExpired:
                    # Force kill if graceful termination fails
                    print(f"[ROBUST CLEANUP] ⚠️ Process {proc.pid} did not exit in time, force killing...")
                    proc.kill()
                    try:
                        proc.wait(timeout=2)
                        print(f"[ROBUST CLEANUP] ✅ Process {proc.pid} force-killed successfully")
                        cleanup_report["processes_killed"] += 1
                    except subprocess.TimeoutExpired:
                        print(f"[ROBUST CLEANUP] ❌ Process {proc.pid} could not be killed")
                        cleanup_report["cleanup_failures"].append({
                            "pid": proc.pid,
                            "error": "Could not be killed even with force"
                        })
                        
            except Exception as e:
                print(f"[ROBUST CLEANUP] ❌ Failed to cleanup process {proc.pid}: {e}")
                cleanup_report["cleanup_failures"].append({
                    "pid": proc.pid,
                    "error": str(e)
                })
    
    print(f"[ROBUST CLEANUP] {test_name}: {cleanup_report['processes_cleaned']} graceful, {cleanup_report['processes_killed']} force-killed, {len(cleanup_report['cleanup_failures'])} failures")
    return cleanup_report


def per_test_file_port_detection(test_file_path: str, test_ports: Set[int] = None) -> Dict[str, Any]:
    """
    Enhanced leak detection for end-of-test-file validation.
    Reports exact test file and specific ports still orphaned.
    
    Usage in test file teardown_class:
        @classmethod 
        def teardown_class(cls):
            per_test_file_port_detection(__file__, {6969, 6968, 3001})
    
    Args:
        test_file_path: __file__ of the test file for exact attribution
        test_ports: Set of ports this test file uses
        
    Returns:
        Dict with test file name, orphaned ports, and specific process details
    """
    test_file_name = os.path.basename(test_file_path)
    test_ports = test_ports or {6969, 6968, 3001}  # Default HeadlessPM ports
    
    print(f"\n[FILE PORT DETECTIVE] Checking {test_file_name} for orphaned ports: {test_ports}")
    
    orphaned_details = {
        "test_file": test_file_name,
        "test_file_path": test_file_path,
        "checked_ports": list(test_ports),
        "orphaned_ports": [],
        "clean_ports": [],
        "total_orphans": 0
    }
    
    for port in test_ports:
        try:
            # Check if port is occupied using socket test
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                # Port is occupied - get process details
                try:
                    result = subprocess.run(
                        ['lsof', '-ti', f':{port}'],
                        capture_output=True, text=True, check=False
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') if pid.strip().isdigit()]
                        for pid in pids:
                            try:
                                proc = psutil.Process(pid)
                                orphaned_details["orphaned_ports"].append({
                                    "port": port,
                                    "pid": pid,
                                    "name": proc.name(),
                                    "cmdline": ' '.join(proc.cmdline()[:5]),  # First 5 args
                                    "create_time": proc.create_time(),
                                    "status": proc.status()
                                })
                                orphaned_details["total_orphans"] += 1
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                orphaned_details["orphaned_ports"].append({
                                    "port": port,
                                    "pid": pid,
                                    "name": "unknown",
                                    "cmdline": "access denied"
                                })
                                orphaned_details["total_orphans"] += 1
                except (subprocess.SubprocessError, FileNotFoundError):
                    # lsof not available - fallback to socket check only
                    orphaned_details["orphaned_ports"].append({
                        "port": port,
                        "pid": "unknown", 
                        "name": "unknown",
                        "cmdline": "lsof not available - port occupied"
                    })
                    orphaned_details["total_orphans"] += 1
            else:
                # Port is free
                orphaned_details["clean_ports"].append(port)
                
        except Exception as e:
            print(f"[FILE PORT DETECTIVE] Error checking port {port}: {e}")
    
    # Report results
    if orphaned_details["total_orphans"] > 0:
        print(f"[FILE PORT DETECTIVE] ❌ {test_file_name}: {orphaned_details['total_orphans']} orphaned ports detected")
        for port_info in orphaned_details["orphaned_ports"]:
            print(f"  Port {port_info['port']}: PID {port_info['pid']} - {port_info['name']} ({port_info['cmdline']})")
        print(f"[FILE PORT DETECTIVE] Clean ports: {orphaned_details['clean_ports']}")
    else:
        print(f"[FILE PORT DETECTIVE] ✅ {test_file_name}: All test ports clean ({orphaned_details['clean_ports']})")
    
    return orphaned_details


def capture_system_state() -> Dict:
    """
    Capture system state for leak detection.
    Integrated from resource_leak_detector.py for backwards compatibility.
    """
    state = {
        'processes': [],
        'ports': [],
        'files': [],
        'timestamp': time.time()
    }
    
    # Capture processes containing headless-pm, mcp, or uvicorn
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            name = proc.info['name'] or ''
            
            if any(keyword in cmdline.lower() or keyword in name.lower() for keyword in [
                'headless-pm', 'mcp', 'uvicorn', 'src.main', 'src.mcp', 'python3.*src'
            ]):
                state['processes'].append({
                    'pid': proc.info['pid'],
                    'name': name,
                    'cmdline': cmdline[:100]  # Truncate for readability
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Capture bound ports in test range
    for conn in psutil.net_connections():
        try:
            if conn.laddr and 6000 <= conn.laddr.port <= 10000:
                state['ports'].append({
                    'port': conn.laddr.port,
                    'status': conn.status,
                    'pid': conn.pid
                })
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    
    # Capture coordination files
    temp_dir = Path("/tmp")
    for pattern in ["headless_pm_*.json", "*.lock", "*mcp*.json"]:
        for file_path in temp_dir.glob(pattern):
            try:
                stat = file_path.stat()
                state['files'].append({
                    'path': str(file_path),
                    'size': stat.st_size,
                    'mtime': stat.st_mtime
                })
            except (OSError, FileNotFoundError):
                pass
    
    return state


def compare_states(before: Dict, after: Dict) -> Dict:
    """
    Compare system states to identify resource leaks.
    Integrated from resource_leak_detector.py for backwards compatibility.
    """
    leaks = {
        'new_processes': [],
        'new_ports': [],
        'new_files': []
    }
    
    # Find new processes
    before_pids = {p['pid'] for p in before['processes']}
    for proc in after['processes']:
        if proc['pid'] not in before_pids:
            leaks['new_processes'].append(proc)
    
    # Find new ports  
    before_ports = {p['port'] for p in before['ports']}
    for port in after['ports']:
        if port['port'] not in before_ports:
            leaks['new_ports'].append(port)
    
    # Find new files
    before_files = {f['path'] for f in before['files']}
    for file_info in after['files']:
        if file_info['path'] not in before_files:
            leaks['new_files'].append(file_info)
    
    return leaks


def audit_test_contamination(test_name: str, before_state: Dict, after_state: Dict) -> str:
    """
    Generate audit report of test contamination.
    Integrated from resource_leak_detector.py for backwards compatibility.
    """
    leaks = compare_states(before_state, after_state)
    
    report = [f"\n=== RESOURCE LEAK AUDIT: {test_name} ==="]
    
    total_leaks = len(leaks['new_processes']) + len(leaks['new_ports']) + len(leaks['new_files'])
    
    if total_leaks == 0:
        report.append("✅ NO RESOURCE LEAKS DETECTED")
        return '\n'.join(report)
    
    report.append(f"❌ {total_leaks} RESOURCE LEAKS DETECTED")
    
    if leaks['new_processes']:
        report.append(f"\nLEAKED PROCESSES ({len(leaks['new_processes'])}):")
        for proc in leaks['new_processes']:
            report.append(f"  PID {proc['pid']}: {proc['name']} - {proc['cmdline']}")
    
    if leaks['new_ports']:
        report.append(f"\nLEAKED PORTS ({len(leaks['new_ports'])}):")
        for port in leaks['new_ports']:
            report.append(f"  Port {port['port']}: {port['status']} (PID {port['pid']})")
    
    if leaks['new_files']:
        report.append(f"\nLEAKED FILES ({len(leaks['new_files'])}):")
        for file_info in leaks['new_files']:
            report.append(f"  {file_info['path']}: {file_info['size']} bytes")
    
    report.append("=== END AUDIT ===")
    return '\n'.join(report)