"""
Test helper utilities for robust server management in tests.
Uses real system port allocation (src.main.get_port) for consistency.
"""

import subprocess
import time
import httpx
import asyncio
import psutil
from pathlib import Path
from typing import Optional, List, Set
from contextlib import asynccontextmanager


class ServerManager:
    """Manages test servers with proper cleanup and existing server handling."""
    
    def __init__(self, port: int = 6969):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.started_processes: List[subprocess.Popen] = []
        self.existing_api_pid: Optional[int] = None
        self.project_root = Path(__file__).parent.parent
        
    async def is_api_running(self) -> bool:
        """Check if API is responding."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
    
    def find_api_process(self) -> Optional[int]:
        """Find existing API process on the port."""
        try:
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and str(self.port) in ' '.join(cmdline):
                        # Check if it's a uvicorn/API process
                        if any('uvicorn' in arg or 'src.main:app' in arg for arg in cmdline):
                            return proc.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        return None
    
    async def record_existing_state(self):
        """Record existing server state before test."""
        self.existing_api_pid = self.find_api_process()
        if self.existing_api_pid:
            print(f"Found existing API server on port {self.port} (PID: {self.existing_api_pid})")
    
    def start_mcp_client(self, env: dict = None, wait: bool = True) -> subprocess.Popen:
        """Start an MCP client process and track it."""
        import sys
        import os
        
        if env is None:
            env = {}

        # Add project root to PYTHONPATH to ensure modules are found by the subprocess
        python_path = os.environ.get("PYTHONPATH", "")
        project_root_str = str(self.project_root)
        if project_root_str not in python_path.split(os.pathsep):
            python_path = f"{project_root_str}{os.pathsep}{python_path}"
        
        full_env = {
            **os.environ, 
            "SERVICE_PORT": str(self.port), 
            "PYTHONPATH": python_path,
            **env
        }
        
        # MCP server expects to run as stdio server, so we need to provide stdin
        # to keep it running. We use PIPE for stdin so the process doesn't exit.
        proc = subprocess.Popen(
            [sys.executable, "-m", "src.mcp.server"],
            stdin=subprocess.PIPE,  # Important: MCP server needs stdin to stay alive
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=full_env
        )
        
        self.started_processes.append(proc)
        
        if wait:
            time.sleep(3)  # Give it time to start
            
        return proc
    
    async def wait_for_api(self, timeout: int = 30) -> bool:
        """Wait for API to become available."""
        for _ in range(timeout):
            if await self.is_api_running():
                return True
            await asyncio.sleep(1)
        return False

    def cleanup_process(self, proc: subprocess.Popen):
        """Safely cleanup a single process with proper coordination cleanup time."""
        if proc.poll() is None:  # Process still running
            try:
                # 1. Close stdin first to signal graceful shutdown for MCP servers
                if proc.stdin and not proc.stdin.closed:
                    proc.stdin.close()
                    
                # 2. Send SIGTERM to trigger signal handlers
                proc.terminate()
                
                # 3. Allow time for MCP coordination cleanup (increased timeout)
                proc.wait(timeout=10)  # Increased from 5s for coordination
            except subprocess.TimeoutExpired:
                # 4. Force kill only if coordination cleanup times out
                proc.kill()
                proc.wait()
            except Exception:
                pass
    
    async def cleanup(self):
        """Clean up only what this test created and wait for port release."""
        # First, terminate all MCP clients we started
        for proc in self.started_processes:
            self.cleanup_process(proc)
        
        self.started_processes.clear()
        
        # Give processes time to clean themselves up
        await asyncio.sleep(2)
        
        # Check if API is still running
        current_api_pid = self.find_api_process()
        
        # Only kill the API if:
        # 1. We didn't find an existing API at start, AND
        # 2. There's an API running now
        if self.existing_api_pid is None and current_api_pid is not None:
            print(f"Cleaning up test-created API server (PID: {current_api_pid})")
            try:
                proc = psutil.Process(current_api_pid)
                proc.terminate()
                proc.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                pass
        elif self.existing_api_pid and current_api_pid == self.existing_api_pid:
            print(f"Preserving pre-existing API server (PID: {self.existing_api_pid})")

        # Actively wait for the port to become free
        for i in range(10): # Wait up to 2.5 seconds
            if not await self.is_api_running():
                print(f"Port {self.port} confirmed free after cleanup.")
                return
            await asyncio.sleep(0.25)
        print(f"Warning: Port {self.port} did not become free after cleanup.")
    
    @asynccontextmanager
    async def test_context(self):
        """Context manager for test execution with automatic cleanup."""
        await self.record_existing_state()
        try:
            yield self
        finally:
            await self.cleanup()


class MultiClientTestHelper:
    """Helper for multi-client coordination tests."""
    
    def __init__(self, port: int = 6969):
        self.manager = ServerManager(port)
        
    async def test_multi_client_coordination(self) -> bool:
        """Test multi-client coordination with proper cleanup.
        
        Returns True if test passes, False otherwise.
        """
        async with self.manager.test_context():
            # Check initial state
            api_was_running = await self.manager.is_api_running()
            
            if api_was_running:
                print(f"Note: API already running on port {self.manager.port}")
                # For this test, we need a clean slate
                return False  # Skip test if API already running
            
            # Start first MCP client (should start API)
            print("Starting first MCP client...")
            proc1 = self.manager.start_mcp_client(wait=False)
            
            # Wait for API to start
            if not await self.manager.wait_for_api(timeout=15):
                print("API failed to start from first client")
                return False
            
            print("✓ First client started API")
            
            # Start second MCP client (should connect to existing)
            print("Starting second MCP client...")
            proc2 = self.manager.start_mcp_client()
            
            # Verify API still running
            if not await self.manager.is_api_running():
                print("API died when second client connected")
                return False
            
            print("✓ Two clients connected")
            
            # Terminate first client
            print("Terminating first client...")
            self.manager.cleanup_process(proc1)
            await asyncio.sleep(2)
            
            # Check if API still running (should be, due to second client)
            if not await self.manager.is_api_running():
                print("❌ API died when first client exited (coordination bug)")
                return False
            
            print("✓ API survived first client exit")
            
            # Terminate second client
            print("Terminating second client...")
            self.manager.cleanup_process(proc2)
            await asyncio.sleep(2)
            
            # API should stop now (no clients left)
            if await self.manager.is_api_running():
                # This might be OK if there was a pre-existing server
                if not api_was_running:
                    print("⚠️ API still running after all clients exited")
                    return False
            
            print("✓ API stopped after all clients exited")
            return True


# For backwards compatibility
async def is_api_running(port: int = 6969) -> bool:
    """Check if API is running on given port."""
    manager = ServerManager(port)
    return await manager.is_api_running()


def ensure_clean_state(port: int = 6969):
    """Ensure no test servers running (for test setup)."""
    manager = ServerManager(port)
    current_pid = manager.find_api_process()
    
    if current_pid:
        print(f"Warning: Found existing API on port {port} (PID: {current_pid})")
        print("Consider using a different port for testing or stopping the server")
        return False
    return True


import os  # Add at top of file