#!/usr/bin/env python3
"""
Advanced Claude PM Runner - Continuous task execution with git worktree support
"""
import argparse
import sys
import time
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from headless_pm_client import HeadlessPMClient
from .config import Config
from .components import (
    GitWorktree, TaskPersistence, HookRunner, 
    ModelMapper, ClaudeExecutor, TerminalUI
)


class AdvancedAgentRunner:
    """Main runner class for continuous Claude agent execution"""
    
    def __init__(self, role: str, agent_id: str, config: Optional[Config] = None):
        """
        Initialize the runner
        
        Args:
            role: Agent role (backend_dev, frontend_dev, qa, etc.)
            agent_id: Unique agent identifier
            config: Optional configuration object
        """
        self.role = role
        self.agent_id = agent_id
        self.config = config or Config()
        
        # Initialize components
        self.ui = TerminalUI()
        self.persistence = TaskPersistence(agent_id)
        self.client = self._init_client()
        self.git_worktree = GitWorktree(Path.cwd())
        self.hook_runner = HookRunner()
        self.model_mapper = ModelMapper()
        self.claude_executor = ClaudeExecutor(self.model_mapper)
        
        # State
        self.running = True
        self.last_health_check = time.time()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _init_client(self) -> HeadlessPMClient:
        """Initialize PM client with config"""
        return HeadlessPMClient(
            base_url=self.config.api_url,
            api_key=self.config.api_key
        )
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.ui.warning("Received shutdown signal, cleaning up...")
        self.running = False
        
    def run_continuous(self):
        """Main execution loop with task persistence"""
        self.ui.header(f"Advanced Agent Runner - {self.role} ({self.agent_id})")
        
        # Validate configuration
        valid, message = self.config.validate()
        if not valid:
            self.ui.error(message)
            sys.exit(1)
            
        # Verify Claude is available
        available, claude_msg = self.claude_executor.verify_claude_available()
        if not available:
            self.ui.error(f"Claude not available: {claude_msg}")
            sys.exit(1)
        self.ui.success(claude_msg)
        
        # Register agent
        self._register_agent()
        
        # Main loop
        session_count = 0
        while self.running:
            session_count += 1
            self.ui.separator()
            self.ui.info(f"Session {session_count} starting...")
            
            # Run health check if needed
            if time.time() - self.last_health_check > self.config.health_check_interval:
                self._run_health_check()
                
            # Check for locked task first (crash recovery)
            task = self._recover_locked_task()
            
            if not task:
                # Get new task
                task = self._get_next_task()
                if not task:
                    self.ui.info("No tasks available, waiting...")
                    time.sleep(self.config.task_check_interval)
                    continue
                    
                # Lock task
                self.persistence.lock_task(task)
                
            # Execute task
            try:
                self._execute_task(task)
            except Exception as e:
                self.ui.error(f"Task execution failed: {e}")
                # Keep task locked for retry
                
        # Cleanup on exit
        self._cleanup()
        
    def run_single_task(self):
        """Run a single task then exit (for testing)"""
        self.ui.header(f"Single Task Mode - {self.role} ({self.agent_id})")
        
        # Register agent
        self._register_agent()
        
        # Get and execute one task
        task = self._get_next_task()
        if task:
            self.persistence.lock_task(task)
            self._execute_task(task)
        else:
            self.ui.warning("No tasks available")
            
        self._cleanup()
        
    def _register_agent(self):
        """Register agent with PM system"""
        try:
            result = self.client.register_agent(
                agent_id=self.agent_id,
                role=self.role,
                skill_level="senior"  # Default to senior
            )
            self.ui.success(f"Agent registered: {self.agent_id}")
        except Exception as e:
            self.ui.error(f"Failed to register agent: {e}")
            sys.exit(1)
            
    def _recover_locked_task(self) -> Optional[Dict[str, Any]]:
        """Check for and recover previously locked task"""
        lock_data = self.persistence.get_locked_task()
        if not lock_data:
            return None
            
        self.ui.warning("Recovering previously locked task...")
        task = lock_data.get('task_data')
        
        if task:
            self.ui.task_info(task)
            
            # Check if task is still valid
            try:
                current_task = self.client.get_task(task['id'])
                if current_task['status'] in ['completed', 'cancelled']:
                    self.ui.info("Task already completed, releasing lock")
                    self.persistence.release_lock()
                    return None
                return current_task
            except:
                # Task might not exist anymore
                self.persistence.release_lock()
                return None
                
        return None
        
    def _get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get next available task from PM system"""
        self.ui.info("Checking for next task...")
        
        try:
            # The API waits up to 3 minutes for a task
            task = self.client.get_next_task(
                role=self.role,
                skill_level="senior"
            )
            
            if task:
                self.ui.success("Task received!")
                self.ui.task_info(task)
                return task
                
        except Exception as e:
            self.ui.error(f"Failed to get task: {e}")
            
        return None
        
    def _execute_task(self, task: Dict[str, Any]):
        """Execute a task with full workflow"""
        start_time = time.time()
        
        # Run pre-task hooks
        self.ui.progress("Running pre-task checks...")
        proceed, hook_msg = self.hook_runner.run_pre_task(task)
        if not proceed:
            self.ui.error(hook_msg)
            # Operator intervention
            choice = self.ui.prompt_operator(
                "Pre-task checks failed. How to proceed?",
                ["Retry checks", "Skip checks and continue", "Release task"]
            )
            if choice == "Release task":
                self.persistence.release_lock()
                return
            elif choice == "Retry checks":
                self._execute_task(task)  # Recursive retry
                return
                
        # Lock task in PM system
        try:
            self.client.lock_task(task['id'], self.agent_id)
            self.ui.success("Task locked in PM system")
        except Exception as e:
            self.ui.error(f"Failed to lock task: {e}")
            self.persistence.release_lock()
            return
            
        # Set up worktree if needed (for major tasks)
        worktree_path = Path.cwd()
        if task.get('complexity') == 'major':
            self.ui.progress("Setting up git worktree for major task...")
            try:
                branch_name = self.git_worktree.create_branch_for_task(task['id'])
                worktree_path = self.git_worktree.create_for_task(task['id'], branch_name)
                self.persistence.update_lock(
                    worktree_path=worktree_path,
                    branch_name=branch_name
                )
                self.ui.success(f"Worktree created at: {worktree_path}")
            except Exception as e:
                self.ui.error(f"Failed to create worktree: {e}")
                # Continue without worktree
                
        # Get instructions
        instructions_path = self.config.get_instructions_path(self.role)
        if not instructions_path:
            self.ui.error(f"No instructions found for role: {self.role}")
            self.persistence.release_lock()
            return
            
        # Execute Claude
        self.ui.progress(f"Executing task with {self.model_mapper.get_model_name(self.model_mapper.get_model(task.get('skill_level', 'senior')))}")
        success, execution_msg = self.claude_executor.execute_task(
            task=task,
            worktree_path=worktree_path,
            instructions_path=instructions_path,
            timeout=self.config.claude_timeout
        )
        
        execution_time = time.time() - start_time
        
        if success:
            self.ui.success(execution_msg)
            
            # Update task status
            new_status = self._get_completion_status()
            try:
                self.client.update_task_status(
                    task_id=task['id'],
                    status=new_status,
                    agent_id=self.agent_id
                )
                self.ui.success(f"Task status updated to: {new_status}")
            except Exception as e:
                self.ui.error(f"Failed to update task status: {e}")
                
        else:
            self.ui.error(execution_msg)
            
        # Run post-task hooks
        self.ui.progress("Running post-task cleanup...")
        self.hook_runner.run_post_task(task, success, execution_time)
        
        # Cleanup worktree if used
        if task.get('complexity') == 'major' and worktree_path != Path.cwd():
            try:
                self.git_worktree.cleanup(task['id'])
                self.ui.info("Worktree cleaned up")
            except Exception as e:
                self.ui.warning(f"Failed to cleanup worktree: {e}")
                
        # Release lock
        self.persistence.release_lock()
        self.ui.success(f"Task completed in {execution_time:.1f} seconds")
        
    def _get_completion_status(self) -> str:
        """Get the appropriate completion status for the role"""
        status_map = {
            'backend_dev': 'dev_done',
            'frontend_dev': 'dev_done',
            'fullstack_dev': 'dev_done',
            'qa': 'completed',
            'architect': 'completed',
            'pm': 'completed'
        }
        return status_map.get(self.role, 'completed')
        
    def _run_health_check(self):
        """Run periodic health check"""
        self.ui.info("Running health check...")
        healthy, msg = self.hook_runner.run_health_check()
        
        if healthy:
            self.ui.success(msg)
        else:
            self.ui.warning(msg)
            
        self.last_health_check = time.time()
        
    def _cleanup(self):
        """Cleanup on exit"""
        self.ui.info("Cleaning up...")
        
        # Release any locked tasks
        if self.persistence.is_locked():
            self.persistence.release_lock()
            
        # Unregister agent
        try:
            self.client.delete_agent(self.agent_id)
            self.ui.success("Agent unregistered")
        except:
            pass  # Ignore errors during cleanup


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Advanced Claude PM Runner - Continuous task execution"
    )
    
    parser.add_argument(
        '--role',
        required=True,
        choices=['backend_dev', 'frontend_dev', 'fullstack_dev', 'qa', 'architect', 'pm'],
        help='Agent role'
    )
    
    parser.add_argument(
        '--agent-id',
        required=True,
        help='Unique agent identifier'
    )
    
    parser.add_argument(
        '--single-task',
        action='store_true',
        help='Run only one task then exit'
    )
    
    parser.add_argument(
        '--hooks-dir',
        type=Path,
        help='Custom hooks directory'
    )
    
    args = parser.parse_args()
    
    # Create config
    config = Config()
    
    # Override hooks dir if provided
    if args.hooks_dir:
        config.hooks_dir = args.hooks_dir
        
    # Create and run runner
    runner = AdvancedAgentRunner(
        role=args.role,
        agent_id=args.agent_id,
        config=config
    )
    
    if args.single_task:
        runner.run_single_task()
    else:
        runner.run_continuous()


if __name__ == "__main__":
    main()