"""
Instrumented version of test_api_functionality_with_http_client to capture concrete failure diagnostics.
This is for debugging the 10% intrinsic failure rate identified in statistical testing.
"""

import pytest
import asyncio
import subprocess
import sys
import os
import httpx
import psutil
import signal
import time
import json
from pathlib import Path
from datetime import datetime
from tests.process_tree_leak_detective import setup_process_tree_tracking, comprehensive_leak_detection

class TestMCPInstrumentedDiagnostics:
    """Instrumented diagnostics for MCP HTTP client test failures."""
    
    @pytest.fixture
    def diagnostic_logger(self):
        """Fixture to capture comprehensive diagnostics."""
        class DiagnosticLogger:
            def __init__(self):
                self.start_time = datetime.now()
                self.events = []
                self.system_state = {}
                
            def log_event(self, event_type: str, message: str, data: dict = None):
                """Log a diagnostic event with timestamp."""
                event = {
                    'timestamp': datetime.now().isoformat(),
                    'elapsed_ms': (datetime.now() - self.start_time).total_seconds() * 1000,
                    'event_type': event_type,
                    'message': message,
                    'data': data or {}
                }
                self.events.append(event)
                print(f"[DIAGNOSTIC] {event_type}: {message}")
                if data:
                    print(f"[DIAGNOSTIC] Data: {json.dumps(data, indent=2)}")
            
            def capture_system_state(self, label: str):
                """Capture comprehensive system state."""
                state = {
                    'label': label,
                    'timestamp': datetime.now().isoformat(),
                    'processes': [],
                    'ports': [],
                    'files': []
                }
                
                # Capture running processes
                try:
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
                        if any(keyword in ' '.join(proc.info['cmdline'] or []).lower() 
                               for keyword in ['python', 'uvicorn', 'src.main', 'mcp']):
                            state['processes'].append({
                                'pid': proc.pid,
                                'name': proc.info['name'],
                                'cmdline': proc.info['cmdline'],
                                'status': proc.info['status']
                            })
                except Exception as e:
                    state['process_error'] = str(e)
                
                # Capture bound ports
                try:
                    for conn in psutil.net_connections():
                        if conn.laddr and 6000 <= conn.laddr.port <= 10000:
                            state['ports'].append({
                                'port': conn.laddr.port,
                                'status': conn.status,
                                'pid': conn.pid
                            })
                except Exception as e:
                    state['port_error'] = str(e)
                
                # Capture relevant files
                try:
                    temp_files = list(Path('/tmp').glob('*mcp*')) + list(Path('/tmp').glob('*headless*'))
                    state['files'] = [str(f) for f in temp_files if f.exists()]
                except Exception as e:
                    state['file_error'] = str(e)
                
                self.system_state[label] = state
                self.log_event("SYSTEM_STATE", f"Captured state: {label}", state)
                
            def save_diagnostics(self, test_name: str, result: str):
                """Save complete diagnostics to file."""
                diagnostic_data = {
                    'test_name': test_name,
                    'start_time': self.start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'duration_ms': (datetime.now() - self.start_time).total_seconds() * 1000,
                    'result': result,
                    'events': self.events,
                    'system_states': self.system_state
                }
                
                filename = f"/tmp/test_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(diagnostic_data, f, indent=2)
                
                print(f"[DIAGNOSTIC] Saved complete diagnostics to {filename}")
                return filename
        
        return DiagnosticLogger()
    
    @pytest.fixture
    def server_manager(self):
        """Simple server manager for testing."""
        class ServerManager:
            def __init__(self):
                self.port = 6969
                self.started_processes = []
            
            def cleanup_process(self, process):
                """Clean up a process safely."""
                if process and process.poll() is None:
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
        
        return ServerManager()
    
    def ensure_no_api_running(self, server_manager, logger):
        """Ensure no API is running on the test port."""
        logger.log_event("CLEANUP", "Checking for existing API processes")
        
        # Check for processes on the port
        port_occupied = False
        occupying_pid = None
        try:
            for conn in psutil.net_connections():
                if conn.laddr and conn.laddr.port == server_manager.port:
                    port_occupied = True
                    occupying_pid = conn.pid
                    break
        except Exception as e:
            logger.log_event("ERROR", f"Failed to check port occupancy: {e}")
        
        if port_occupied:
            logger.log_event("WARNING", f"Port {server_manager.port} occupied by PID {occupying_pid}")
            
            # Try to kill the occupying process
            try:
                if occupying_pid:
                    proc = psutil.Process(occupying_pid)
                    proc.terminate()
                    proc.wait(timeout=3)
                    logger.log_event("CLEANUP", f"Terminated process {occupying_pid}")
            except Exception as e:
                logger.log_event("ERROR", f"Failed to kill occupying process: {e}")
        
        logger.log_event("CLEANUP", "API cleanup complete")
    
    async def is_api_running(self, server_manager, logger):
        """Check if API is running with detailed logging."""
        logger.log_event("CHECK", f"Testing API connectivity on port {server_manager.port}")
        
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"http://localhost:{server_manager.port}/health")
                running = response.status_code == 200
                logger.log_event("CHECK", f"API health check: {response.status_code}", {
                    'port': server_manager.port,
                    'status_code': response.status_code,
                    'running': running
                })
                return running
        except Exception as e:
            logger.log_event("ERROR", f"API health check failed: {e}", {
                'port': server_manager.port,
                'error': str(e),
                'error_type': type(e).__name__
            })
            return False
    
    @pytest.mark.asyncio
    async def test_instrumented_api_functionality_with_http_client(self, server_manager, diagnostic_logger):
        """Fully instrumented version of the failing test to capture concrete failure data."""
        
        logger = diagnostic_logger
        logger.log_event("START", f"Beginning instrumented test on port {server_manager.port}")
        logger.capture_system_state("pre_test")
        
        try:
            # Setup process tree tracking
            setup_process_tree_tracking()
            logger.log_event("SETUP", "Process tree tracking enabled")
            
            # Ensure clean start
            self.ensure_no_api_running(server_manager, logger)
            logger.capture_system_state("after_cleanup")
            
            # Start MCP server process with enhanced monitoring
            logger.log_event("START", "Starting MCP server process")
            
            # CRITICAL: Keep stdin open - MCP server's stdio_server() waits for stdin
            mcp_process = subprocess.Popen([
                sys.executable, "-m", "src.mcp.server"
            ],
            stdin=subprocess.PIPE,  # Keep stdin open to prevent immediate termination
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent.parent,
            env={**os.environ, "SERVICE_PORT": str(server_manager.port)}
            )
            
            logger.log_event("PROCESS", f"MCP process started", {
                'pid': mcp_process.pid,
                'port': server_manager.port
            })
            logger.capture_system_state("mcp_started")
            
            try:
                # Enhanced API startup monitoring
                api_started = False
                startup_attempts = 0
                startup_errors = []
                
                for attempt in range(30):
                    startup_attempts += 1
                    await asyncio.sleep(0.5)
                    
                    # Check process health
                    if mcp_process.poll() is not None:
                        stdout, stderr = mcp_process.communicate()
                        logger.log_event("CRITICAL", "MCP process died during startup", {
                            'exit_code': mcp_process.returncode,
                            'stdout': stdout[:500],
                            'stderr': stderr[:500],
                            'attempt': attempt
                        })
                        break
                    
                    # Test API connectivity
                    try:
                        running = await self.is_api_running(server_manager, logger)
                        if running:
                            api_started = True
                            logger.log_event("SUCCESS", f"API started after {startup_attempts} attempts")
                            break
                    except Exception as e:
                        startup_errors.append({
                            'attempt': attempt,
                            'error': str(e),
                            'error_type': type(e).__name__
                        })
                        if len(startup_errors) <= 3:  # Log first few errors
                            logger.log_event("RETRY", f"Startup attempt {attempt} failed: {e}")
                
                logger.capture_system_state("after_startup_attempts")
                
                if not api_started:
                    # Comprehensive failure diagnostics
                    stdout, stderr = None, None
                    if mcp_process.poll() is None:
                        mcp_process.terminate()
                        stdout, stderr = mcp_process.communicate(timeout=5)
                    
                    logger.log_event("FAILURE", "API startup failed", {
                        'startup_attempts': startup_attempts,
                        'process_exit_code': mcp_process.returncode,
                        'startup_errors': startup_errors,
                        'stdout': (stdout or '')[:1000],
                        'stderr': (stderr or '')[:1000]
                    })
                    
                    # Save diagnostics before assertion
                    diagnostic_file = logger.save_diagnostics("test_api_functionality_with_http_client", "STARTUP_FAILED")
                    
                    assert False, f"API startup failed after {startup_attempts} attempts. Diagnostics saved to {diagnostic_file}"
                
                # Test HTTP endpoints with detailed monitoring
                logger.log_event("TEST", "Testing HTTP endpoints")
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Test health endpoint
                    logger.log_event("HTTP", "Testing health endpoint")
                    try:
                        response = await client.get(f"http://localhost:{server_manager.port}/health")
                        logger.log_event("HTTP", "Health endpoint response", {
                            'status_code': response.status_code,
                            'content': response.text[:200]
                        })
                        assert response.status_code == 200, f"Health endpoint failed: {response.status_code}"
                    except Exception as e:
                        logger.log_event("ERROR", f"Health endpoint error: {e}")
                        raise
                    
                    # Test authenticated endpoints
                    headers = {"X-API-Key": "XXXXXX"}
                    authenticated_endpoints = [
                        ("context", f"http://localhost:{server_manager.port}/api/v1/context"),
                        ("agents", f"http://localhost:{server_manager.port}/api/v1/agents"),
                    ]
                    
                    for test_name, url in authenticated_endpoints:
                        logger.log_event("HTTP", f"Testing {test_name} endpoint")
                        try:
                            response = await client.get(url, headers=headers)
                            logger.log_event("HTTP", f"{test_name} endpoint response", {
                                'status_code': response.status_code,
                                'content': response.text[:200]
                            })
                            assert response.status_code == 200, f"{test_name} endpoint failed: {response.status_code}"
                        except Exception as e:
                            logger.log_event("ERROR", f"{test_name} endpoint error: {e}")
                            raise
                
                logger.log_event("SUCCESS", "All HTTP tests completed successfully")
                result = "PASSED"
                
            finally:
                # Enhanced cleanup with diagnostics
                logger.log_event("CLEANUP", "Starting process cleanup")
                logger.capture_system_state("before_cleanup")
                
                if mcp_process.poll() is None:
                    logger.log_event("CLEANUP", "Terminating MCP process")
                    mcp_process.terminate()
                    try:
                        mcp_process.wait(timeout=5)
                        logger.log_event("CLEANUP", "MCP process terminated gracefully")
                    except subprocess.TimeoutExpired:
                        logger.log_event("WARNING", "MCP process timeout, killing forcefully")
                        mcp_process.kill()
                        mcp_process.wait()
                
                self.ensure_no_api_running(server_manager, logger)
                logger.capture_system_state("after_cleanup")
                
                # Run leak detection
                try:
                    comprehensive_leak_detection("test_instrumented_api_functionality", {server_manager.port})
                    logger.log_event("LEAK_CHECK", "Process leak detection completed")
                except Exception as e:
                    logger.log_event("ERROR", f"Leak detection failed: {e}")
                
        except Exception as e:
            # Capture failure diagnostics
            logger.log_event("FAILURE", f"Test failed with exception: {e}", {
                'exception_type': type(e).__name__,
                'exception_message': str(e)
            })
            logger.capture_system_state("failure_state")
            
            # Save comprehensive diagnostics
            diagnostic_file = logger.save_diagnostics("test_api_functionality_with_http_client", "EXCEPTION_FAILED")
            print(f"\n=== FAILURE DIAGNOSTICS SAVED ===")
            print(f"File: {diagnostic_file}")
            print(f"Exception: {e}")
            
            result = "FAILED"
            raise
        else:
            # Save success diagnostics too for comparison
            diagnostic_file = logger.save_diagnostics("test_api_functionality_with_http_client", "PASSED")
            logger.log_event("COMPLETE", f"Test completed successfully, diagnostics saved to {diagnostic_file}")
            result = "PASSED"
    
    def ensure_no_api_running(self, server_manager, logger):
        """Enhanced cleanup with detailed logging."""
        logger.log_event("CLEANUP", f"Ensuring no API running on port {server_manager.port}")
        
        killed_processes = []
        
        # Kill processes by port
        try:
            for conn in psutil.net_connections():
                if conn.laddr and conn.laddr.port == server_manager.port and conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        proc_info = {
                            'pid': conn.pid,
                            'name': proc.name(),
                            'cmdline': ' '.join(proc.cmdline()[:3])  # First 3 args
                        }
                        proc.terminate()
                        killed_processes.append(proc_info)
                        logger.log_event("CLEANUP", f"Killed port-occupying process", proc_info)
                    except Exception as e:
                        logger.log_event("ERROR", f"Failed to kill process {conn.pid}: {e}")
        except Exception as e:
            logger.log_event("ERROR", f"Port cleanup error: {e}")
        
        # Kill processes by pattern
        pattern_killed = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = ' '.join(proc.info['cmdline'] or [])
                name = proc.info['name'] or ''
                
                if any(keyword in cmdline.lower() or keyword in name.lower() 
                       for keyword in ['uvicorn', 'src.main', 'src.mcp.server']) and proc.pid != os.getpid():
                    try:
                        proc_info = {
                            'pid': proc.pid,
                            'name': name,
                            'cmdline': cmdline[:100]  # Truncate long cmdlines
                        }
                        proc.terminate()
                        pattern_killed.append(proc_info)
                        logger.log_event("CLEANUP", "Killed pattern-matching process", proc_info)
                    except Exception as e:
                        logger.log_event("ERROR", f"Failed to kill process {proc.pid}: {e}")
        except Exception as e:
            logger.log_event("ERROR", f"Pattern cleanup error: {e}")
        
        if killed_processes or pattern_killed:
            time.sleep(1)  # Wait for cleanup
            logger.log_event("CLEANUP", f"Cleanup complete: {len(killed_processes)} port-based, {len(pattern_killed)} pattern-based")

    async def is_api_running(self, server_manager, logger):
        """Enhanced API check with detailed logging."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"http://localhost:{server_manager.port}/health")
                running = response.status_code == 200
                
                logger.log_event("CHECK", f"API health check result", {
                    'port': server_manager.port,
                    'status_code': response.status_code,
                    'response_time_ms': response.elapsed.total_seconds() * 1000 if hasattr(response, 'elapsed') else None,
                    'running': running
                })
                return running
        except Exception as e:
            logger.log_event("CHECK", f"API health check exception: {e}", {
                'port': server_manager.port,
                'error_type': type(e).__name__,
                'error_message': str(e)
            })
            return False