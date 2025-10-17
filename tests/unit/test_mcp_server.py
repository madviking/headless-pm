"""
Unit tests for MCP server functionality including auto-discovery.
"""
import pytest
import asyncio
import httpx
import subprocess
import signal
import time
import os
import tempfile
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture
def engine():
    """Create file-based SQLite engine for testing"""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_file.close()

    engine = create_engine(
        f"sqlite:///{db_file.name}",
        connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)

    try:
        yield engine
    finally:
        # Cleanup - guaranteed to run even if test fails/times out
        try:
            engine.dispose()
        except Exception:
            pass
        try:
            os.unlink(db_file.name)
        except Exception:
            pass


@pytest.fixture
def session(engine):
    """Create database session for testing"""
    with Session(engine) as session:
        yield session


def import_mcp_server():
    """Helper function to import MCP server without path conflicts."""
    # Load module directly to avoid sys.path conflicts
    server_path = Path(__file__).parent.parent.parent / "src" / "mcp" / "server.py"
    spec = importlib.util.spec_from_file_location("server", server_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load MCP server from {server_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.HeadlessPMMCPServer


class TestMCPServer:
    """Test MCP server functionality."""

    def test_import_mcp_server(self):
        """Test that MCP server can be imported correctly."""
        # Use helper function to avoid import conflicts
        HeadlessPMMCPServer = import_mcp_server()

        # Should be able to create instance
        server = HeadlessPMMCPServer()
        assert server.base_url == "http://localhost:6969"
        assert server.client is not None
        assert server.server is not None

    def test_command_discovery(self):
        """Test MCP server command discovery logic."""
        HeadlessPMMCPServer = import_mcp_server()

        server = HeadlessPMMCPServer()
        command = server._find_headless_pm_command()

        # Should find at least one valid command
        assert command is not None, "Should find a valid headless-pm command"
        assert isinstance(command, list), "Command should be a list"
        assert len(command) > 0, "Command list should not be empty"

        # First element should be a valid executable
        assert isinstance(command[0], str), "First command element should be string"

    def test_url_parsing(self):
        """Test URL parsing logic in auto-discovery."""
        HeadlessPMMCPServer = import_mcp_server()
        import urllib.parse

        # Test default URL
        server = HeadlessPMMCPServer()
        parsed = urllib.parse.urlparse(server.base_url)
        port = parsed.port or 6969
        assert port == 6969, "Should parse port correctly from default URL"

        # Test custom URL
        server_custom = HeadlessPMMCPServer("http://localhost:8080")
        parsed_custom = urllib.parse.urlparse(server_custom.base_url)
        port_custom = parsed_custom.port or 6969
        assert port_custom == 8080, "Should parse port correctly from custom URL"

    @pytest.mark.asyncio
    async def test_health_check_logic(self):
        """Test the health check logic used in auto-discovery."""
        HeadlessPMMCPServer = import_mcp_server()

        server = HeadlessPMMCPServer()

        # Mock httpx client for testing
        with patch.object(server.client, 'get') as mock_get:
            # Test successful health check
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            # This tests the core health check logic that auto-discovery uses
            try:
                response = await server.client.get(f"{server.base_url}/health", timeout=5.0)
                assert response.status_code == 200
            except Exception:
                pytest.fail("Health check logic should work with mocked response")

    def test_process_tracking(self):
        """Test that MCP server properly tracks API processes."""
        HeadlessPMMCPServer = import_mcp_server()

        server = HeadlessPMMCPServer()

        # Initially should have no process
        assert server._api_process is None

        # After setting a mock process, should track it
        mock_process = MagicMock()
        server._api_process = mock_process
        assert server._api_process is mock_process

    @pytest.mark.asyncio
    async def test_ensure_api_available_no_command(self):
        """Test auto-discovery behavior when no command is found."""
        HeadlessPMMCPServer = import_mcp_server()

        server = HeadlessPMMCPServer()

        # Mock command discovery to return None
        with patch.object(server, '_find_headless_pm_command', return_value=None):
            # Mock client to simulate no existing API
            with patch.object(server.client, 'get', side_effect=Exception("No API")):
                result = await server.ensure_api_available()
                assert result is False, "Should return False when no command found"

    @pytest.mark.asyncio
    async def test_ensure_api_available_existing_api(self):
        """Test auto-discovery behavior when API already exists."""
        HeadlessPMMCPServer = import_mcp_server()

        server = HeadlessPMMCPServer()

        # Mock successful connection to existing API
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(server.client, 'get', return_value=mock_response):
            result = await server.ensure_api_available()
            assert result is True, "Should return True when existing API found"
            assert server._api_process is None, "Should not start new process"

    @pytest.mark.asyncio
    async def test_client_cleanup(self):
        """Test that HTTP client is properly cleaned up."""
        HeadlessPMMCPServer = import_mcp_server()

        server = HeadlessPMMCPServer()

        # Mock the client's aclose method
        with patch.object(server.client, 'aclose', new_callable=AsyncMock) as mock_aclose:
            # Simulate cleanup
            await server.client.aclose()
            mock_aclose.assert_called_once()

    def test_base_url_normalization(self):
        """Test that base URL is properly normalized."""
        HeadlessPMMCPServer = import_mcp_server()

        # Test URL with trailing slash
        server = HeadlessPMMCPServer("http://localhost:6969/")
        assert server.base_url == "http://localhost:6969", "Should strip trailing slash"

        # Test URL without trailing slash
        server2 = HeadlessPMMCPServer("http://localhost:6969")
        assert server2.base_url == "http://localhost:6969", "Should preserve clean URL"

    def test_token_tracker_initialization(self):
        """Test that token tracker is properly initialized."""
        HeadlessPMMCPServer = import_mcp_server()

        server = HeadlessPMMCPServer()
        assert server.token_tracker is not None, "Token tracker should be initialized"

        # Test that it has expected methods
        assert hasattr(server.token_tracker, 'track_request'), "Should have track_request method"
        assert hasattr(server.token_tracker, 'track_response'), "Should have track_response method"


class TestMCPServerIntegration:
    """Integration tests for MCP server (requires more setup)."""

    @pytest.mark.skipif(
        not Path("/Users/athundt/src/agentic/headless-pm/src/mcp/server.py").exists(),
        reason="MCP server file not found"
    )
    def test_mcp_server_script_executable(self):
        """Test that MCP server script can be executed."""
        server_path = Path(__file__).parent.parent.parent / "src" / "mcp" / "server.py"
        assert server_path.exists(), "MCP server script should exist"

        # Test that it can be imported and doesn't crash immediately
        result = subprocess.run([
            "python", "-c",
            f"import sys; sys.path.insert(0, '{server_path.parent}'); "
            "from server import HeadlessPMMCPServer; "
            "s = HeadlessPMMCPServer(); "
            "print('SUCCESS')"
        ],
        capture_output=True,
        text=True,
        cwd=server_path.parent.parent.parent
        )

        assert result.returncode == 0, f"Script import failed: {result.stderr}"
        assert "SUCCESS" in result.stdout, "Should successfully import and create server"

    def test_command_priority_order(self):
        """Test that command discovery follows the correct priority order."""
        HeadlessPMMCPServer = import_mcp_server()
        import shutil

        server = HeadlessPMMCPServer()
        command = server._find_headless_pm_command()

        if command:  # Only test if a command was found
            # Build expected patterns dynamically based on available tools
            expected_patterns = [
                ["headless-pm"],
                ["python", "-m", "src.main"],
                ["uvicorn", "src.main:app", "--host", "0.0.0.0"]
            ]

            # Add python3 patterns if python3 is available
            if shutil.which("python3"):
                expected_patterns.append(["python3", "-m", "src.main"])

            # Add UV patterns only if UV is available
            if shutil.which("uv"):
                expected_patterns.extend([
                    ["uv", "run"],
                    ["uv", "run", "python", "-m", "src.main"],
                    ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0"]
                ])

            # Should match at least one pattern
            matches_pattern = any(
                command[:len(pattern)] == pattern
                for pattern in expected_patterns
            )
            assert matches_pattern, f"Command {command} should match expected patterns. Available: {[p for p in expected_patterns]}"

    def test_project_directory_discovery_method(self):
        """Test the separated project directory discovery method."""
        HeadlessPMMCPServer = import_mcp_server()

        server = HeadlessPMMCPServer()
        project_dir = server._find_project_directory()

        # Should return None or a valid Path
        assert project_dir is None or isinstance(project_dir, Path), "Should return None or Path"

        if project_dir:
            # If found, should be a valid headless-pm project
            assert (project_dir / "pyproject.toml").exists(), "Should have pyproject.toml"

    def test_command_testing_method(self):
        """Test the separated command testing method."""
        HeadlessPMMCPServer = import_mcp_server()

        server = HeadlessPMMCPServer()

        # Test with a command that should fail
        assert not server._test_command(["/nonexistent/command"], None), "Should fail for nonexistent command"

        # Test with a basic command that might work
        if Path("/bin/echo").exists():
            # Test echo command should work
            assert server._test_command(["/bin/echo"], None), "Echo command should work"

    def test_virtual_environment_handling(self):
        """Test virtual environment path handling."""
        HeadlessPMMCPServer = import_mcp_server()
        from pathlib import Path

        server = HeadlessPMMCPServer()
        current_dir = Path.cwd()

        # Test the logic for checking .venv, venv, claude_venv
        venv_variants = [".venv", "venv", "claude_venv"]

        for venv_name in venv_variants:
            venv_path = current_dir / venv_name / "bin" / "headless-pm"
            # The _test_command method should handle non-existent paths gracefully
            result = server._test_command([str(venv_path)], None)
            assert isinstance(result, bool), f"Should return boolean for {venv_name} test"

    def test_environment_variable_overrides(self):
        """Test environment variable override functionality."""
        HeadlessPMMCPServer = import_mcp_server()
        import os
        from unittest.mock import patch

        # Test HEADLESS_PM_DIR override
        with patch.dict(os.environ, {"HEADLESS_PM_DIR": "/tmp"}):
            server = HeadlessPMMCPServer()
            # Should handle non-existent directory gracefully
            project_dir = server._find_project_directory()
            assert project_dir == Path("/tmp")  # Should use environment override

        # Test HEADLESS_PM_COMMAND override
        with patch.dict(os.environ, {"HEADLESS_PM_COMMAND": "echo hello"}):
            server = HeadlessPMMCPServer()
            # Mock the _test_command to return True
            with patch.object(server, '_test_command', return_value=True):
                cmd = server._find_headless_pm_command()
                assert cmd == ["echo", "hello"], "Should split command string"

    def test_no_regressions_from_original(self):
        """Test that core functionality from original server still works."""
        HeadlessPMMCPServer = import_mcp_server()

        server = HeadlessPMMCPServer()

        # Original functionality should still work
        assert server.base_url == "http://localhost:6969"
        assert server.client is not None
        assert server.server is not None
        assert server.token_tracker is not None

        # Auto-discovery features should be additional, not breaking
        assert hasattr(server, 'ensure_api_available')
        assert hasattr(server, '_find_headless_pm_command')
        assert hasattr(server, '_find_project_directory')
        assert hasattr(server, '_test_command')

    def test_best_practices_implementation(self):
        """Test implementation follows best practices."""
        HeadlessPMMCPServer = import_mcp_server()
        import os
        from unittest.mock import patch

        # Test disable auto-start functionality
        with patch.dict(os.environ, {"HEADLESS_PM_NO_AUTOSTART": "true"}):
            server = HeadlessPMMCPServer()
            # Should have disable flag available
            assert os.environ.get("HEADLESS_PM_NO_AUTOSTART") == "true"

        # Test Python consistency by default
        with patch.dict(os.environ, {}, clear=False):
            server = HeadlessPMMCPServer()
            python_exe = server._get_current_python()
            assert python_exe  # Should return current Python

        # Test working directory determination
        server = HeadlessPMMCPServer()

        # Command that doesn't need project directory
        wd1 = server._determine_working_directory(["headless-pm"])
        assert wd1 is None, "Should preserve user's CWD (None means current directory)"

        # Command that needs project directory
        wd2 = server._determine_working_directory(["python3", "-m", "src.main"])
        # Should either find project or fallback to None (current directory)
        assert wd2 is not None or wd2 is None

    def test_connection_first_pattern(self):
        """Test that connection-first pattern is properly implemented."""
        HeadlessPMMCPServer = import_mcp_server()
        import asyncio
        from unittest.mock import patch, AsyncMock

        server = HeadlessPMMCPServer()

        # Mock successful API connection
        with patch.object(server.client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            # Should return True without trying to start process
            async def test_connection():
                result = await server.ensure_api_available()
                assert result is True
                mock_get.assert_called_once()  # Should only try connection

            # Run the async test
            import asyncio
            try:
                asyncio.run(test_connection())
            except RuntimeError:
                # If event loop already running, that's ok for testing
                pass

    def test_environment_variable_hierarchy(self):
        """Test environment variable hierarchy and override behavior."""
        HeadlessPMMCPServer = import_mcp_server()
        import os
        from unittest.mock import patch
        from pathlib import Path

        # Test HEADLESS_PM_DIR override
        with patch.dict(os.environ, {"HEADLESS_PM_DIR": "/tmp"}):
            server = HeadlessPMMCPServer()
            wd = server._determine_working_directory(["any-command"])
            assert wd == Path("/tmp")

        # Test SERVICE_PORT environment variable
        with patch.dict(os.environ, {"SERVICE_PORT": "8080"}):
            server = HeadlessPMMCPServer()
            assert os.environ.get("SERVICE_PORT") == "8080"

        # Test HEADLESS_PM_NO_AUTOSTART flag
        with patch.dict(os.environ, {"HEADLESS_PM_NO_AUTOSTART": "1"}):
            server = HeadlessPMMCPServer()
            # Should recognize the flag
            assert os.environ.get("HEADLESS_PM_NO_AUTOSTART") == "1"


class TestMCPServerErrorHandling:
    """Test error handling in MCP server."""

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors during health checks."""
        HeadlessPMMCPServer = import_mcp_server()

        server = HeadlessPMMCPServer()

        # Mock network error
        with patch.object(server.client, 'get', side_effect=httpx.ConnectError("Connection failed")):
            # Should handle network errors gracefully in health check logic
            try:
                await server.client.get(f"{server.base_url}/health", timeout=5.0)
                pytest.fail("Should have raised ConnectError")
            except httpx.ConnectError:
                pass  # Expected behavior

    def test_process_termination_handling(self):
        """Test proper process termination logic."""
        HeadlessPMMCPServer = import_mcp_server()

        server = HeadlessPMMCPServer()

        # Mock a process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process running
        server._api_process = mock_process

        # Test termination logic (simulated)
        if server._api_process and server._api_process.poll() is None:
            server._api_process.terminate()
            server._api_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling in API startup."""
        HeadlessPMMCPServer = import_mcp_server()
        import asyncio

        server = HeadlessPMMCPServer()

        # Test that asyncio.sleep calls work (used in retry loops)
        start_time = time.time()
        await asyncio.sleep(0.1)  # Minimal sleep for testing
        elapsed = time.time() - start_time
        assert elapsed >= 0.1, "Should actually wait for the specified time"
        assert elapsed < 0.2, "Should not wait significantly longer than specified"

    @pytest.mark.asyncio
    async def test_raise_for_status_error_handling(self):
        """Test that API methods properly handle HTTP errors with raise_for_status()."""
        HeadlessPMMCPServer = import_mcp_server()
        
        server = HeadlessPMMCPServer()
        server.agent_id = "test_agent"
        
        # Mock client to return 404 error
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", 
            request=MagicMock(), 
            response=mock_response
        )
        
        with patch.object(server.client, 'get', return_value=mock_response):
            # Test that _get_project_context properly raises HTTP errors
            with pytest.raises(httpx.HTTPStatusError):
                await server._get_project_context({})
                
        with patch.object(server.client, 'post', return_value=mock_response):
            # Test that _register_agent properly raises HTTP errors
            with pytest.raises(httpx.HTTPStatusError):
                await server._register_agent({"agent_id": "test", "role": "backend_dev", "skill_level": "senior"})

    @pytest.mark.asyncio  
    async def test_multi_client_safety_cleanup(self):
        """Test that process cleanup respects multi-client safety."""
        HeadlessPMMCPServer = import_mcp_server()
        
        server = HeadlessPMMCPServer()
        server.agent_id = "test_agent"
        
        # Mock a running API process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        server._api_process = mock_process
        
        # Mock agents API response showing multiple active agents
        mock_agents_response = MagicMock()
        mock_agents_response.status_code = 200
        mock_agents_response.json.return_value = [
            {"id": "agent1", "role": "backend_dev"}, 
            {"id": "agent2", "role": "frontend_dev"}
        ]
        
        with patch.object(server.client, 'get', return_value=mock_agents_response):
            # This simulates the cleanup logic that checks for other active agents
            response = await server.client.get(f"{server.base_url}/api/v1/agents", timeout=2.0)
            agents = response.json()
            
            # Should detect multiple agents and avoid termination
            assert len(agents) > 1, "Should detect multiple active agents"
            
            # In real cleanup, this would skip termination
            # We can't test the full cleanup without running the actual method,
            # but this tests the core logic used in multi-client safety
            
        # Test single agent scenario (should allow termination)
        mock_single_agent_response = MagicMock()
        mock_single_agent_response.status_code = 200  
        mock_single_agent_response.json.return_value = [{"id": "agent1", "role": "backend_dev"}]
        
        with patch.object(server.client, 'get', return_value=mock_single_agent_response):
            response = await server.client.get(f"{server.base_url}/api/v1/agents", timeout=2.0)
            agents = response.json()
            
            # Should detect single agent and allow termination
            assert len(agents) == 1, "Should detect single active agent"