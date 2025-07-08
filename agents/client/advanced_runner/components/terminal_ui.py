"""
Terminal UI with colored output and operator prompts
"""
import sys
from datetime import datetime
from typing import List, Optional


class TerminalUI:
    """Terminal output with colors and operator prompts"""
    
    # ANSI color codes
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def __init__(self, show_timestamp: bool = True):
        """
        Initialize Terminal UI
        
        Args:
            show_timestamp: Whether to show timestamps in output
        """
        self.show_timestamp = show_timestamp
        
    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        if self.show_timestamp:
            return f"[{datetime.now().strftime('%H:%M:%S')}] "
        return ""
        
    def info(self, message: str) -> None:
        """Standard info output"""
        timestamp = self._get_timestamp()
        print(f"{self.BLUE}{timestamp}{self.RESET}{message}")
        
    def success(self, message: str) -> None:
        """Success message with green checkmark"""
        timestamp = self._get_timestamp()
        print(f"{self.GREEN}✓ {timestamp}{message}{self.RESET}")
        
    def error(self, message: str) -> None:
        """Error message with red X"""
        timestamp = self._get_timestamp()
        print(f"{self.RED}✗ {timestamp}{message}{self.RESET}")
        
    def warning(self, message: str) -> None:
        """Warning message in yellow"""
        timestamp = self._get_timestamp()
        print(f"{self.YELLOW}⚠ {timestamp}{message}{self.RESET}")
        
    def header(self, message: str) -> None:
        """Section header with separator"""
        separator = "=" * 60
        print(f"\n{self.CYAN}{separator}{self.RESET}")
        print(f"{self.CYAN}{self.BOLD}{message}{self.RESET}")
        print(f"{self.CYAN}{separator}{self.RESET}\n")
        
    def task_info(self, task: dict) -> None:
        """Display task information"""
        print(f"\n{self.BLUE}Task Information:{self.RESET}")
        print(f"  ID: {task['id']}")
        print(f"  Title: {task['title']}")
        print(f"  Skill Level: {task.get('skill_level', 'N/A')}")
        print(f"  Complexity: {task.get('complexity', 'N/A')}")
        print(f"  Status: {task.get('status', 'N/A')}")
        if task.get('description'):
            print(f"  Description: {task['description'][:100]}...")
        print()
        
    def progress(self, message: str) -> None:
        """Progress indicator"""
        timestamp = self._get_timestamp()
        print(f"{self.CYAN}➤ {timestamp}{message}{self.RESET}")
        
    def prompt_operator(self, message: str, options: List[str]) -> str:
        """
        Blocking prompt for operator intervention
        
        Args:
            message: Prompt message to display
            options: List of options to present
            
        Returns:
            Selected option text
        """
        print(f"\n{self.YELLOW}{self.BOLD}⚠ Operator Intervention Required{self.RESET}")
        print(f"{self.YELLOW}{message}{self.RESET}\n")
        
        # Display options
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
            
        # Get user input
        while True:
            try:
                choice = input(f"\n{self.CYAN}Select option (1-{len(options)}): {self.RESET}")
                choice_idx = int(choice) - 1
                
                if 0 <= choice_idx < len(options):
                    selected = options[choice_idx]
                    print(f"{self.GREEN}Selected: {selected}{self.RESET}\n")
                    return selected
                else:
                    print(f"{self.RED}Invalid choice. Please enter a number between 1 and {len(options)}{self.RESET}")
                    
            except ValueError:
                print(f"{self.RED}Invalid input. Please enter a number{self.RESET}")
            except KeyboardInterrupt:
                print(f"\n{self.RED}Operation cancelled{self.RESET}")
                sys.exit(1)
                
    def confirm(self, message: str, default: bool = False) -> bool:
        """
        Yes/No confirmation prompt
        
        Args:
            message: Confirmation message
            default: Default value if user presses Enter
            
        Returns:
            True if confirmed, False otherwise
        """
        default_hint = " [Y/n]" if default else " [y/N]"
        
        try:
            response = input(f"{self.YELLOW}{message}{default_hint}: {self.RESET}").strip().lower()
            
            if not response:
                return default
                
            return response in ['y', 'yes']
            
        except KeyboardInterrupt:
            print(f"\n{self.RED}Operation cancelled{self.RESET}")
            return False
            
    def separator(self) -> None:
        """Print a separator line"""
        print(f"{self.CYAN}{'─' * 60}{self.RESET}")