"""
Configuration management for Advanced Agent Runner
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration settings for the runner"""
    
    def __init__(self):
        # API settings
        self.api_key = os.environ.get('HEADLESS_PM_API_KEY') or \
                      os.environ.get('API_KEY_HEADLESS_PM') or \
                      os.environ.get('API_KEY')
        self.api_url = os.environ.get('HEADLESS_PM_API_URL', 'http://localhost:6969')
        
        # Paths
        self.worktree_base = Path(os.environ.get('HEADLESS_PM_WORKTREE_BASE', '/tmp/headless-pm-worktrees'))
        self.worktree_base.mkdir(parents=True, exist_ok=True)
        
        # Timeouts
        self.hook_timeout = int(os.environ.get('HEADLESS_PM_HOOK_TIMEOUT', '30'))
        self.claude_timeout = int(os.environ.get('HEADLESS_PM_CLAUDE_TIMEOUT', '600'))
        
        # Runner settings
        self.health_check_interval = int(os.environ.get('HEADLESS_PM_HEALTH_CHECK_INTERVAL', '300'))  # 5 minutes
        self.task_check_interval = int(os.environ.get('HEADLESS_PM_TASK_CHECK_INTERVAL', '30'))  # 30 seconds
        
        # Team roles path
        self.team_roles_dir = self._find_team_roles_dir()
        
    def _find_team_roles_dir(self) -> Optional[Path]:
        """Find the team_roles directory"""
        # Check various possible locations
        current_file = Path(__file__)
        candidates = [
            current_file.parent.parent / "team_roles",  # Next to advanced_runner
            current_file.parent.parent.parent / "team_roles",  # In agents/
            current_file.parent.parent.parent.parent / "agent_instructions",  # Project root
            Path.cwd() / "team_roles",  # Current directory
            Path.cwd() / "agent_instructions"  # Alternative name
        ]
        
        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return candidate
                
        return None
        
    def get_instructions_path(self, role: str) -> Optional[Path]:
        """Get path to role instructions"""
        if not self.team_roles_dir:
            return None
            
        instructions_file = self.team_roles_dir / f"{role}.md"
        return instructions_file if instructions_file.exists() else None
        
    def validate(self) -> tuple[bool, str]:
        """Validate configuration"""
        if not self.api_key:
            return False, "No API key found. Set HEADLESS_PM_API_KEY environment variable"
            
        if not self.team_roles_dir:
            return False, "Team roles directory not found"
            
        return True, "Configuration valid"