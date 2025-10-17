"""
Systematic test isolation audit to identify cross-test resource leakage.
Implements rigorous empirical methodology for debugging intermittent failures.
"""

import pytest
import psutil
import os
import socket
import time
import subprocess
from pathlib import Path
from typing import Set, Dict, List, Tuple
from tests.process_tree_leak_detective import comprehensive_leak_detection


class TestIsolationAuditor:
    """Audits test isolation to identify resource leakage patterns."""
    
    def __init__(self):
        self.initial_processes: Set[int] = set()
        self.initial_ports: Set[int] = set()
        self.initial_files: Set[Path] = set()
        
    def capture_baseline(self):
        """Capture system baseline before test execution."""
        self.initial_processes = set(proc.pid for proc in psutil.process_iter())
        self.initial_ports = self._get_bound_ports()
        self.initial_files = self._get_temp_files()
        
    def audit_leakage(self) -> Dict[str, List]:
        """Audit for resource leakage after test execution."""
        current_processes = set(proc.pid for proc in psutil.process_iter())
        current_ports = self._get_bound_ports() 
        current_files = self._get_temp_files()
        
        leaked_processes = current_processes - self.initial_processes
        leaked_ports = current_ports - self.initial_ports
        leaked_files = current_files - self.initial_files
        
        return {
            'processes': list(leaked_processes),
            'ports': list(leaked_ports),
            'files': [str(f) for f in leaked_files]
        }
        
    def _get_bound_ports(self) -> Set[int]:
        """Get all currently bound ports."""
        ports = set()
        try:
            for conn in psutil.net_connections():
                if conn.laddr:
                    ports.add(conn.laddr.port)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        return ports
        
    def _get_temp_files(self) -> Set[Path]:
        """Get relevant temporary files."""
        temp_dir = Path("/tmp")
        files = set()
        try:
            for pattern in ["headless_pm_mcp_*.json", "*.lock"]:
                files.update(temp_dir.glob(pattern))
        except Exception:
            pass
        return files


# Global auditor instance for cross-test tracking
auditor = TestIsolationAuditor()


@pytest.fixture(scope="function", autouse=True)
def audit_test_isolation(request):
    """Automatic test isolation audit for every test."""
    if request.function.__name__ == "test_baseline_capture":
        yield  # Must yield even when skipping audit
        return
        
    # Capture baseline before test
    test_id = f"{request.cls.__name__ if request.cls else 'NoClass'}::{request.function.__name__}"
    print(f"\n[AUDIT] Starting isolation audit for {test_id}")
    
    pre_audit = auditor.audit_leakage()
    
    yield
    
    # Check for leakage after test
    post_audit = auditor.audit_leakage()
    
    # Report any new leakage
    new_processes = set(post_audit['processes']) - set(pre_audit['processes'])
    new_ports = set(post_audit['ports']) - set(pre_audit['ports'])
    new_files = set(post_audit['files']) - set(pre_audit['files'])
    
    if new_processes or new_ports or new_files:
        print(f"[AUDIT] ❌ Resource leakage detected in {test_id}:")
        if new_processes:
            print(f"  Leaked processes: {new_processes}")
        if new_ports: 
            print(f"  Leaked ports: {new_ports}")
        if new_files:
            print(f"  Leaked files: {new_files}")
    else:
        print(f"[AUDIT] ✅ No resource leakage detected in {test_id}")


class TestIsolationAudit:
    """Test class to verify isolation audit functionality."""
    
    @classmethod
    def teardown_class(cls):
        """Class-level teardown with systematic process leak detection."""
        print(f"\n[CLASS TEARDOWN] Running leak detective for TestIsolationAudit")
        comprehensive_leak_detection("TestIsolationAudit")
    
    def test_baseline_capture(self):
        """Capture system baseline for audit comparisons."""
        auditor.capture_baseline()
        print(f"Baseline: {len(auditor.initial_processes)} processes, {len(auditor.initial_ports)} ports, {len(auditor.initial_files)} files")
        assert len(auditor.initial_processes) > 0  # Sanity check
        
    def test_no_leakage_example(self):
        """Example test that should not leak resources.""" 
        # This test doesn't create any resources
        x = 1 + 1
        assert x == 2
        
    def test_intentional_leakage_example(self):
        """Example test that intentionally leaks resources for audit verification."""
        # Create a subprocess that we "forget" to clean up
        proc = subprocess.Popen(['sleep', '1'])
        # Intentionally don't clean up to test audit detection
        time.sleep(0.1)  # Let process start
        
    def test_port_leakage_example(self):
        """Example test that leaks a port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', 0))  # Bind to random port
            sock.listen(1)
            # Intentionally don't close socket
            time.sleep(0.1)
        except Exception:
            pass  # Ignore binding errors for this example