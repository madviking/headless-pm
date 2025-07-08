"""
Git worktree management for feature branches
"""
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple


class GitWorktree:
    """Manages git worktrees for feature branches"""
    
    def __init__(self, base_path: Path):
        """
        Initialize worktree manager
        
        Args:
            base_path: Base repository path
        """
        self.base_path = Path(base_path)
        self.worktrees_dir = self.base_path / '.worktrees'
        self.worktrees_dir.mkdir(exist_ok=True)
        
    def create_for_task(self, task_id: int, branch_name: str) -> Path:
        """
        Create worktree for feature branch
        
        Args:
            task_id: Task ID for worktree naming
            branch_name: Git branch to check out
            
        Returns:
            Path to created worktree
            
        Raises:
            subprocess.CalledProcessError: If git command fails
        """
        worktree_path = self.worktrees_dir / f"task-{task_id}"
        
        # Remove existing worktree if it exists
        if worktree_path.exists():
            self.cleanup(task_id)
            
        # Create new worktree
        cmd = ['git', 'worktree', 'add', str(worktree_path), branch_name]
        subprocess.run(cmd, cwd=self.base_path, check=True, capture_output=True, text=True)
        
        return worktree_path
        
    def cleanup(self, task_id: int) -> None:
        """
        Remove worktree after task completion
        
        Args:
            task_id: Task ID of worktree to remove
        """
        worktree_path = self.worktrees_dir / f"task-{task_id}"
        
        if worktree_path.exists():
            # First, try git worktree remove
            try:
                cmd = ['git', 'worktree', 'remove', str(worktree_path)]
                subprocess.run(cmd, cwd=self.base_path, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                # Force removal if git command fails
                cmd = ['git', 'worktree', 'remove', '--force', str(worktree_path)]
                subprocess.run(cmd, cwd=self.base_path, check=True, capture_output=True, text=True)
                
    def list_worktrees(self) -> list:
        """
        List all active worktrees
        
        Returns:
            List of worktree info dictionaries
        """
        cmd = ['git', 'worktree', 'list', '--porcelain']
        result = subprocess.run(cmd, cwd=self.base_path, check=True, capture_output=True, text=True)
        
        worktrees = []
        current = {}
        
        for line in result.stdout.strip().split('\n'):
            if line.startswith('worktree '):
                if current:
                    worktrees.append(current)
                current = {'path': line[9:]}
            elif line.startswith('HEAD '):
                current['head'] = line[5:]
            elif line.startswith('branch '):
                current['branch'] = line[7:]
            elif line == '':
                if current:
                    worktrees.append(current)
                    current = {}
                    
        if current:
            worktrees.append(current)
            
        return worktrees
        
    def get_worktree_path(self, task_id: int) -> Optional[Path]:
        """
        Get path to existing worktree for task
        
        Args:
            task_id: Task ID to look up
            
        Returns:
            Path if worktree exists, None otherwise
        """
        worktree_path = self.worktrees_dir / f"task-{task_id}"
        return worktree_path if worktree_path.exists() else None
        
    def prune_worktrees(self) -> None:
        """Remove stale worktree references"""
        cmd = ['git', 'worktree', 'prune']
        subprocess.run(cmd, cwd=self.base_path, check=True)
        
    def create_branch_for_task(self, task_id: int, base_branch: str = 'main') -> str:
        """
        Create a new branch for a task
        
        Args:
            task_id: Task ID for branch naming
            base_branch: Branch to create from
            
        Returns:
            Name of created branch
        """
        branch_name = f"task-{task_id}"
        
        # Check if branch already exists
        cmd = ['git', 'branch', '--list', branch_name]
        result = subprocess.run(cmd, cwd=self.base_path, capture_output=True, text=True)
        
        if result.stdout.strip():
            # Branch exists, return it
            return branch_name
            
        # Create new branch
        cmd = ['git', 'branch', branch_name, base_branch]
        subprocess.run(cmd, cwd=self.base_path, check=True)
        
        return branch_name
        
    def is_clean(self, worktree_path: Path) -> Tuple[bool, str]:
        """
        Check if worktree has uncommitted changes
        
        Args:
            worktree_path: Path to worktree
            
        Returns:
            Tuple of (is_clean, status_message)
        """
        cmd = ['git', 'status', '--porcelain']
        result = subprocess.run(cmd, cwd=worktree_path, capture_output=True, text=True)
        
        if result.stdout.strip():
            return False, "Worktree has uncommitted changes"
        return True, "Worktree is clean"