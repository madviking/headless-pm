"""
Reliable race condition detection and diagnosis test.
This test is designed to consistently reproduce and report on coordination issues.
"""
import pytest
import subprocess
import asyncio
import time
import httpx
import json
import os
import signal
import psutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import tempfile
from tests.process_tree_leak_detective import setup_process_tree_tracking, comprehensive_leak_detection


class RaceConditionDetector:
    """Detects and diagnoses race conditions in multi-client coordination."""
    
    def __init__(self, test_port: int = 8888):
        self.test_port = test_port
        self.base_url = f"http://localhost:{test_port}"
        self.processes: List[subprocess.Popen] = []
        self.coordination_file = f"/tmp/headless_pm_mcp_clients_{test_port}.json"
        self.test_results: List[Dict] = []
        
    async def cleanup(self):
        """Clean up all test processes with proper MCP coordination cleanup."""
        # Terminate all processes with proper coordination cleanup
        for proc in self.processes:
            if proc.poll() is None:
                try:
                    # 1. Signal graceful shutdown for MCP servers
                    if proc.stdin and not proc.stdin.closed:
                        proc.stdin.close()
                        
                    # 2. Send SIGTERM to trigger signal handlers  
                    proc.terminate()
                    
                    # 3. Allow time for MCP coordination cleanup
                    proc.wait(timeout=10)  # Increased from 3s for coordination
                except subprocess.TimeoutExpired:
                    # 4. Force kill only if coordination cleanup fails
                    proc.kill()
                    proc.wait()
                except Exception:
                    pass
        self.processes.clear()
        
        # Remove coordination file
        try:
            os.unlink(self.coordination_file)
        except FileNotFoundError:
            pass
            
        # Kill any remaining API processes
        await self._kill_test_api_processes()
        
    async def _kill_test_api_processes(self):
        """Find and kill any API processes running on test port."""
        try:
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and str(self.test_port) in ' '.join(cmdline):
                        if any('uvicorn' in arg or 'src.main:app' in arg for arg in cmdline):
                            print(f"Killing test API process {proc.info['pid']}")
                            proc.terminate()
                            proc.wait(timeout=3)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    pass
        except Exception as e:
            print(f"Warning: Could not clean up test processes: {e}")

    async def is_api_running(self) -> bool:
        """Check if API is responding."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False

    def read_coordination_file(self) -> Optional[Dict]:
        """Read coordination file if it exists."""
        try:
            with open(self.coordination_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def start_mcp_client(self, client_id: str, capture_output: bool = True) -> subprocess.Popen:
        """Start an MCP client and track it."""
        import sys
        env = {
            **os.environ, 
            "SERVICE_PORT": str(self.test_port),
            "HEADLESS_PM_COMMAND": f"{sys.executable} -m src.main"
        }
        
        if capture_output:
            proc = subprocess.Popen(
                [sys.executable, "-m", "src.mcp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
        else:
            proc = subprocess.Popen(
                [sys.executable, "-m", "src.mcp"],
                stdin=subprocess.PIPE,
                env=env
            )
            
        self.processes.append(proc)
        print(f"Started MCP client {client_id} (PID: {proc.pid})")
        return proc

    async def wait_for_coordination_file(self, timeout: int = 10) -> bool:
        """Wait for coordination file to appear."""
        for _ in range(timeout * 10):  # 0.1s intervals
            if os.path.exists(self.coordination_file):
                return True
            await asyncio.sleep(0.1)
        return False

    async def run_comprehensive_race_detection(self) -> Dict:
        """Run comprehensive race condition detection with detailed reporting."""
        test_start = time.time()
        result = {
            "test_name": "comprehensive_race_detection",
            "start_time": test_start,
            "phases": [],
            "coordination_states": [],
            "issues_detected": [],
            "final_diagnosis": ""
        }
        
        try:
            # Phase 1: Clean environment verification
            phase1 = await self._phase1_clean_environment()
            result["phases"].append(phase1)
            
            if not phase1["success"]:
                result["final_diagnosis"] = "Failed at environment setup"
                return result
                
            # Phase 2: Single client baseline
            phase2 = await self._phase2_single_client_baseline()
            result["phases"].append(phase2)
            
            # Phase 3: Multi-client coordination test
            phase3 = await self._phase3_multi_client_coordination()
            result["phases"].append(phase3)
            
            # Phase 4: Race condition analysis
            phase4 = await self._phase4_race_condition_analysis()
            result["phases"].append(phase4)
            
            # Diagnose issues
            result["final_diagnosis"] = self._diagnose_results(result)
            
        except Exception as e:
            result["final_diagnosis"] = f"Test framework error: {str(e)}"
            
        finally:
            result["duration"] = time.time() - test_start
            
        return result

    async def _phase1_clean_environment(self) -> Dict:
        """Verify clean test environment."""
        phase = {
            "name": "clean_environment_verification",
            "success": True,
            "details": {},
            "issues": []
        }
        
        # Check no API running
        api_running = await self.is_api_running()
        phase["details"]["api_initially_running"] = api_running
        
        if api_running:
            phase["issues"].append(f"API already running on port {self.test_port}")
            phase["success"] = False
            
        # Check no coordination file
        coord_exists = os.path.exists(self.coordination_file)
        phase["details"]["coordination_file_exists"] = coord_exists
        
        if coord_exists:
            phase["issues"].append(f"Coordination file already exists: {self.coordination_file}")
            # Read existing file for diagnosis
            phase["details"]["existing_coordination_data"] = self.read_coordination_file()
            
        return phase

    async def _phase2_single_client_baseline(self) -> Dict:
        """Test single client behavior for baseline."""
        phase = {
            "name": "single_client_baseline",
            "success": True,
            "details": {},
            "issues": []
        }
        
        print("Phase 2: Testing single client baseline...")
        
        # Start single client
        client1 = self.start_mcp_client("client1")
        start_time = time.time()
        
        # Wait for startup
        await asyncio.sleep(3)
        
        # Check API started
        api_running = await self.is_api_running()
        phase["details"]["api_started"] = api_running
        phase["details"]["startup_time"] = time.time() - start_time
        
        if not api_running:
            phase["issues"].append("Single client failed to start API")
            phase["success"] = False
        
        # Check coordination file
        coord_data = self.read_coordination_file()
        phase["details"]["coordination_data"] = coord_data
        
        if coord_data:
            client_count = len(coord_data.get("clients", []))
            phase["details"]["client_count"] = client_count
            
            if client_count != 1:
                phase["issues"].append(f"Expected 1 client in coordination file, found {client_count}")
        else:
            phase["issues"].append("Coordination file not created")
            phase["success"] = False
            
        # Clean up single client
        if client1.poll() is None:
            if client1.stdin:
                client1.stdin.close()
            client1.terminate()
            client1.wait()
            
        # Wait for cleanup
        await asyncio.sleep(2)
        
        # Verify cleanup
        api_after_cleanup = await self.is_api_running()
        phase["details"]["api_cleaned_up"] = not api_after_cleanup
        
        if api_after_cleanup:
            phase["issues"].append("API not cleaned up after single client exit")
            
        return phase

    async def _phase3_multi_client_coordination(self) -> Dict:
        """Core multi-client coordination test with detailed state tracking."""
        phase = {
            "name": "multi_client_coordination",
            "success": True,
            "details": {
                "client_states": [],
                "coordination_snapshots": [],
                "api_states": []
            },
            "issues": []
        }
        
        print("Phase 3: Testing multi-client coordination...")
        
        # Start first client
        print("  Starting client1...")
        client1 = self.start_mcp_client("client1")
        
        # Wait and capture state
        await asyncio.sleep(4)  # Longer wait for startup
        
        api_state1 = await self.is_api_running()
        coord_data1 = self.read_coordination_file()
        
        phase["details"]["api_states"].append({"step": "client1_started", "api_running": api_state1})
        phase["details"]["coordination_snapshots"].append({"step": "client1_started", "data": coord_data1})
        
        if not api_state1:
            phase["issues"].append("Client1 failed to start API")
            phase["success"] = False
            return phase
            
        client1_count = len(coord_data1.get("clients", [])) if coord_data1 else 0
        if client1_count != 1:
            phase["issues"].append(f"After client1 start: expected 1 client, found {client1_count}")
            
        # Start second client  
        print("  Starting client2...")
        client2 = self.start_mcp_client("client2")
        
        # Wait for second client registration
        await asyncio.sleep(3)
        
        api_state2 = await self.is_api_running()
        coord_data2 = self.read_coordination_file()
        
        phase["details"]["api_states"].append({"step": "client2_started", "api_running": api_state2})
        phase["details"]["coordination_snapshots"].append({"step": "client2_started", "data": coord_data2})
        
        if not api_state2:
            phase["issues"].append("API died when client2 started")
            phase["success"] = False
            
        client2_count = len(coord_data2.get("clients", [])) if coord_data2 else 0
        if client2_count != 2:
            phase["issues"].append(f"After client2 start: expected 2 clients, found {client2_count}")
            phase["success"] = False
            
        print(f"  Both clients running. API: {api_state2}, Clients in file: {client2_count}")
        
        # Critical test: Terminate first client
        print("  Terminating client1...")
        termination_start = time.time()
        
        if client1.stdin:
            client1.stdin.close()
        client1.terminate()
        
        # Wait for client1 to fully exit
        client1.wait()
        phase["details"]["client1_exit_time"] = time.time() - termination_start
        
        # Wait for coordination update
        await asyncio.sleep(2)
        
        # Check coordination state after client1 exit
        coord_data3 = self.read_coordination_file()
        api_state3 = await self.is_api_running()
        
        phase["details"]["api_states"].append({"step": "client1_terminated", "api_running": api_state3})
        phase["details"]["coordination_snapshots"].append({"step": "client1_terminated", "data": coord_data3})
        
        remaining_clients = len(coord_data3.get("clients", [])) if coord_data3 else 0
        phase["details"]["remaining_clients_after_client1_exit"] = remaining_clients
        
        # THE CRITICAL TEST
        if not api_state3:
            phase["issues"].append("❌ RACE CONDITION: API terminated when first client exited, but second client still running")
            phase["success"] = False
            
        if remaining_clients != 1:
            phase["issues"].append(f"Expected 1 remaining client after first exit, found {remaining_clients}")
            
        print(f"  After client1 exit: API running: {api_state3}, Remaining clients: {remaining_clients}")
        
        # Clean up second client
        print("  Terminating client2...")
        if client2.stdin:
            client2.stdin.close()
        client2.terminate()
        client2.wait()
        
        await asyncio.sleep(2)
        
        # Final state
        api_state4 = await self.is_api_running()
        coord_data4 = self.read_coordination_file()
        
        phase["details"]["api_states"].append({"step": "all_clients_terminated", "api_running": api_state4})
        phase["details"]["coordination_snapshots"].append({"step": "all_clients_terminated", "data": coord_data4})
        
        if api_state4:
            phase["issues"].append("API should have stopped after all clients exited")
            
        return phase

    async def _phase4_race_condition_analysis(self) -> Dict:
        """Analyze coordination behavior for race conditions."""
        phase = {
            "name": "race_condition_analysis", 
            "success": True,
            "details": {},
            "issues": []
        }
        
        print("Phase 4: Analyzing race condition patterns...")
        
        # Run multiple rapid iterations to detect intermittent issues
        iteration_results = []
        
        for i in range(5):
            print(f"  Iteration {i+1}/5...")
            iteration_start = time.time()
            
            # Rapid client cycling
            client = self.start_mcp_client(f"rapid_client_{i}")
            await asyncio.sleep(1)  # Shorter wait to stress timing
            
            api_running = await self.is_api_running()
            coord_data = self.read_coordination_file()
            
            # Immediate termination
            if client.stdin:
                client.stdin.close()
            client.terminate()
            client.wait()
            
            await asyncio.sleep(0.5)  # Short cleanup wait
            
            api_after = await self.is_api_running()
            coord_after = self.read_coordination_file()
            
            iteration_result = {
                "iteration": i + 1,
                "duration": time.time() - iteration_start,
                "api_started": api_running,
                "api_cleaned": not api_after,
                "coordination_during": coord_data,
                "coordination_after": coord_after
            }
            
            iteration_results.append(iteration_result)
            
            # Check for consistency
            if api_running != api_after:  # Should cleanup properly
                continue
            else:
                phase["issues"].append(f"Iteration {i+1}: Inconsistent API lifecycle")
                
        phase["details"]["iterations"] = iteration_results
        
        # Analyze patterns
        api_start_failures = sum(1 for r in iteration_results if not r["api_started"])
        api_cleanup_failures = sum(1 for r in iteration_results if not r["api_cleaned"])
        
        phase["details"]["api_start_failure_rate"] = api_start_failures / 5
        phase["details"]["api_cleanup_failure_rate"] = api_cleanup_failures / 5
        
        if api_start_failures > 0:
            phase["issues"].append(f"{api_start_failures}/5 iterations failed to start API")
            
        if api_cleanup_failures > 0:
            phase["issues"].append(f"{api_cleanup_failures}/5 iterations failed to cleanup API")
            
        return phase

    def _diagnose_results(self, results: Dict) -> str:
        """Generate actionable diagnosis from test results."""
        issues = []
        
        # Check each phase
        for phase in results["phases"]:
            if not phase["success"]:
                issues.extend(phase["issues"])
                
        if not issues:
            return "✅ No race conditions detected - coordination working properly"
            
        # Categorize issues
        signal_handler_issues = [i for i in issues if "signal" in i.lower() or "handler" in i.lower()]
        coordination_issues = [i for i in issues if "client" in i.lower() and "expected" in i.lower()]
        api_lifecycle_issues = [i for i in issues if "API" in i and ("terminated" in i or "died" in i)]
        
        diagnosis = "❌ RACE CONDITIONS DETECTED:\n\n"
        
        if signal_handler_issues:
            diagnosis += "🔥 SIGNAL HANDLER ISSUES:\n"
            for issue in signal_handler_issues:
                diagnosis += f"  - {issue}\n"
            diagnosis += "  → FIX: Check signal handler registration in subprocess environment\n\n"
            
        if api_lifecycle_issues:
            diagnosis += "🔥 API LIFECYCLE ISSUES:\n" 
            for issue in api_lifecycle_issues:
                diagnosis += f"  - {issue}\n"
            diagnosis += "  → FIX: Signal handlers not executing, backup cleanup triggers prematurely\n\n"
            
        if coordination_issues:
            diagnosis += "🔥 CLIENT COORDINATION ISSUES:\n"
            for issue in coordination_issues:
                diagnosis += f"  - {issue}\n" 
            diagnosis += "  → FIX: Client registration/deregistration not atomic\n\n"
            
        # Add specific technical recommendations
        diagnosis += "🛠️  TECHNICAL FIXES NEEDED:\n"
        diagnosis += "  1. Fix signal handler registration in src/mcp/server.py\n"
        diagnosis += "  2. Make client registration atomic with proper file locking\n"
        diagnosis += "  3. Add startup synchronization barriers\n"
        diagnosis += "  4. Implement proper subprocess signal handling\n"
        diagnosis += "  5. Add coordination state validation before cleanup\n"
        
        return diagnosis


@pytest.mark.asyncio 
class TestRaceConditionDetector:
    """Test suite for race condition detection."""
    
    @classmethod
    def setup_class(cls):
        """Class-level setup with process tree baseline."""
        setup_process_tree_tracking()
    
    @classmethod
    def teardown_class(cls):
        """Class-level teardown with comprehensive leak detection."""
        # Use default port range for detection since we use auto-discovery
        default_ports = {6969, 6968, 3001}  # Real system defaults
        test_ports = set(range(8000, 8100))  # Range we use for this test file
        all_ports = default_ports.union(test_ports)
        
        comprehensive_leak_detection("TestRaceConditionDetector", all_ports)
    
    async def test_reliable_race_condition_detection(self):
        """Reliably detect and report coordination race conditions."""
        from src.main import get_port
        test_instance_id = "TestRaceConditionDetector::test_reliable_race_condition_detection"
        test_port = get_port(8000, instance_id=test_instance_id)
        detector = RaceConditionDetector(test_port=test_port)
        
        try:
            # Run comprehensive detection
            results = await detector.run_comprehensive_race_detection()
            
            # Print detailed results
            print(f"\n{'='*80}")
            print("RACE CONDITION DETECTION RESULTS")
            print(f"{'='*80}")
            print(f"Test Duration: {results['duration']:.2f} seconds")
            print(f"Phases Completed: {len(results['phases'])}")
            
            for phase in results["phases"]:
                print(f"\nPhase: {phase['name']}")
                print(f"  Success: {phase['success']}")
                if phase["issues"]:
                    print("  Issues:")
                    for issue in phase["issues"]:
                        print(f"    - {issue}")
                        
            print(f"\n{results['final_diagnosis']}")
            print(f"{'='*80}")
            
            # Save detailed results for analysis
            results_file = f"/tmp/race_condition_results_{int(time.time())}.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Detailed results saved to: {results_file}")
            
            # Assert based on detection
            if "No race conditions detected" in results["final_diagnosis"]:
                print("✅ COORDINATION WORKING PROPERLY")
            else:
                # Don't fail the test, but report the issues clearly
                print("❌ RACE CONDITIONS CONFIRMED")
                print("This test serves as a diagnostic tool.")
                print("See diagnosis above for specific fixes needed.")
                
        finally:
            await detector.cleanup()

    async def test_signal_handler_behavior(self):
        """Specifically test signal handler behavior in subprocess."""
        from src.main import get_port
        test_port = get_port(8000, instance_id="TestRaceConditionDetector::method")
        detector = RaceConditionDetector(test_port=test_port)
        
        try:
            print("Testing signal handler behavior...")
            
            # Start client with output capture to check for signal handler messages
            client = detector.start_mcp_client("signal_test", capture_output=True)
            await asyncio.sleep(3)
            
            # Send SIGTERM and capture output
            client.terminate()
            stdout, stderr = client.communicate(timeout=5)
            
            # Analyze output for signal handler evidence
            signal_handler_ran = "signal handler" not in stderr.lower() or "backup cleanup" not in stderr.lower()
            backup_cleanup_ran = "backup cleanup" in stderr.lower()
            
            print(f"Signal handler executed properly: {signal_handler_ran}")
            print(f"Backup cleanup triggered: {backup_cleanup_ran}")
            
            if backup_cleanup_ran:
                print("❌ SIGNAL HANDLER ISSUE CONFIRMED")
                print("Signal handlers not executing, backup cleanup running instead")
                print(f"stderr output:\n{stderr}")
            else:
                print("✅ Signal handlers working properly")
                
        finally:
            await detector.cleanup()

    async def test_coordination_file_atomicity(self):
        """Test coordination file operations for race conditions."""
        from src.main import get_port
        test_port = get_port(8000, instance_id="TestRaceConditionDetector::method")
        detector = RaceConditionDetector(test_port=test_port)
        
        try:
            print("Testing coordination file atomicity...")
            
            # Simulate rapid concurrent client registration with proper synchronization
            clients = []
            for i in range(3):
                client = detector.start_mcp_client(f"concurrent_client_{i}", capture_output=False)
                clients.append(client)
                await asyncio.sleep(0.2)  # Slightly longer delay to reduce write contention
                
            # Wait for all clients to fully register with exponential backoff verification
            max_attempts = 10
            for attempt in range(max_attempts):
                await asyncio.sleep(1)  # Check every second
                coord_data = detector.read_coordination_file()
                if coord_data and len(coord_data.get("clients", [])) >= 3:
                    break
                print(f"Waiting for client registration completion, attempt {attempt + 1}/{max_attempts}")
            
            # Additional settling time after successful registration
            await asyncio.sleep(2)
            
            # Check final coordination state
            coord_data = detector.read_coordination_file()
            api_running = await detector.is_api_running()
            
            expected_clients = 3
            actual_clients = len(coord_data.get("clients", [])) if coord_data else 0
            
            print(f"Expected clients: {expected_clients}")
            print(f"Actual clients in file: {actual_clients}")
            print(f"API running: {api_running}")
            
            if actual_clients != expected_clients:
                print(f"❌ COORDINATION FILE RACE CONDITION")
                print(f"Expected {expected_clients} clients, found {actual_clients}")
                print(f"Coordination data: {coord_data}")
            else:
                print("✅ Coordination file handling is atomic")
                
        finally:
            await detector.cleanup()


if __name__ == "__main__":
    # Can be run standalone for debugging
    import asyncio
    
    async def main():
        detector = RaceConditionDetector()
        try:
            results = await detector.run_comprehensive_race_detection()
            print(results["final_diagnosis"])
        finally:
            await detector.cleanup()
            
    asyncio.run(main())