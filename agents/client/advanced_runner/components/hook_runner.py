"""
Global hook execution for continuous operation assurance
"""
import subprocess
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple


class HookRunner:
    """Executes global hooks for continuous operation assurance"""
    
    def __init__(self, hooks_dir: Optional[Path] = None):
        """
        Initialize hook runner
        
        Args:
            hooks_dir: Directory containing hook scripts (defaults to ./hooks)
        """
        if hooks_dir:
            self.hooks_dir = Path(hooks_dir)
        else:
            # Default to hooks directory relative to this file
            self.hooks_dir = Path(__file__).parent.parent / "hooks"
            
        self.hooks_dir.mkdir(exist_ok=True)
        
    def _execute_hook(self, hook_name: str, data: Optional[Dict[str, Any]] = None,
                     timeout: int = 30) -> Tuple[bool, str]:
        """
        Execute a single hook script
        
        Args:
            hook_name: Name of hook script (without extension)
            data: Optional data to pass to hook via stdin
            timeout: Execution timeout in seconds
            
        Returns:
            Tuple of (success, output_or_error)
        """
        # Look for hook script (try .py first, then .sh)
        hook_paths = [
            self.hooks_dir / f"{hook_name}.py",
            self.hooks_dir / f"{hook_name}.sh",
            self.hooks_dir / hook_name  # No extension
        ]
        
        hook_script = None
        for path in hook_paths:
            if path.exists() and path.is_file():
                hook_script = path
                break
                
        if not hook_script:
            return True, f"No hook found for: {hook_name}"
            
        # Make sure hook is executable
        if not os.access(hook_script, os.X_OK):
            os.chmod(hook_script, 0o755)
            
        # Prepare input data
        input_data = json.dumps(data) if data else ""
        
        try:
            # Execute hook
            result = subprocess.run(
                [str(hook_script)],
                input=input_data,
                text=True,
                capture_output=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                error_msg = result.stderr or result.stdout or f"Hook failed with code {result.returncode}"
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            return False, f"Hook {hook_name} timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Failed to execute hook {hook_name}: {e}"
            
    def run_pre_task(self, task: dict) -> Tuple[bool, str]:
        """
        Run pre-task hooks
        
        Args:
            task: Task dictionary
            
        Returns:
            Tuple of (should_proceed, message)
        """
        hook_data = {
            "task_id": task.get("id"),
            "task_title": task.get("title"),
            "skill_level": task.get("skill_level"),
            "complexity": task.get("complexity"),
            "status": task.get("status")
        }
        
        success, message = self._execute_hook("pre_task", hook_data)
        
        if not success:
            return False, f"Pre-task hook failed: {message}"
            
        return True, "Pre-task checks passed"
        
    def run_post_task(self, task: dict, success: bool, execution_time: Optional[float] = None) -> None:
        """
        Run post-task hooks for cleanup/validation
        
        Args:
            task: Task dictionary
            success: Whether task execution was successful
            execution_time: Optional task execution time in seconds
        """
        hook_data = {
            "task_id": task.get("id"),
            "task_title": task.get("title"),
            "success": success,
            "execution_time": execution_time
        }
        
        # Post-task hooks are non-blocking - we don't care if they fail
        self._execute_hook("post_task", hook_data)
        
    def run_health_check(self) -> Tuple[bool, str]:
        """
        Run periodic health verification
        
        Returns:
            Tuple of (is_healthy, message)
        """
        success, message = self._execute_hook("health_check")
        
        if not success:
            return False, f"Health check failed: {message}"
            
        return True, "System healthy"
        
    def list_available_hooks(self) -> Dict[str, Path]:
        """
        List all available hook scripts
        
        Returns:
            Dictionary of hook_name -> hook_path
        """
        hooks = {}
        
        if not self.hooks_dir.exists():
            return hooks
            
        # Look for executable files in hooks directory
        for file in self.hooks_dir.iterdir():
            if file.is_file() and os.access(file, os.X_OK):
                # Remove extension for hook name
                name = file.stem if file.suffix in ['.py', '.sh'] else file.name
                hooks[name] = file
                
        return hooks
        
    def validate_hooks(self) -> Dict[str, bool]:
        """
        Validate all hooks are properly configured
        
        Returns:
            Dictionary of hook_name -> is_valid
        """
        results = {}
        available_hooks = self.list_available_hooks()
        
        # Check required hooks
        required_hooks = ['pre_task', 'post_task', 'health_check']
        
        for hook in required_hooks:
            results[hook] = hook in available_hooks
            
        return results