"""
Claude subprocess execution with model selection
"""
import subprocess
import os
from pathlib import Path
from typing import Optional, Tuple, List
from .model_mapper import ModelMapper


class ClaudeExecutor:
    """Manages Claude subprocess with proper model selection"""
    
    def __init__(self, model_mapper: Optional[ModelMapper] = None):
        """
        Initialize Claude executor
        
        Args:
            model_mapper: ModelMapper instance (creates default if not provided)
        """
        self.model_mapper = model_mapper or ModelMapper()
        self.claude_command = self._find_claude_command()
        
    def _find_claude_command(self) -> str:
        """
        Find Claude executable
        
        Returns:
            Path to Claude command
        """
        # Check common locations
        paths = [
            os.path.expanduser("~/.claude/bin/claude"),
            "/usr/local/bin/claude",
            "claude"  # Fallback to PATH
        ]
        
        for path in paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
                
        # Default to 'claude' and let subprocess handle PATH resolution
        return "claude"
        
    def execute_task(self, task: dict, worktree_path: Path, 
                    instructions_path: Path, timeout: int = 600) -> Tuple[bool, str]:
        """
        Run Claude with task-specific configuration
        
        Args:
            task: Task dictionary with skill_level
            worktree_path: Working directory for Claude
            instructions_path: Path to instructions markdown file
            timeout: Execution timeout in seconds (default 10 minutes)
            
        Returns:
            Tuple of (success, output_or_error)
        """
        # Get appropriate model based on task skill level
        skill_level = task.get('skill_level', 'senior')
        model = self.model_mapper.get_model(skill_level)
        model_name = self.model_mapper.get_model_name(model)
        
        # Build Claude command
        cmd = [
            self.claude_command,
            '--model', model,
            '--dangerously-skip-permissions'
        ]
        
        # Prepare environment
        env = os.environ.copy()
        
        # Ensure worktree path exists
        if not worktree_path.exists():
            return False, f"Worktree path does not exist: {worktree_path}"
            
        # Read instructions
        try:
            with open(instructions_path, 'r') as f:
                instructions = f.read()
        except Exception as e:
            return False, f"Failed to read instructions: {e}"
            
        try:
            # Execute Claude
            result = subprocess.run(
                cmd,
                input=instructions,
                text=True,
                cwd=worktree_path,
                env=env,
                timeout=timeout,
                capture_output=True
            )
            
            if result.returncode == 0:
                return True, f"Task completed successfully with {model_name}"
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return False, f"Claude exited with code {result.returncode}: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, f"Claude execution timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Failed to execute Claude: {e}"
            
    def verify_claude_available(self) -> Tuple[bool, str]:
        """
        Verify Claude is installed and accessible
        
        Returns:
            Tuple of (is_available, message)
        """
        try:
            result = subprocess.run(
                [self.claude_command, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, f"Claude available: {version}"
            else:
                return False, "Claude command failed"
                
        except FileNotFoundError:
            return False, f"Claude not found at: {self.claude_command}"
        except Exception as e:
            return False, f"Error checking Claude: {e}"
            
    def build_command_args(self, task: dict, additional_flags: Optional[List[str]] = None) -> List[str]:
        """
        Build command arguments for Claude execution
        
        Args:
            task: Task dictionary
            additional_flags: Optional additional command flags
            
        Returns:
            List of command arguments
        """
        skill_level = task.get('skill_level', 'senior')
        model = self.model_mapper.get_model(skill_level)
        
        args = [
            self.claude_command,
            '--model', model,
            '--dangerously-skip-permissions'
        ]
        
        if additional_flags:
            args.extend(additional_flags)
            
        return args