"""
Task persistence for crash recovery
Ensures task continuity across crashes/restarts by storing task lock information
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class TaskPersistence:
    """Manages task lock persistence to filesystem"""
    
    def __init__(self, agent_id: str):
        """
        Initialize task persistence for an agent
        
        Args:
            agent_id: Unique identifier for the agent
        """
        self.agent_id = agent_id
        self.lock_dir = Path.home() / ".headless-pm" / "locks"
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.lock_file = self.lock_dir / f"agent-{agent_id}.lock"
        
    def lock_task(self, task: Dict[str, Any], worktree_path: Optional[Path] = None, 
                  branch_name: Optional[str] = None) -> None:
        """
        Persist task lock to filesystem
        
        Args:
            task: Task dictionary from PM API
            worktree_path: Optional path to git worktree
            branch_name: Optional git branch name
        """
        lock_data = {
            "task_id": task["id"],
            "task_title": task.get("title", ""),
            "agent_id": self.agent_id,
            "locked_at": datetime.now().isoformat(),
            "worktree_path": str(worktree_path) if worktree_path else None,
            "branch_name": branch_name,
            "task_data": task  # Store full task for recovery
        }
        
        with open(self.lock_file, 'w') as f:
            json.dump(lock_data, f, indent=2)
            
    def get_locked_task(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve previously locked task if exists
        
        Returns:
            Task data if lock exists, None otherwise
        """
        if not self.lock_file.exists():
            return None
            
        try:
            with open(self.lock_file, 'r') as f:
                lock_data = json.load(f)
                
            # Validate lock is for this agent
            if lock_data.get("agent_id") != self.agent_id:
                return None
                
            return lock_data
            
        except (json.JSONDecodeError, KeyError):
            # Corrupted lock file, remove it
            self.release_lock()
            return None
            
    def update_lock(self, **kwargs) -> None:
        """
        Update existing lock with new information
        
        Args:
            **kwargs: Fields to update in the lock
        """
        lock_data = self.get_locked_task()
        if lock_data:
            lock_data.update(kwargs)
            lock_data["updated_at"] = datetime.now().isoformat()
            
            with open(self.lock_file, 'w') as f:
                json.dump(lock_data, f, indent=2)
                
    def release_lock(self) -> None:
        """Clean up lock file"""
        if self.lock_file.exists():
            self.lock_file.unlink()
            
    def is_locked(self) -> bool:
        """Check if agent has a locked task"""
        return self.lock_file.exists()
        
    def get_lock_age_seconds(self) -> Optional[float]:
        """
        Get age of current lock in seconds
        
        Returns:
            Age in seconds if lock exists, None otherwise
        """
        lock_data = self.get_locked_task()
        if not lock_data:
            return None
            
        locked_at = datetime.fromisoformat(lock_data["locked_at"])
        return (datetime.now() - locked_at).total_seconds()