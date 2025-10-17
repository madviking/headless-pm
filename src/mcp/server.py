"""
Headless PM MCP Server - Model Context Protocol server for Headless PM integration
Provides standardized interface for Claude Code and other MCP clients.

Environment Variables:
    HEADLESS_PM_COMMAND: Full command to start HeadlessPM (overrides all discovery)
    HEADLESS_PM_DIR: Project/working directory for HeadlessPM
    HEADLESS_PM_NO_AUTOSTART: Skip auto-start, connection-only mode (any non-empty value)
    HEADLESS_PM_URL: API base URL (overrides default, e.g., http://localhost:6969)
    SERVICE_PORT: HeadlessPM API port (default: 6969)

Design Principles:
    1. Connection-first: Try existing API before starting new process
    2. Smart discovery: Prioritize same Python interpreter for consistency
    3. Simple configuration: Minimal, non-redundant environment variables
    4. Context preservation: Respect user's working directory when possible

Example Usage:
    # Connection-only mode
    HEADLESS_PM_NO_AUTOSTART=1 headless-pm-mcp

    # Override discovery with specific command
    HEADLESS_PM_COMMAND="uv run headless-pm" headless-pm-mcp

    # Run in specific directory
    HEADLESS_PM_DIR=/path/to/project headless-pm-mcp
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import httpx

# Configure logging first (needed for import error messages)
logging.basicConfig(level=logging.INFO, format='[MCP] %(message)s')
logger = logging.getLogger("headless-pm-mcp")

# Import atomic file operations utility (handle both relative and absolute imports)
try:
    from ..utils.atomic_file_ops import AtomicFileOperations, with_coordination_lock
except ImportError:
    from src.utils.atomic_file_ops import AtomicFileOperations, with_coordination_lock

# Optional psutil import for process management (graceful fallback if missing)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    logger.warning("psutil not available - process discovery and cleanup features disabled")
    HAS_PSUTIL = False
    # Create minimal psutil mock for graceful degradation
    class psutil:
        @staticmethod
        def process_iter(*args):
            return []
        @staticmethod 
        def pid_exists(pid):
            return False
        class Process:
            def __init__(self, pid=None): pass
            def create_time(self): return time.time()
            def cmdline(self): return []

# Cross-platform file locking
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    # Windows doesn't have fcntl, use msvcrt or simple fallback
    HAS_FCNTL = False
    try:
        import msvcrt
        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.server.lowlevel.server import NotificationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    ReadResourceRequest,
    ReadResourceResult,
    Resource,
    TextContent,
    Tool,
    EmbeddedResource,
)
try:
    from .token_tracker import TokenTracker
except ImportError:
    # Handle case where this is run as a standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from token_tracker import TokenTracker

# Logging already configured at top of file

# Note: Rate limiting now uses file-based coordination only (no global state)


class HeadlessPMMCPServer:
    """MCP Server for Headless PM integration."""

    def __init__(self, base_url: str = None):
        # Construct base_url - defer port discovery to avoid subprocess issues
        if base_url is None:
            # Simple port resolution without auto-discovery for MCP server
            service_port = os.getenv('SERVICE_PORT', '6969')
            base_url = f"http://localhost:{service_port}"
        # Prioritize HEADLESS_PM_URL env var, then constructed/provided base_url
        self.base_url = (os.getenv('HEADLESS_PM_URL') or base_url).rstrip('/')
        self.server = Server("headless-pm")
        # Create client with API key header
        api_key = os.getenv("API_KEY_HEADLESS_PM", "XXXXXX")
        self.client = httpx.AsyncClient(timeout=30.0, headers={"X-API-Key": api_key})
        self.agent_id: Optional[str] = None
        self.agent_role: Optional[str] = None
        self.agent_skill_level: Optional[str] = None
        self.token_tracker = TokenTracker()
        self._api_process: Optional[subprocess.Popen] = None
        self._api_server_pid: Optional[int] = None  # Track actual server process PID
        self._api_server_start_time: Optional[float] = None  # Track process creation time
        self._we_started_api = False  # Track whether WE started the API process
        import random
        self._client_id = f"mcp_{os.getpid()}_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"  # More unique client identifier
        self._shutdown_requested = asyncio.Event()

        # Register handlers
        self._register_handlers()
        
        # Set up signal handlers for graceful shutdown (asyncio-compatible)
        try:
            loop = asyncio.get_event_loop()
            loop.add_signal_handler(signal.SIGTERM, self._handle_shutdown_signal)
            loop.add_signal_handler(signal.SIGINT, self._handle_shutdown_signal)
        except (RuntimeError, NotImplementedError):
            # Signal handling not available (Windows or no event loop)
            pass

    def _handle_shutdown_signal(self):
        """Handle shutdown signals (SIGTERM, SIGINT)."""
        logger.info("Received shutdown signal, initiating graceful shutdown...")
        self._shutdown_requested.set()

    async def _perform_cleanup(self):
        """Perform cleanup of API process using reference counting coordination."""
        # Prevent multiple concurrent cleanup calls
        if hasattr(self, '_cleanup_in_progress') and self._cleanup_in_progress:
            logger.info("Cleanup already in progress, skipping...")
            return

        # Mark cleanup as in progress
        self._cleanup_in_progress = True
        
        try:
            # Unregister this MCP client and check if we should cleanup API
            should_cleanup_api = self._unregister_mcp_client()
            
            if not should_cleanup_api:
                logger.info("Other MCP clients still active, leaving API running")
                return
            
            # Only clean up APIs that we actually started
            # Don't clean up pre-existing APIs that we just connected to
            if not self._we_started_api:
                logger.info("API was not started by this MCP client, leaving it running")
                return
                
            if not self._api_server_pid:
                logger.info("No API process PID tracked, cannot clean up")
                return

            cleanup_pid = self._api_server_pid  # Capture PID in case it changes
            
            logger.info(f"Last MCP client - cleaning up API process (PID: {cleanup_pid})...")

            # Terminate the API server process (we're the last client)
            try:
                server_process = psutil.Process(cleanup_pid)
                
                # Validate process identity using creation time to prevent PID reuse attacks
                current_create_time = server_process.create_time()
                if self._api_server_start_time and abs(current_create_time - self._api_server_start_time) > 1.0:
                    logger.warning(f"Process {cleanup_pid} creation time mismatch - possible PID reuse! "
                                 f"Expected: {self._api_server_start_time}, Found: {current_create_time}")
                    logger.warning("Skipping termination to prevent killing wrong process")
                    return
                
                # Verify this is still a server process before terminating
                cmdline = server_process.cmdline()
                if not any('uvicorn' in str(arg) or 'src.main' in str(arg) for arg in cmdline):
                    logger.warning(f"PID {cleanup_pid} doesn't appear to be a server process, skipping termination")
                    return
                
                logger.info(f"Terminating API server process (PID: {cleanup_pid})...")
                server_process.terminate()
                
                # Wait for graceful termination
                try:
                    server_process.wait(timeout=5)
                    logger.info("✅ HeadlessPM API process terminated gracefully")
                except psutil.TimeoutExpired:
                    logger.warning("API process did not stop gracefully, forcing shutdown...")
                    try:
                        server_process.kill()
                        server_process.wait(timeout=2)
                        logger.info("✅ HeadlessPM API process force-killed")
                    except psutil.NoSuchProcess:
                        logger.info("Process already terminated during force-kill")
                        
            except psutil.NoSuchProcess:
                logger.info("API server process already terminated")
            except psutil.AccessDenied:
                logger.error(f"Access denied when terminating PID {cleanup_pid} - insufficient permissions")
            except Exception as e:
                logger.error(f"Error terminating API server process: {e}")
                
        finally:
            # Clear the references and cleanup flag
            self._api_server_pid = None
            self._api_server_start_time = None
            self._we_started_api = False
            self._cleanup_in_progress = False

    async def ensure_api_available(self) -> bool:
        """Ensure HeadlessPM API is available using connection-first pattern with fork bomb protection."""
        # Extract host and port from base_url
        parsed = urllib.parse.urlparse(self.base_url)
        port = parsed.port or 6969

        # Pre-emptive stale API PID check
        coordination_file = self._get_mcp_coordination_file()
        if coordination_file.exists():
            def clean_stale_pids(data: Dict) -> Dict:
                from src.utils.process_registry import migrate_legacy_structure
                
                # First migrate to flat structure
                data = migrate_legacy_structure(data)
                
                # Clean legacy api_pid field 
                api_pid = data.get('api_pid')
                if api_pid and HAS_PSUTIL and not psutil.pid_exists(api_pid):
                    logger.warning(f"Found stale legacy API PID {api_pid}. Cleaning up.")
                    del data['api_pid']
                
                # Clean stale PIDs from flat structure
                if HAS_PSUTIL and 'processes' in data:
                    stale_pids = []
                    for pid_str, info in data['processes'].items():
                        try:
                            pid = int(pid_str)
                            if not psutil.pid_exists(pid):
                                stale_pids.append(pid_str)
                                logger.warning(f"Found stale {info.get('type', 'unknown')} PID {pid}. Cleaning up.")
                        except (ValueError, TypeError):
                            stale_pids.append(pid_str)
                            logger.warning(f"Found invalid PID entry '{pid_str}'. Cleaning up.")
                    
                    for pid_str in stale_pids:
                        del data['processes'][pid_str]
                
                return data
            try:
                AtomicFileOperations.atomic_json_update(coordination_file, clean_stale_pids, {})
            except Exception as e:
                logger.warning(f"Could not perform pre-emptive stale PID check: {e}")

        # Register this MCP client for coordination
        should_start_api = self._register_mcp_client()

        # Step 1: Try to connect to existing API
        try:
            logger.info(f"Checking for existing API at {self.base_url}...")
            response = await self.client.get(f"{self.base_url}/health", timeout=5.0)
            if response.status_code == 200:
                logger.info("✅ Connected to existing HeadlessPM API")
                self._we_started_api = False  # We connected to existing API
                # Discover the API server PID for proper cleanup coordination
                api_port = int(os.environ.get("SERVICE_PORT", "6969"))
                pid_info = self._find_api_server_pid(api_port)
                if pid_info:
                    self._api_server_pid, self._api_server_start_time = pid_info
                    logger.info(f"Discovered existing API server PID: {self._api_server_pid} (created: {self._api_server_start_time})")
                    # Mark that we discovered an existing API (enables handoff cleanup)
                    self._discovered_existing_api = True
                else:
                    logger.warning("Could not discover existing API server PID - cleanup may not work properly")
                return True
        except Exception:
            logger.info("No existing API found")

        # Only attempt to start if coordination says we should
        if not should_start_api:
            logger.info("Another MCP client should be starting the API, waiting...")
            # Wait a bit and try connecting again
            for attempt in range(10):
                await asyncio.sleep(1)
                try:
                    response = await self.client.get(f"{self.base_url}/health", timeout=5.0)
                    if response.status_code == 200:
                        logger.info("✅ Connected to API started by another MCP client")
                        self._we_started_api = False
                        # Discover the API server PID for proper cleanup coordination
                        api_port = int(os.environ.get("SERVICE_PORT", "6969"))
                        pid_info = self._find_api_server_pid(api_port)
                        if pid_info:
                            self._api_server_pid, self._api_server_start_time = pid_info
                            logger.info(f"Discovered API server PID from another client: {self._api_server_pid} (created: {self._api_server_start_time})")
                            # Mark that we discovered an existing API (enables handoff cleanup)
                            self._discovered_existing_api = True
                        else:
                            logger.warning("Could not discover API server PID - cleanup may not work properly")
                        return True
                except Exception:
                    continue
            logger.warning("Timeout waiting for another MCP client to start API")

        # Check if auto-start is disabled
        if os.environ.get("HEADLESS_PM_NO_AUTOSTART"):
            logger.info("Auto-start disabled via HEADLESS_PM_NO_AUTOSTART")
            return False

        # Step 2: Try to start API process with fork bomb protection
        logger.info("Attempting to start HeadlessPM API...")
        
        # FORK BOMB PROTECTION: Rate limit using coordination file (thread/process safe)
        if not await self._check_startup_rate_limit(port):
            logger.error("🚨 FORK BOMB PROTECTION: Rate limit exceeded - preventing startup")
            return False
        
        try:
            # Find headless-pm executable in common locations
            headless_pm_cmd = self._find_headless_pm_command()
            if not headless_pm_cmd:
                logger.error("❌ headless-pm command not found")
                logger.error("   Install: pip install headless-pm")
                logger.error("   Override: HEADLESS_PM_COMMAND='your command'")
                return False

            logger.info(f"Starting HeadlessPM API with: {headless_pm_cmd}")

            # Determine working directory with better user context preservation
            working_dir = self._determine_working_directory(headless_pm_cmd)
            logger.info(f"Working directory determined: {working_dir}")
            
            # Ensure working directory is valid and absolute
            if working_dir is None:
                working_dir = os.getcwd()
                logger.info(f"Using current working directory: {working_dir}")
            
            working_dir = str(working_dir)  # Ensure string type
            if not os.path.isabs(working_dir):
                working_dir = os.path.abspath(working_dir)
                logger.info(f"Made working directory absolute: {working_dir}")
            
            # ENVIRONMENT PRE-VALIDATION: Check prerequisites before subprocess spawn
            logger.info("Validating environment prerequisites...")
            
            # 1. Validate HeadlessPM command is executable
            cmd_to_check = headless_pm_cmd[0]
            if not os.path.isabs(cmd_to_check):
                # For relative commands, resolve through PATH
                try:
                    result = subprocess.run(['which', cmd_to_check], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        cmd_to_check = result.stdout.strip()
                        logger.debug(f"Resolved command '{headless_pm_cmd[0]}' to '{cmd_to_check}'")
                    else:
                        logger.error(f"❌ Command not found in PATH: {headless_pm_cmd[0]}")
                        logger.error("   Check if command is installed and PATH is correct")
                        return False
                except Exception as e:
                    logger.error(f"❌ Failed to resolve command path: {e}")
                    return False
            
            if not os.access(cmd_to_check, os.X_OK):
                logger.error(f"❌ Command not executable: {cmd_to_check}")
                logger.error("   Check file permissions")
                return False
                
            logger.debug(f"✅ Command validated: {cmd_to_check}")
            
            # 2. Validate working directory accessibility
            if not os.path.exists(working_dir):
                logger.error(f"❌ Working directory does not exist: {working_dir}")
                return False
                
            if not os.access(working_dir, os.R_OK | os.W_OK):
                logger.error(f"❌ Working directory not accessible: {working_dir}")
                logger.error("   Check directory permissions")
                return False
            
            # 3. Check port availability
            import socket
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('localhost', port))
                    if result == 0:
                        logger.warning(f"⚠️ Port {port} appears to be occupied")
                        logger.warning("   Will attempt startup anyway (may be existing HeadlessPM)")
            except Exception as e:
                logger.debug(f"Port check failed (proceeding anyway): {e}")
            
            # 4. Validate Python interpreter and basic imports
            try:
                # Test if we can import required modules by running a quick validation
                import sys
                test_cmd = [sys.executable, "-c", "import sqlite3, fastapi, uvicorn; print('OK')"]
                result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    logger.warning(f"⚠️ Python dependency validation failed: {result.stderr}")
                    logger.warning("   HeadlessPM may fail due to missing dependencies")
                else:
                    logger.info("✅ Python dependencies validated")
            except Exception as e:
                logger.warning(f"⚠️ Could not validate dependencies: {e}")
            
            # 5. Check database connectivity (if database file exists)
            database_path = os.path.join(working_dir, "headless_pm.db")
            if os.path.exists(database_path):
                try:
                    import sqlite3
                    conn = sqlite3.connect(database_path, timeout=5)
                    conn.execute("SELECT 1")
                    conn.close()
                    logger.info(f"✅ Database connectivity validated: {database_path}")
                except Exception as e:
                    logger.error(f"❌ Database connectivity failed: {e}")
                    logger.error(f"   Database: {database_path}")
                    logger.error("   This may cause HeadlessPM startup failure")
                    print(f"❌ Database error: {e}", file=sys.stderr)
                    return False
            else:
                logger.info(f"Database will be created at: {database_path}")
            
            logger.info("✅ Environment pre-validation completed")

            # Start API process with fork bomb prevention
            fork_bomb_env = {
                **os.environ, 
                "SERVICE_PORT": str(port),
                "HEADLESS_PM_FROM_MCP": "1",  # Prevent MCP server startup in spawned process
            }
            # Only clear MCP_PORT if it would cause recursive startup
            if headless_pm_cmd and "headless-pm" in " ".join(str(arg) for arg in headless_pm_cmd):
                fork_bomb_env["MCP_PORT"] = ""  # Disable MCP server only for recursive commands
            
            # Keep stdout=DEVNULL (prevents buffering issues)
            # Keep stderr=PIPE (needed for error diagnostics and Uvicorn operation)
            # Note: stderr PIPE may fill up with Uvicorn logs (~100 bytes/request)
            # TODO: Investigate background stderr reader if pipe overflow occurs
            self._api_process = subprocess.Popen(
                headless_pm_cmd,
                stdout=subprocess.DEVNULL,  # Keep DEVNULL for stdout to prevent buffering issues
                stderr=subprocess.PIPE,     # Keep PIPE for stderr (needed for diagnostics)
                cwd=working_dir,
                env=fork_bomb_env,
                text=True,  # Enable text mode for easier log processing
                bufsize=1   # Line buffering for immediate stderr output
            )

            logger.info(f"HeadlessPM process started with PID: {self._api_process.pid}")

            # Step 3: Wait for API to become available (with enhanced monitoring)
            startup_start_time = time.time()
            for attempt in range(30):  # Increased from 12 to 30 attempts (15 seconds)
                # Check if process died during startup
                if self._api_process.poll() is not None:
                    # Process died - capture stderr immediately (stdout is DEVNULL so will be empty)
                    try:
                        stdout, stderr = self._api_process.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Force kill if communicate hangs
                        self._api_process.kill()
                        try:
                            stdout, stderr = self._api_process.communicate(timeout=2)
                        except subprocess.TimeoutExpired:
                            logger.error("Process unresponsive after SIGKILL during communicate")
                            stdout, stderr = b"", b"Process hung after kill"
                    
                    exit_code = self._api_process.returncode
                    
                    logger.error(f"❌ CRITICAL: HeadlessPM process died during startup (exit code: {exit_code})")
                    logger.error(f"❌ Process stderr: {stderr[:2000] if stderr else 'No stderr output'}")
                    logger.error(f"❌ Command: {' '.join(headless_pm_cmd)}")
                    logger.error(f"❌ Working directory: {working_dir}")
                    logger.error(f"❌ Environment variables: SERVICE_PORT={fork_bomb_env.get('SERVICE_PORT')}")
                    
                    # Log to stderr for immediate visibility
                    print(f"❌ HeadlessPM startup failed: {stderr[:200] if stderr else 'No error details'}", file=sys.stderr)
                    
                    self._api_process = None
                    return False

                try:
                    await asyncio.sleep(0.5)
                    response = await self.client.get(f"{self.base_url}/health", timeout=5.0)
                    if response.status_code == 200:
                        startup_duration = time.time() - startup_start_time
                        logger.info(f"✅ SUCCESS: HeadlessPM API started successfully in {startup_duration:.2f} seconds")
                        logger.info(f"✅ Health check passed on attempt {attempt + 1}/30")
                        logger.info(f"✅ API responding at {self.base_url}/health")
                        
                        # Mark that WE started this API process
                        self._we_started_api = True
                        
                        # Discover the actual server process PID for proper cleanup
                        port = int(os.environ.get("SERVICE_PORT", "6969"))
                        pid_info = self._find_api_server_pid(port)
                        if pid_info:
                            self._api_server_pid, self._api_server_start_time = pid_info
                            logger.info(f"✅ Discovered API server PID: {self._api_server_pid} (created: {self._api_server_start_time})")
                        else:
                            logger.warning("⚠️ Could not discover API server PID - cleanup may not work properly")
                        
                        # Log successful startup to stderr for visibility
                        print(f"✅ HeadlessPM API started successfully on port {port}", file=sys.stderr)
                        return True
                        
                except Exception as e:
                    if attempt % 5 == 0:  # Log every 5th attempt to avoid spam
                        elapsed = time.time() - startup_start_time
                        logger.debug(f"Startup attempt {attempt + 1}/30 failed after {elapsed:.1f}s: {type(e).__name__}: {e}")
                    continue

            # If we get here, startup failed after all attempts
            startup_duration = time.time() - startup_start_time
            logger.error(f"❌ TIMEOUT: API startup failed after {startup_duration:.2f} seconds (30 attempts)")
            
            if self._api_process.poll() is None:
                logger.error(f"❌ API process still running but not responding at {self.base_url}")
                logger.error("❌ Terminating unresponsive process...")
                try:
                    # Try to get any available stderr before termination (stdout is DEVNULL)
                    stdout, stderr = self._api_process.communicate(timeout=2)
                    if stderr:
                        logger.error(f"❌ Process stderr before termination: {stderr[:1000]}")
                except subprocess.TimeoutExpired:
                    logger.error("❌ Timeout getting process output, force-terminating")
                    
                self._api_process.terminate()
                try:
                    self._api_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._api_process.kill()
                    try:
                        self._api_process.wait(timeout=2)  # Safe timeout after kill
                    except subprocess.TimeoutExpired:
                        logger.error("Process failed to die after SIGKILL - system issue")
            else:
                logger.error("❌ API process exited during startup attempts")
                # Get final stderr if available (stdout is DEVNULL)
                try:
                    stdout, stderr = self._api_process.communicate(timeout=1)
                    if stderr:
                        logger.error(f"❌ Final process stderr: {stderr[:1000]}")
                except:
                    pass

            self._api_process = None
            return False

        except Exception as e:
            logger.error(f"❌ Failed to start HeadlessPM API: {e}")
            return False

    def _find_project_directory(self) -> Optional[Path]:
        """Find HeadlessPM project directory by searching common locations."""
        # Check environment variable first (highest priority)
        if "HEADLESS_PM_DIR" in os.environ:
            env_dir = Path(os.environ["HEADLESS_PM_DIR"])
            if env_dir.exists():
                return env_dir

        # Smart discovery: look for pyproject.toml with headless-pm
        candidates = [
            Path.cwd(),  # Current directory
            Path.cwd() / "headless-pm",  # Subdirectory
            Path.home() / "source" / "agentic" / "headless-pm",  # Common dev path
        ]

        for candidate in candidates:
            if (candidate / "pyproject.toml").exists():
                try:
                    content = (candidate / "pyproject.toml").read_text()
                    if 'name = "headless-pm"' in content:
                        return candidate
                except Exception:
                    continue
        return None

    def _get_current_python(self) -> str:
        """Get the current Python interpreter path."""
        return sys.executable

    def _determine_working_directory(self, cmd: List[str]) -> Optional[Path]:
        """Determine working directory for the command."""
        # Use explicit directory if set
        if "HEADLESS_PM_DIR" in os.environ:
            return Path(os.environ["HEADLESS_PM_DIR"])

        # Commands that need project context
        needs_project_context = any([
            "src.main" in str(cmd),
            "uv" in cmd and any(x in cmd for x in ["run", "start", "api-only"])
        ])

        if needs_project_context:
            project_dir = self._find_project_directory()
            if project_dir:
                return project_dir

        # Default: preserve user's working directory
        return None  # None means use current directory

    def _find_headless_pm_command(self) -> Optional[List[str]]:
        """Find headless-pm command using smart discovery with fork bomb protection."""
        # Environment override - highest priority
        if "HEADLESS_PM_COMMAND" in os.environ:
            return os.environ["HEADLESS_PM_COMMAND"].split()

        current_python = self._get_current_python()

        # Build candidate commands in priority order
        # FORK BOMB PROTECTION: When called from MCP context, prioritize API-only commands
        candidates = []
        
        # If we're in an MCP context, prioritize API-only commands to prevent recursion
        if self._is_mcp_spawned_context():
            # Use port discovery for uvicorn commands but handle import carefully
            try:
                from src.main import get_port
                service_port = str(get_port(6969, env_override="SERVICE_PORT"))
            except ImportError:
                # Fallback if import fails (e.g., in test subprocess)
                service_port = os.environ.get("SERVICE_PORT", "6969")
            candidates.extend([
                # API-only commands first when in MCP context (use dynamic port)
                ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", service_port],
                [current_python, "-m", "src.main"],
                ["python3", "-m", "src.main"],
                ["uv", "run", "api-only"],
                ["uv", "run", "--", "python", "-m", "src.main"],
            ])
        else:
            # Normal discovery order for non-MCP contexts - prioritize port-aware commands
            try:
                from src.main import get_port
                service_port = str(get_port(6969, env_override="SERVICE_PORT"))
            except ImportError:
                service_port = os.environ.get("SERVICE_PORT", "6969")
                
            candidates.extend([
                # 1. Port-aware commands first (respect SERVICE_PORT)
                ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", service_port],
                [current_python, "-m", "src.main"],
                ["python3", "-m", "src.main"],
                
                # 2. Global installations (may ignore SERVICE_PORT)
                ["headless-pm"],
                ["headless-pm-mcp"],

                # 3. Same Python interpreter (consistency)
                [current_python, "-m", "headless_pm"],

                # 4. UV commands
                ["uv", "run", "headless-pm"],
                ["uv", "run", "start"],

                # 5. Virtual environments
                *self._get_venv_commands(),

                # 6. Direct Python execution
                ["python3", "-m", "headless_pm"],
                ["python", "-m", "headless_pm"],
            ])

        # Add project-specific commands if project found
        project_dir = self._find_project_directory()
        if project_dir:
            # Use port discovery for project uvicorn commands with fallback
            try:
                from src.main import get_port
                service_port = str(get_port(6969, env_override="SERVICE_PORT"))
            except ImportError:
                service_port = os.environ.get("SERVICE_PORT", "6969")
            candidates.extend([
                [current_python, "-m", "src.main"],
                ["python3", "-m", "src.main"],
                ["uv", "run", "--", "python", "-m", "src.main"],
                ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", service_port],
            ])

        # Test candidates
        for cmd in candidates:
            if self._test_command(cmd, self._determine_working_directory(cmd)):
                return cmd

        logger.error("❌ No working HeadlessPM command found")
        logger.error("   Install: pip install headless-pm")
        logger.error("   Override: HEADLESS_PM_COMMAND='your command'")
        return None

    def _find_api_server_pid(self, port: int) -> Optional[tuple[int, float]]:
        """Find the PID and creation time of the actual API server process listening on the given port."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Get process connections directly (not from attrs)  
                    connections = proc.net_connections(kind='inet')
                    
                    for conn in connections:
                        if (conn.status == psutil.CONN_LISTEN and 
                            conn.laddr.port == port):
                            
                            # Additional validation: check if it's likely a web server
                            cmdline = proc.info.get('cmdline', [])
                            if cmdline and any('uvicorn' in str(arg) or 'src.main' in str(arg) for arg in cmdline):
                                # Get process creation time for PID reuse protection
                                create_time = proc.create_time()
                                logger.info(f"Found API server process: PID={proc.info['pid']} created={create_time} cmdline={cmdline}")
                                return (proc.info['pid'], create_time)
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    logger.debug(f"Error checking process {proc.info.get('pid', 'unknown')}: {e}")
                    continue
            
            logger.info(f"No API server process found listening on port {port}")
            return None
            
        except Exception as e:
            logger.error(f"Error during process discovery: {e}")
            return None

    def _get_mcp_coordination_file(self) -> Path:
        """Get path to MCP client coordination file using platform-appropriate temp directory."""
        temp_dir = Path(tempfile.gettempdir())
        port = os.environ.get('SERVICE_PORT', '6969')
        return temp_dir / f"headless_pm_mcp_clients_{port}.json"

    def _register_mcp_client(self) -> bool:
        """Register this MCP client and return True if we should start API."""
        coordination_file = self._get_mcp_coordination_file()
        
        def add_client(data: Dict) -> Dict:
            """Add MCP client to flat PID-keyed structure."""
            # Import required utilities for flat structure
            from src.utils.process_registry import check_pid_conflict, migrate_legacy_structure
            
            # Migrate to flat structure immediately
            data = migrate_legacy_structure(data)
            
            current_pid = os.getpid()
            
            # Check for PID conflicts
            if check_pid_conflict(data, current_pid, 'mcp_client'):
                logger.warning(f"PID {current_pid} already registered as API server - skipping MCP client registration")
                return data  # Don't register if conflict
            
            # Register in flat structure
            data.setdefault('processes', {})
            data['processes'][str(current_pid)] = {
                'type': 'mcp_client',
                'client_id': self._client_id,
                'started': time.time(),
                'repository': os.getcwd(),
                'last_heartbeat': time.time()
            }
            
            return data
        
        try:
            # Use atomic file operations
            result = AtomicFileOperations.atomic_json_update(
                coordination_file, add_client, {'clients': {}}
            )
            
            # Count MCP clients in new flat structure
            processes = result.get('processes', {})
            mcp_client_count = sum(1 for info in processes.values() if info.get('type') == 'mcp_client')
            
            # Should start API if this is the first MCP client or no API server exists
            api_server_count = sum(1 for info in processes.values() if info.get('type') == 'api_server')
            should_start = (mcp_client_count == 1 and api_server_count == 0) or api_server_count == 0
            
            logger.info(f"Registered MCP client {self._client_id} ({mcp_client_count} total MCP clients, {api_server_count} API servers)")
            return should_start
            
        except Exception as e:
            logger.warning(f"Could not register MCP client: {e}")
            return True  # Default to starting API if coordination fails

    def _unregister_mcp_client(self) -> bool:
        """Unregister this MCP client and return True if we should cleanup API."""
        coordination_file = self._get_mcp_coordination_file()
        port = os.environ.get('SERVICE_PORT', '6969')
        
        def coordinated_unregister():
            """Perform unregister with coordination lock."""
            def remove_client(data: Dict) -> Dict:
                """Remove MCP client from flat PID-keyed structure."""
                # Import required migration for flat structure
                from src.utils.process_registry import migrate_legacy_structure
                
                # Migrate to flat structure immediately
                data = migrate_legacy_structure(data)
                
                # Remove from flat structure
                current_pid_str = str(os.getpid())
                processes = data.get('processes', {})
                
                # Remove this process if it's our MCP client
                if (current_pid_str in processes and 
                    processes[current_pid_str].get('client_id') == self._client_id):
                    processes.pop(current_pid_str)
                
                data['processes'] = processes
                return data
            
            # Atomic file update
            result = AtomicFileOperations.atomic_json_update(
                coordination_file, remove_client, {'clients': {}}
            )
            
            # Count remaining processes in flat structure
            processes = result.get('processes', {})
            mcp_client_count = sum(1 for info in processes.values() if info.get('type') == 'mcp_client')
            api_server_count = sum(1 for info in processes.values() if info.get('type') == 'api_server')
            
            # Should cleanup API if no MCP clients remain and we started the API
            should_cleanup = mcp_client_count == 0 and self._we_started_api
            
            logger.info(f"Unregistered MCP client {self._client_id} ({mcp_client_count} remaining MCP clients, {api_server_count} API servers)")
            
            # Remove coordination file if no clients remain
            if should_cleanup:
                try:
                    coordination_file.unlink()
                except:
                    pass
            
            return should_cleanup
        
        try:
            # Use coordination lock for atomic unregister + cleanup decision
            result = with_coordination_lock(
                f"api_exit_{port}", 
                coordinated_unregister,
                timeout=10,
                client_id=self._client_id
            )
            
            return result if result is not None else False
            
        except Exception as e:
            logger.warning(f"Could not unregister MCP client: {e}")
            return False  # Default to not cleaning up if coordination fails

    async def _check_startup_rate_limit(self, port: int) -> bool:
        """
        Check startup rate limit using atomic file operations for consistency.
        Allows 3 startups within a 5-second window. The 4th is blocked.
        """
        coordination_file = self._get_mcp_coordination_file()
        now = time.time()

        def update_and_check_rate_limit(data: Dict) -> Dict:
            """Atomically checks and updates rate limiting data."""
            if 'rate_limits' not in data:
                data['rate_limits'] = {}

            port_key = str(port)
            rate_data = data['rate_limits'].get(port_key, {'attempts': []})

            # 1. Prune old timestamps (older than 5 minutes) to prevent the file from growing indefinitely.
            five_minutes_ago = now - 300
            rate_data['attempts'] = [t for t in rate_data['attempts'] if t > five_minutes_ago]

            # 2. Check the condition BEFORE adding the new attempt.
            five_seconds_ago = now - 5.0
            recent_attempts = [t for t in rate_data['attempts'] if t > five_seconds_ago]

            # 3. The core logic: If 3 or more attempts are already logged, this new one is the 4th (or more), which should be blocked.
            if len(recent_attempts) >= 3:
                logger.warning(
                    f"Rate limit exceeded for port {port}: Found {len(recent_attempts)} attempts in the last 5 seconds. Blocking new attempt."
                )
                # Use a signal key to inform the outer scope that a block occurred.
                data['rate_limit_blocked_port'] = port_key
                # Return the data WITHOUT adding the new attempt.
                return data

            # 4. If not blocked, record this new attempt.
            rate_data['attempts'].append(now)
            data['rate_limits'][port_key] = rate_data

            # 5. Ensure the signal key is not present if we are not blocking.
            if 'rate_limit_blocked_port' in data:
                del data['rate_limit_blocked_port']

            return data

        try:
            # Execute the atomic update
            final_data = AtomicFileOperations.atomic_json_update(
                coordination_file, update_and_check_rate_limit, {}
            )

            # Check if the signal key was set by the update function
            if final_data.get('rate_limit_blocked_port') == str(port):
                return False  # Startup is NOT allowed

            return True  # Startup is allowed

        except Exception as e:
            logger.warning(f"Rate limit check failed with exception: {e} - allowing startup as a failsafe.")
            return True

    def _get_venv_commands(self) -> List[List[str]]:
        """Get virtual environment commands to try."""
        commands = []
        project_dir = self._find_project_directory()
        # Search in CWD first, then project_dir if it's different
        search_dirs = [Path.cwd()]
        if project_dir and project_dir != Path.cwd():
            search_dirs.append(project_dir)

        for venv_name in [".venv", "venv", "claude_venv"]:
            for base_dir in search_dirs:
                venv_path = base_dir / venv_name / "bin" / "headless-pm"
                if venv_path.exists():
                    commands.append([str(venv_path)])
        return commands

    def _get_venv_api_commands(self) -> List[List[str]]:
        """Get virtual environment API-only commands to prevent fork bombs."""
        commands = []
        project_dir = self._find_project_directory()
        # Search in CWD first, then project_dir if it's different
        search_dirs = [Path.cwd()]
        if project_dir and project_dir != Path.cwd():
            search_dirs.append(project_dir)

        for venv_name in [".venv", "venv", "claude_venv"]:
            for base_dir in search_dirs:
                venv_python = base_dir / venv_name / "bin" / "python"
                if venv_python.exists():
                    # Use Python API commands only - never spawn full headless-pm
                    commands.extend([
                        [str(venv_python), "-m", "src.main"],
                        [str(venv_python), "-m", "headless_pm"]
                    ])
        return commands

    def _is_mcp_spawned_context(self) -> bool:
        """Detect if we're running in an MCP-spawned context to prevent fork bombs."""
        # Check for MCP-specific environment markers
        mcp_indicators = [
            "HEADLESS_PM_FROM_MCP",  # Explicit marker we'll set
            "MCP_CLIENT_ID",         # MCP client identifier
            "_MCP_SERVER_RUNNING",   # Internal MCP server marker
        ]
        
        # Check if any MCP indicators are present
        for indicator in mcp_indicators:
            if os.environ.get(indicator):
                logger.debug(f"Detected MCP context via {indicator}")
                return True
        
        # Check process ancestry for MCP server processes
        try:
            current_process = psutil.Process()
            parent = current_process.parent()
            
            # Check up to 3 levels of parent processes
            for level in range(3):
                if parent is None:
                    break
                    
                cmdline = parent.cmdline()
                # More specific MCP detection - look for actual MCP-related patterns
                if cmdline and any(pattern in str(cmdline).lower() for pattern in [
                    'src.mcp', 'mcp/server', 'mcp_server', 'headless-pm-mcp', 'mcp.server'
                ]):
                    logger.debug(f"Detected MCP context via parent process: {cmdline}")
                    return True
                    
                parent = parent.parent()
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        except Exception as e:
            # If context detection fails, err on side of caution and assume MCP context
            logger.warning(f"Error detecting MCP context - assuming MCP context for safety: {e}")
            return True  # Safe default: assume MCP context to prevent fork bomb
            
        return False

    def _test_command(self, cmd: List[str], working_dir: Optional[Path]) -> bool:
        """Test if a command is executable and working."""
        try:
            # Skip non-existent venv binaries quickly
            if len(cmd) == 1 and "/" in cmd[0] and not Path(cmd[0]).exists():
                return False

            # Use --help for general compatibility
            test_args = cmd + ["--help"]
            
            # Use minimal test environment (don't include fork bomb protection vars in testing)
            test_env = {k: v for k, v in os.environ.items() 
                       if not k.startswith('HEADLESS_PM_FROM_MCP')}

            result = subprocess.run(
                test_args,
                capture_output=True,
                timeout=3,
                cwd=working_dir or Path.cwd(),
                env=test_env
            )
            return result.returncode == 0
        except Exception:
            return False

    def _register_handlers(self):
        """Register MCP handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available tools."""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="register_agent",
                        description="Register agent with Headless PM system",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "agent_id": {
                                    "type": "string",
                                    "description": "Unique identifier for the agent"
                                },
                                "role": {
                                    "type": "string",
                                    "description": "Agent role (frontend_dev, backend_dev, architect, pm, qa)",
                                    "enum": ["frontend_dev", "backend_dev", "architect", "pm", "qa"]
                                },
                                "skill_level": {
                                    "type": "string",
                                    "description": "Agent skill level",
                                    "enum": ["junior", "senior", "principal"],
                                    "default": "senior"
                                }
                            },
                            "required": ["agent_id", "role"]
                        }
                    ),
                    Tool(
                        name="get_project_context",
                        description="Get project configuration and context information",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    ),
                    Tool(
                        name="get_next_task",
                        description="Get next available task for the registered agent",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "role": {
                                    "type": "string",
                                    "description": "Override agent role for task search"
                                },
                                "skill_level": {
                                    "type": "string",
                                    "description": "Override skill level for task search"
                                }
                            }
                        }
                    ),
                    Tool(
                        name="create_task",
                        description="Create a new task",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Task title"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Detailed task description"
                                },
                                "complexity": {
                                    "type": "string",
                                    "description": "Task complexity level",
                                    "enum": ["minor", "major"]
                                },
                                "role": {
                                    "type": "string",
                                    "description": "Required role for the task"
                                },
                                "skill_level": {
                                    "type": "string",
                                    "description": "Required skill level for the task",
                                    "enum": ["junior", "senior", "principal"]
                                }
                            },
                            "required": ["title", "description", "complexity"]
                        }
                    ),
                    Tool(
                        name="lock_task",
                        description="Lock a task to prevent other agents from picking it up",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "task_id": {
                                    "type": "integer",
                                    "description": "ID of the task to lock"
                                }
                            },
                            "required": ["task_id"]
                        }
                    ),
                    Tool(
                        name="update_task_status",
                        description="Update task status and progress",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "task_id": {
                                    "type": "integer",
                                    "description": "ID of the task to update"
                                },
                                "status": {
                                    "type": "string",
                                    "description": "New task status",
                                    "enum": ["created", "assigned", "under_work", "dev_done", "testing", "completed",
                                             "blocked"]
                                },
                                "notes": {
                                    "type": "string",
                                    "description": "Optional notes about the update"
                                }
                            },
                            "required": ["task_id", "status"]
                        }
                    ),
                    Tool(
                        name="create_document",
                        description="Create a document with optional @mentions for team communication",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Document title"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Document content (supports @mentions)"
                                },
                                "doc_type": {
                                    "type": "string",
                                    "description": "Document type",
                                    "default": "note"
                                },
                                "mentions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of agent IDs to mention"
                                }
                            },
                            "required": ["title", "content"]
                        }
                    ),
                    Tool(
                        name="get_mentions",
                        description="Get notifications and mentions for the registered agent",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    ),
                    Tool(
                        name="register_service",
                        description="Register a microservice with the system",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "service_name": {
                                    "type": "string",
                                    "description": "Name of the service"
                                },
                                "service_url": {
                                    "type": "string",
                                    "description": "Service URL"
                                },
                                "health_check_url": {
                                    "type": "string",
                                    "description": "Health check endpoint URL"
                                }
                            },
                            "required": ["service_name", "service_url"]
                        }
                    ),
                    Tool(
                        name="send_heartbeat",
                        description="Send heartbeat for a registered service",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "service_name": {
                                    "type": "string",
                                    "description": "Name of the service"
                                },
                                "status": {
                                    "type": "string",
                                    "description": "Service status",
                                    "default": "healthy"
                                }
                            },
                            "required": ["service_name"]
                        }
                    ),
                    Tool(
                        name="poll_changes",
                        description="Poll for system changes since a given timestamp",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "since_timestamp": {
                                    "type": "string",
                                    "description": "ISO timestamp to poll changes since"
                                }
                            }
                        }
                    ),
                    Tool(
                        name="get_token_usage",
                        description="Get MCP token usage statistics",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    )
                ]
            )

        @self.server.list_resources()
        async def handle_list_resources() -> ListResourcesResult:
            """List available resources."""
            return ListResourcesResult(
                resources=[
                Resource(
                        uri="headless-pm://tasks/list",
                        name="Current Tasks",
                        description="List of all current tasks in the system",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="headless-pm://agents/list",
                        name="Active Agents",
                        description="List of all registered agents",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="headless-pm://documents/recent",
                        name="Recent Documents",
                        description="Recently created documents and communications",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="headless-pm://services/status",
                        name="Service Status",
                        description="Status of all registered microservices",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="headless-pm://changelog/recent",
                        name="Recent Activity",
                        description="Recent system activity and changes",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="headless-pm://context/project",
                        name="Project Context",
                        description="Current project configuration and context",
                        mimeType="application/json"
                    )
                ]
            )

        @self.server.read_resource()
        async def handle_read_resource(request: ReadResourceRequest) -> ReadResourceResult:
            """Read resource content."""
            uri = request.uri

            try:
                if uri == "headless-pm://tasks/list":
                    response = await self.client.get(f"{self.base_url}/api/v1/tasks")
                    data = response.json()
                    content = json.dumps(data, indent=2)

                elif uri == "headless-pm://agents/list":
                    response = await self.client.get(f"{self.base_url}/api/v1/agents")
                    data = response.json()
                    content = json.dumps(data, indent=2)

                elif uri == "headless-pm://documents/recent":
                    response = await self.client.get(f"{self.base_url}/api/v1/documents?limit=20")
                    data = response.json()
                    content = json.dumps(data, indent=2)

                elif uri == "headless-pm://services/status":
                    response = await self.client.get(f"{self.base_url}/api/v1/services")
                    data = response.json()
                    content = json.dumps(data, indent=2)

                elif uri == "headless-pm://changelog/recent":
                    response = await self.client.get(f"{self.base_url}/api/v1/changelog?limit=50")
                    data = response.json()
                    content = json.dumps(data, indent=2)

                elif uri == "headless-pm://context/project":
                    response = await self.client.get(f"{self.base_url}/api/v1/context")
                    data = response.json()
                    content = json.dumps(data, indent=2)

                else:
                    raise ValueError(f"Unknown resource URI: {uri}")

                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=content
                        )
                    ]
                )

            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=f"Error reading resource: {str(e)}"
                        )
                    ]
                )

        @self.server.call_tool()
        async def handle_call_tool(tool_name: str, arguments: dict):
            """Handle tool calls."""
            try:
                # Track request tokens
                self.token_tracker.track_request({"tool": tool_name, "args": arguments})
                if tool_name == "register_agent":
                    return await self._register_agent(arguments)
                elif tool_name == "get_project_context":
                    return await self._get_project_context(arguments)
                elif tool_name == "get_next_task":
                    return await self._get_next_task(arguments)
                elif tool_name == "create_task":
                    return await self._create_task(arguments)
                elif tool_name == "lock_task":
                    return await self._lock_task(arguments)
                elif tool_name == "update_task_status":
                    return await self._update_task_status(arguments)
                elif tool_name == "create_document":
                    return await self._create_document(arguments)
                elif tool_name == "get_mentions":
                    return await self._get_mentions(arguments)
                elif tool_name == "register_service":
                    return await self._register_service(arguments)
                elif tool_name == "send_heartbeat":
                    return await self._send_heartbeat(arguments)
                elif tool_name == "poll_changes":
                    return await self._poll_changes(arguments)
                elif tool_name == "get_token_usage":
                    return await self._get_token_usage(arguments)
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")

            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                # Track response tokens
                self.token_tracker.track_response({"error": str(e)})
                # Return error as unstructured content
                return [
                    TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]

    async def _register_agent(self, args: Dict[str, Any]):
        """Register agent with the system."""
        self.agent_id = args["agent_id"]
        self.agent_role = args["role"]
        self.agent_skill_level = args.get("skill_level", "senior")

        data = {
            "agent_id": self.agent_id,
            "role": self.agent_role,
            "level": self.agent_skill_level,  # Changed from skill_level to level
            "connection_type": "mcp"  # Set connection type to MCP
        }

        # API key is already in client headers (set in __init__)
        response = await self.client.post(f"{self.base_url}/api/v1/register", json=data)
        response.raise_for_status()
        result = response.json()

        # Track response tokens
        self.token_tracker.track_response(result)

        # Return unstructured content (list of ContentBlock) - decorator wraps it
        return [
            TextContent(
                type="text",
                text=f"Agent {self.agent_id} registered as {self.agent_role} ({self.agent_skill_level})"
            )
        ]

    async def _get_project_context(self, args: Dict[str, Any]):
        """Get project context."""
        response = await self.client.get(f"{self.base_url}/api/v1/context")
        response.raise_for_status()
        result = response.json()

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

    async def _get_next_task(self, args: Dict[str, Any]):
        """Get next available task."""
        params = {
            "role": args.get("role", self.agent_role),
            "level": args.get("skill_level", self.agent_skill_level)  # API expects 'level' not 'skill_level'
        }

        response = await self.client.get(f"{self.base_url}/api/v1/tasks/next", params=params)
        response.raise_for_status()
        result = response.json()

        if not result:
            return [
                TextContent(
                    type="text",
                    text="No tasks available"
                )
            ]

        return [
            TextContent(
                type="text",
                text=f"Task {result.get('id')}: {result.get('title')}\nComplexity: {result.get('complexity')}\n{result.get('description')}"
            )
        ]

    async def _create_task(self, args: Dict[str, Any]):
        """Create a new task."""
        data = {
            "title": args["title"],
            "description": args["description"],
            "complexity": args["complexity"],
            "role": args.get("role", self.agent_role),
            "skill_level": args.get("skill_level", self.agent_skill_level)
        }

        response = await self.client.post(f"{self.base_url}/api/v1/tasks/create", json=data)
        response.raise_for_status()
        result = response.json()

        return [
            TextContent(
                type="text",
                text=f"Task {result.get('id')} created: {result.get('title')}"
            )
        ]

    async def _lock_task(self, args: Dict[str, Any]):
        """Lock a task."""
        task_id = args["task_id"]
        data = {"agent_id": self.agent_id}

        response = await self.client.post(f"{self.base_url}/api/v1/tasks/{task_id}/lock", json=data)
        response.raise_for_status()

        return [
            TextContent(
                type="text",
                text=f"Task {task_id} locked"
            )
        ]

    async def _update_task_status(self, args: Dict[str, Any]):
        """Update task status."""
        task_id = args["task_id"]
        data = {
            "status": args["status"],
            "agent_id": self.agent_id
        }

        if "notes" in args:
            data["notes"] = args["notes"]

        response = await self.client.put(f"{self.base_url}/api/v1/tasks/{task_id}/status", json=data)
        response.raise_for_status()

        return [
            TextContent(
                type="text",
                text=f"Task {task_id} status: {args['status']}"
            )
        ]

    async def _create_document(self, args: Dict[str, Any]):
        """Create a document."""
        data = {
            "title": args["title"],
            "content": args["content"],
            "type": args.get("doc_type", "note"),
            "author": self.agent_id
        }

        if "mentions" in args:
            data["mentions"] = args["mentions"]

        response = await self.client.post(f"{self.base_url}/api/v1/documents", json=data)
        response.raise_for_status()
        result = response.json()

        mentions_text = ""
        if "mentions" in args and args["mentions"]:
            mentions_text = f"\n**Mentions:** {', '.join(args['mentions'])}"

        return [
            TextContent(
                type="text",
                text=f"Document {result.get('id')} created: {result.get('title')}"
            )
        ]

    async def _get_mentions(self, args: Dict[str, Any]):
        """Get mentions for the agent."""
        params = {"agent_id": self.agent_id}
        response = await self.client.get(f"{self.base_url}/api/v1/mentions", params=params)
        response.raise_for_status()
        result = response.json()

        if not result:
            return [
                TextContent(
                    type="text",
                    text="No mentions"
                )
            ]

        return [
            TextContent(
                type="text",
                text=f"{len(result)} mentions: {json.dumps(result, indent=2)}"
            )
        ]

    async def _register_service(self, args: Dict[str, Any]):
        """Register a service."""
        data = {
            "name": args["service_name"],
            "url": args["service_url"],
            "registered_by": self.agent_id
        }

        if "health_check_url" in args:
            data["health_check_url"] = args["health_check_url"]

        response = await self.client.post(f"{self.base_url}/api/v1/services/register", json=data)
        response.raise_for_status()

        return [
            TextContent(
                type="text",
                text=f"Service '{args['service_name']}' registered"
            )
        ]

    async def _send_heartbeat(self, args: Dict[str, Any]):
        """Send service heartbeat."""
        service_name = args["service_name"]
        data = {"status": args.get("status", "healthy")}

        response = await self.client.post(f"{self.base_url}/api/v1/services/{service_name}/heartbeat", json=data)
        response.raise_for_status()

        return [
            TextContent(
                type="text",
                text=f"Heartbeat sent: {service_name}"
            )
        ]

    async def _poll_changes(self, args: Dict[str, Any]):
        """Poll for changes."""
        params = {}
        if "since_timestamp" in args:
            params["since"] = args["since_timestamp"]

        response = await self.client.get(f"{self.base_url}/api/v1/changes", params=params)
        response.raise_for_status()
        result = response.json()

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

    async def _get_token_usage(self, args: Dict[str, Any]):
        """Get token usage statistics."""
        usage_summary = self.token_tracker.get_usage_summary()

        # Track response tokens
        self.token_tracker.track_response(usage_summary)

        return [
            TextContent(
                type="text",
                text=json.dumps(usage_summary, indent=2)
            )
        ]

    async def run(self):
        """Run the MCP server."""
        if not await self.ensure_api_available():
            logger.error("❌ Could not start or connect to HeadlessPM API")
            logger.error("   Please ensure HeadlessPM is installed or start it manually with: headless-pm")
            return

        try:
            async with stdio_server() as (read_stream, write_stream):
                # Create server task
                server_task = asyncio.create_task(
                    self.server.run(
                        read_stream,
                        write_stream,
                        InitializationOptions(
                            server_name="headless-pm",
                            server_version="1.0.0",
                            capabilities=self.server.get_capabilities(
                                notification_options=NotificationOptions(
                                    prompts_changed=True,
                                    resources_changed=True,
                                    tools_changed=True
                                ),
                                experimental_capabilities={}
                            )
                        )
                    )
                )
                
                # Wait for either server completion or shutdown signal
                shutdown_task = asyncio.create_task(self._shutdown_requested.wait())
                
                try:
                    done, pending = await asyncio.wait(
                        [server_task, shutdown_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Cancel any remaining tasks
                    for task in pending:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                            
                    # If shutdown was requested, perform cleanup
                    if self._shutdown_requested.is_set():
                        logger.info("Performing graceful shutdown...")
                        await self._perform_cleanup()
                        
                except asyncio.CancelledError:
                    logger.info("Server task cancelled, performing cleanup...")
                    await self._perform_cleanup()
                    raise
        finally:
            # Save token usage on shutdown
            if self.agent_id:
                self.token_tracker.end_session(self.agent_id)

            # Backup cleanup in case signal handler didn't run
            if not self._shutdown_requested.is_set():
                logger.info("Signal handler didn't run, performing backup cleanup...")
                await self._perform_cleanup()

            await self.client.aclose()


async def main():
    """Main entry point."""
    import sys
    import os

    # Get base URL from command line args or let constructor handle SERVICE_PORT
    base_url = None
    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    server = HeadlessPMMCPServer(base_url)
    logger.info(f"Starting MCP server, connecting to API at {server.base_url}")
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())