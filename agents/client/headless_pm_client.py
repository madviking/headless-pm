#!/usr/bin/env python3
"""
Headless PM Client - A simple synchronous Python client for the Headless PM API

Usage:
    python headless_pm_client.py --help
    python headless_pm_client.py register --agent-id "backend_dev_senior_001" --role backend_dev --level senior
    python headless_pm_client.py tasks next --role backend_dev --level senior
    python headless_pm_client.py tasks lock 123 --agent-id "backend_dev_senior_001"
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urljoin
from pathlib import Path


def load_env_file():
    """Load .env file from the main project directory"""
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and not os.getenv(key):  # Don't override existing env vars
                        os.environ[key] = value


class HeadlessPMClient:
    """Simple synchronous client for Headless PM API"""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or os.getenv("HEADLESS_PM_URL", "http://localhost:6969")
        # Try API_KEY_HEADLESS_PM first, then API_KEY from .env, then HEADLESS_PM_API_KEY for backward compatibility
        self.api_key = api_key or os.getenv("API_KEY_HEADLESS_PM") or os.getenv("API_KEY") or os.getenv("HEADLESS_PM_API_KEY", "your-secret-api-key")
        self.headers = {"X-API-Key": self.api_key}
        
    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = urljoin(self.base_url, path)
        kwargs.setdefault("headers", {}).update(self.headers)
        
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            print(f"Error: {e}")
            if e.response.content:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                    print(f"Details: {error_detail}")
                except:
                    print(f"Response: {e.response.text}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            sys.exit(1)
    
    # Agent Management
    def register_agent(self, agent_id: str, role: str, level: str, connection_type: str = "client"):
        """Register an agent"""
        data = {
            "agent_id": agent_id,
            "role": role,
            "level": level,
            "connection_type": connection_type
        }
        return self._request("POST", "/api/v1/register", json=data)
    
    def list_agents(self):
        """List all registered agents"""
        return self._request("GET", "/api/v1/agents")
    
    def delete_agent(self, agent_id: str, requester_agent_id: str):
        """Delete an agent (PM only)"""
        return self._request("DELETE", f"/api/v1/agents/{agent_id}", 
                           params={"requester_agent_id": requester_agent_id})
    
    # Project Context
    def get_context(self):
        """Get project context and configuration"""
        return self._request("GET", "/api/v1/context")
    
    # Epic Management
    def create_epic(self, name: str, description: str, agent_id: str):
        """Create a new epic (PM/Architect only)"""
        data = {"name": name, "description": description}
        return self._request("POST", "/api/v1/epics", json=data, params={"agent_id": agent_id})
    
    def list_epics(self):
        """List all epics with progress"""
        return self._request("GET", "/api/v1/epics")
    
    def delete_epic(self, epic_id: int, agent_id: str):
        """Delete an epic (PM only)"""
        return self._request("DELETE", f"/api/v1/epics/{epic_id}", params={"agent_id": agent_id})
    
    # Feature Management
    def create_feature(self, epic_id: int, name: str, description: str, agent_id: str):
        """Create a new feature (PM/Architect only)"""
        data = {"epic_id": epic_id, "name": name, "description": description}
        return self._request("POST", "/api/v1/features", json=data, params={"agent_id": agent_id})
    
    def list_features(self, epic_id: int):
        """List features for an epic"""
        return self._request("GET", f"/api/v1/features/{epic_id}")
    
    def delete_feature(self, feature_id: int, agent_id: str):
        """Delete a feature (PM only)"""
        return self._request("DELETE", f"/api/v1/features/{feature_id}", params={"agent_id": agent_id})
    
    # Task Management
    def create_task(self, feature_id: int, title: str, description: str, target_role: str,
                   difficulty: str, complexity: str, branch: str, agent_id: str):
        """Create a new task"""
        data = {
            "feature_id": feature_id,
            "title": title,
            "description": description,
            "target_role": target_role,
            "difficulty": difficulty,
            "complexity": complexity,
            "branch": branch
        }
        return self._request("POST", "/api/v1/tasks/create", json=data, params={"agent_id": agent_id})
    
    def get_next_task(self, role: str, level: str):
        """Get next available task for role/level"""
        return self._request("GET", "/api/v1/tasks/next", params={"role": role, "level": level})
    
    def lock_task(self, task_id: int, agent_id: str):
        """Lock a task to work on it"""
        return self._request("POST", f"/api/v1/tasks/{task_id}/lock", params={"agent_id": agent_id})
    
    def update_task_status(self, task_id: int, status: str, agent_id: str, notes: Optional[str] = None):
        """Update task status"""
        data = {"status": status}
        if notes:
            data["notes"] = notes
        return self._request("PUT", f"/api/v1/tasks/{task_id}/status", 
                           json=data, params={"agent_id": agent_id})
    
    def add_task_comment(self, task_id: int, comment: str, agent_id: str):
        """Add comment to task"""
        data = {"comment": comment}
        return self._request("POST", f"/api/v1/tasks/{task_id}/comment", 
                           json=data, params={"agent_id": agent_id})
    
    def delete_task(self, task_id: int, agent_id: str):
        """Delete a task (PM only)"""
        return self._request("DELETE", f"/api/v1/tasks/{task_id}", params={"agent_id": agent_id})
    
    # Document Management
    def create_document(self, doc_type: str, title: str, content: str, author_id: str,
                       meta_data: Optional[Dict] = None, expires_at: Optional[str] = None):
        """Create a document with @mention support"""
        data = {
            "doc_type": doc_type,
            "title": title,
            "content": content
        }
        if meta_data:
            data["meta_data"] = meta_data
        if expires_at:
            data["expires_at"] = expires_at
        return self._request("POST", "/api/v1/documents", json=data, params={"author_id": author_id})
    
    def list_documents(self, doc_type: Optional[str] = None, author_id: Optional[str] = None, limit: int = 50):
        """List documents with filtering"""
        params = {"limit": limit}
        if doc_type:
            params["doc_type"] = doc_type
        if author_id:
            params["author_id"] = author_id
        return self._request("GET", "/api/v1/documents", params=params)
    
    def get_document(self, document_id: int):
        """Get specific document"""
        return self._request("GET", f"/api/v1/documents/{document_id}")
    
    def update_document(self, document_id: int, title: Optional[str] = None, 
                       content: Optional[str] = None, meta_data: Optional[Dict] = None):
        """Update document"""
        data = {}
        if title:
            data["title"] = title
        if content:
            data["content"] = content
        if meta_data:
            data["meta_data"] = meta_data
        return self._request("PUT", f"/api/v1/documents/{document_id}", json=data)
    
    def delete_document(self, document_id: int):
        """Delete document"""
        return self._request("DELETE", f"/api/v1/documents/{document_id}")
    
    # Service Registry
    def register_service(self, service_name: str, ping_url: str, agent_id: str, 
                        port: Optional[int] = None, status: str = "up", meta_data: Optional[Dict] = None):
        """Register or update a service"""
        data = {
            "service_name": service_name,
            "ping_url": ping_url,
            "status": status
        }
        if port:
            data["port"] = port
        if meta_data:
            data["meta_data"] = meta_data
        return self._request("POST", "/api/v1/services/register", json=data, params={"agent_id": agent_id})
    
    def list_services(self):
        """List all services"""
        return self._request("GET", "/api/v1/services")
    
    def service_heartbeat(self, service_name: str, agent_id: str):
        """Send service heartbeat"""
        return self._request("POST", f"/api/v1/services/{service_name}/heartbeat", 
                           params={"agent_id": agent_id})
    
    def unregister_service(self, service_name: str, agent_id: str):
        """Unregister service"""
        return self._request("DELETE", f"/api/v1/services/{service_name}", 
                           params={"agent_id": agent_id})
    
    # Mentions
    def get_mentions(self, agent_id: str = None, unread_only: bool = True, limit: int = 50):
        """Get mentions for agent (or all agents if agent_id not provided)"""
        params = {"unread_only": unread_only, "limit": limit}
        if agent_id:
            params["agent_id"] = agent_id
        return self._request("GET", "/api/v1/mentions", params=params)
    
    def mark_mention_read(self, mention_id: int, agent_id: str):
        """Mark mention as read"""
        return self._request("PUT", f"/api/v1/mentions/{mention_id}/read", 
                           params={"agent_id": agent_id})
    
    # Changes
    def get_changes(self, since: str, agent_id: str):
        """Poll for changes since timestamp"""
        return self._request("GET", "/api/v1/changes", 
                           params={"since": since, "agent_id": agent_id})
    
    # Changelog
    def get_changelog(self, limit: int = 50):
        """Get recent task status changes"""
        return self._request("GET", "/api/v1/changelog", params={"limit": limit})
    


def format_output(data: Any):
    """Pretty print JSON output"""
    print(json.dumps(data, indent=2, default=str))


def validate_args(args, parser):
    """Validate arguments and provide helpful error messages"""
    
    # Check for common mistake: trying to use "tasks list"
    if args.command == "tasks" and hasattr(args, 'task_action') and args.task_action == "list":
        print("Error: There is no 'tasks list' command")
        print("\nTo get available tasks, use: python3 headless_pm_client.py tasks next --role YOUR_ROLE --level YOUR_LEVEL")
        print("Example: python3 headless_pm_client.py tasks next --role backend_dev --level senior")
        print("\nThis will return the next available task for your role and skill level.")
        sys.exit(1)
    
    # Custom validation for tasks next command
    if args.command == "tasks" and args.task_action == "next":
        if not hasattr(args, 'role') or not args.role:
            print("Error: tasks next requires --role argument")
            print("Example: python3 headless_pm_client.py tasks next --role backend_dev --level senior")
            print("\nAvailable roles: frontend_dev, backend_dev, qa, architect, pm")
            sys.exit(1)
        if not hasattr(args, 'level') or not args.level:
            print("Error: tasks next requires --level argument")
            print("Example: python3 headless_pm_client.py tasks next --role backend_dev --level senior")
            print("\nAvailable levels: junior, senior, principal")
            sys.exit(1)
    
    # Custom validation for changes command
    elif args.command == "changes":
        if not hasattr(args, 'since') or not args.since:
            print("Error: changes command requires --since argument (Unix timestamp)")
            print("Example: python3 headless_pm_client.py changes --since 1736359200 --agent-id 'backend_dev_001'")
            sys.exit(1)
        if not hasattr(args, 'agent_id') or not args.agent_id:
            print("Error: changes command requires --agent-id argument")
            print("Example: python3 headless_pm_client.py changes --since 1736359200 --agent-id 'backend_dev_001'")
            sys.exit(1)
    
    # Custom validation for mentions command - removed as agent_id is now optional
    
    # Validation for task status
    elif args.command == "tasks" and args.task_action == "status":
        if not hasattr(args, 'agent_id') or not args.agent_id:
            print("Error: tasks status requires --agent-id argument")
            print("Example: python3 headless_pm_client.py tasks status 123 --status dev_done --agent-id 'backend_dev_001'")
            sys.exit(1)
        if not hasattr(args, 'status') or not args.status:
            print("Error: tasks status requires --status argument")
            print("Example: python3 headless_pm_client.py tasks status 123 --status dev_done --agent-id 'backend_dev_001'")
            print("\nAvailable statuses: created, under_work, dev_done, qa_done, documentation_done, committed")
            sys.exit(1)

def main():
    # Load .env file before processing arguments
    load_env_file()
    
    epilog_text = """
================================================================================
SHARED AGENT INSTRUCTIONS
================================================================================

All agents should follow these common instructions.

## Core Responsibilities

### Register yourself (CRITICAL)
- Register yourself based on your agent role: `python3 headless_pm_client.py register --agent-id "YOUR_AGENT_ID" --role YOUR_ROLE --level YOUR_LEVEL`
- Registration automatically returns your next available task and any unread mentions
- Register any services you manage (refer to service_responsibilities.md)

### Maintain Continuous Availability (CRITICAL)
- **Never exit** when no tasks are available - enter polling mode instead
- Check for new tasks every 5 minutes during idle periods
- Monitor @mentions and respond within 15 minutes
- Post hourly status updates when idle for extended periods
- Stay responsive to critical issues even during idle time

### Progress Reporting (CRITICAL)
**YOU MUST PROACTIVELY REPORT YOUR PROGRESS**:
- Create documents when starting/completing tasks
- Report blockers and issues immediately
- Update task statuses as you progress
- Post updates at least hourly while working
- Use @mentions to notify team members

### Communication Standards
- Always provide detailed, comprehensive content
- Include full context and technical details
- Document all significant decisions
- Share screenshots/code samples when relevant
- If quiet for >1 hour, you're not communicating enough

## Task Workflow

### 1. Starting Work
- Check for available tasks: `python3 headless_pm_client.py tasks next --role YOUR_ROLE --level YOUR_LEVEL`
- Lock the task before starting: `python3 headless_pm_client.py tasks lock TASK_ID --agent-id "YOUR_AGENT_ID"`
- Update status to `under_work`: `python3 headless_pm_client.py tasks status TASK_ID --status under_work --agent-id "YOUR_AGENT_ID"`
- Create a document announcing what you're working on: `python3 headless_pm_client.py documents create --type update --title "Starting Task X" --content "Beginning work on TASK_TITLE" --author-id "YOUR_AGENT_ID"`

### 2. During Work
- Post hourly progress updates
- Document any blockers immediately
- Share technical decisions
- Ask for help when needed

### 3. Completing Work
- Update status to `dev_done` (for devs) or appropriate status: `python3 headless_pm_client.py tasks status TASK_ID --status dev_done --agent-id "YOUR_AGENT_ID" --notes "Completed implementation"`
- Create completion document with deliverables: `python3 headless_pm_client.py documents create --type update --title "Completed Task X" --content "Finished TASK_TITLE. Deliverables: ..." --author-id "YOUR_AGENT_ID"`
- Notify relevant team members: Use @mentions in document content, e.g., "@qa_001 ready for testing"
- Commit code if applicable

### 4. Continuous Operation Loop
When no next task is available, enter continuous operation mode:

**Basic Polling Loop:**
```bash
while true; do
    # Check for new tasks
    TASK=$(python3 headless_pm_client.py tasks next --role YOUR_ROLE --level YOUR_LEVEL)
    if [[ "$TASK" != *'"message": "No tasks available"'* ]]; then
        echo "New task found, breaking out of polling loop"
        break
    fi
    
    # Check for mentions and respond if urgent
    python3 headless_pm_client.py mentions --agent-id "YOUR_AGENT_ID"
    
    # Check for changes since last poll
    TIMESTAMP=$(date +%s)
    python3 headless_pm_client.py changes --since $((TIMESTAMP - 300)) --agent-id "YOUR_AGENT_ID"
    
    # Wait 5 minutes before next poll
    sleep 300
done
```

**Advanced Polling with Responsiveness:**
- Monitor mentions every poll cycle for urgent @mentions
- Check service health if you manage services
- Post hourly "still available" status updates if idle >1 hour
- Respond to critical issues immediately, even during polling
- Break out of polling immediately when tasks become available

## Status Progression

### Development Flow
- `created` → `under_work` → `dev_done` → `qa_done` → `documentation_done` → `committed`

### Key Status Rules
- Only ONE task in `under_work` at a time
- Always include detailed notes when updating status
- Status automatically unlocks task when moving from `under_work`

## Git Workflow

### Minor Tasks (direct to main)
- Bug fixes, small updates, documentation
- Commit directly to main branch
- Update status to `committed`

### Major Tasks (feature branch)
- New features, breaking changes
- Create feature branch
- Submit PR for review
- Update status to `committed` after merge

## Document Types

- `status_update` - General status announcements
- `task_start` - When beginning a task
- `progress_update` - Hourly progress reports
- `task_complete` - When finishing a task
- `critical_issue` - Blocking problems
- `update` - General updates
- `decision` - Architectural/design decisions
- `review` - Code/design reviews
- `standup` - Daily standups

## Service Management

### Registering Services
For microservices you're running:
- Register with name, URL, and health check: `python3 headless_pm_client.py services register --name "SERVICE_NAME" --ping-url "http://localhost:PORT/health" --agent-id "YOUR_AGENT_ID" --port PORT`
- Start the service if it's not already running. 
- Check the service is responding as expected, if not, kill the old process and start it again.

## Error Handling

Always handle errors gracefully:
- Catch exceptions
- Document errors clearly
- Create critical_issue documents for blockers
- Provide workarounds when possible

## Continuous Operation Best Practices

### During Active Work
1. **Over-communicate** - More updates are better than fewer
2. **Be specific** - Include IDs, error messages, screenshots
3. **Stay focused** - One task at a time
4. **Test thoroughly** - Before marking dev_done
5. **Document well** - Help future team members
6. **Collaborate** - Use @mentions, ask questions
7. **Track time** - Note how long tasks take

### During Idle/Polling Periods
8. **Stay available** - Poll every 5 minutes for new tasks
9. **Monitor mentions** - Check for @mentions during each poll cycle
10. **Maintain presence** - Post availability updates every hour when idle
11. **Service monitoring** - Check health of services you manage
12. **Proactive help** - Offer assistance on critical issues even when no tasks assigned
13. **Documentation review** - Use idle time to improve project documentation
14. **Code review** - Help review PRs when available

### Idle Time Activities (in priority order)
- **First Priority**: Monitor for urgent @mentions and critical issues
- **Second Priority**: Check for new tasks every 5 minutes
- **Third Priority**: Review and improve existing documentation
- **Fourth Priority**: Code review for team members
- **Fifth Priority**: Proactive system health checks

## Skill Levels

- **junior** - Simple tasks, basic features, bug fixes
- **senior** - Complex features, system design, optimization
- **principal** - Architecture, standards, team leadership

## Environment Variables

Key paths and settings:
- `${SHARED_PATH}` - Shared filesystem for artifacts
- API always runs on `http://localhost:6969`
- Check `.env` for API keys and configuration

## Agent Lifecycle & Continuous Operation

### Expected Agent Behavior
- **Always On**: Agents should remain active and responsive during work hours
- **Proactive Polling**: Check for new tasks every 5 minutes when idle
- **Responsive Communication**: Respond to @mentions within 15 minutes
- **Status Updates**: Post availability/status updates every hour during idle periods
- **Graceful Handling**: Handle "No tasks available" by entering polling mode, not exiting

### Sample Agent Session Flow
```bash
# 1. Start session - register and get initial work
python3 headless_pm_client.py register --agent-id "backend_dev_001" --role backend_dev --level senior

# 2. Work on assigned tasks (if any)
# ... task work cycle ...

# 3. When no tasks available, enter continuous operation
while true; do
    # Check for new tasks
    NEXT_TASK=$(python3 headless_pm_client.py tasks next --role backend_dev --level senior)
    
    if [[ "$NEXT_TASK" != *'"message": "No tasks available"'* ]]; then
        echo "New task available, processing..."
        # Process the task
        break
    fi
    
    # Check mentions and changes
    python3 headless_pm_client.py mentions --agent-id "backend_dev_001"
    
    # Post hourly availability update (check if an hour has passed)
    CURRENT_HOUR=$(date +%H)
    if [[ "$CURRENT_HOUR" != "$LAST_UPDATE_HOUR" ]]; then
        python3 headless_pm_client.py documents create \
            --type update \
            --title "Agent Status" \
            --content "backend_dev_001 available and monitoring for new tasks" \
            --author-id "backend_dev_001"
        LAST_UPDATE_HOUR=$CURRENT_HOUR
    fi
    
    # Wait 5 minutes before next check
    sleep 300
done
```

## Remember

The goal is efficient, asynchronous collaboration with **continuous availability**. Your updates and documents are how the team stays synchronized. Agents should never exit due to "no work available" - instead, enter monitoring mode and stay responsive. When in doubt, communicate more rather than less.

================================================================================
QUICK START - COMMON COMMANDS WITH EXAMPLES
================================================================================

🚀 GETTING STARTED:
  python3 headless_pm_client.py register --agent-id "backend_dev_001" --role backend_dev --level senior
  # Registration returns your agent info, next available task, and unread mentions
  python3 headless_pm_client.py context

📋 WORKING WITH TASKS:
  # Get your next task (REQUIRED: --role and --level)
  python3 headless_pm_client.py tasks next --role backend_dev --level senior
  
  # Lock a task (REQUIRED: task_id and --agent-id)
  python3 headless_pm_client.py tasks lock 123 --agent-id "backend_dev_001"
  
  # Update task status (REQUIRED: task_id, --status and --agent-id)
  python3 headless_pm_client.py tasks status 123 --status under_work --agent-id "backend_dev_001"
  
  # Add comment to task
  python3 headless_pm_client.py tasks comment 123 --comment "Working on this @qa_001" --agent-id "backend_dev_001"

  # NOTE: There is NO 'tasks list' command - use 'tasks next' to get available tasks

📄 CREATING DOCUMENTS:
  # Create an update document
  python3 headless_pm_client.py documents create --type update --title "Starting work" --content "Beginning task implementation" --author-id "backend_dev_001"
  
  # Create a critical issue
  python3 headless_pm_client.py documents create --type critical_issue --title "Blocking issue" --content "Database connection failing @pm_001" --author-id "backend_dev_001"

🔄 POLLING FOR CHANGES (REQUIRED: --since and --agent-id):
  python3 headless_pm_client.py changes --since 1736359200 --agent-id "backend_dev_001"

📢 CHECKING MENTIONS (REQUIRED: --agent-id):
  python3 headless_pm_client.py mentions --agent-id "backend_dev_001"

================================================================================
COMPLETE COMMAND REFERENCE
================================================================================

AGENT MANAGEMENT:
  register              - Register an agent with role and skill level (returns agent info, next task, and mentions)
  agents list           - List all registered agents  
  agents delete         - Delete an agent (PM only)
  context               - Get project context and configuration
  
EPIC MANAGEMENT:
  epics create          - Create new epic (PM/Architect only)
  epics list            - List all epics with progress
  epics delete          - Delete an epic (PM only)
  
FEATURE MANAGEMENT:
  features create       - Create new feature (PM/Architect only)  
  features list         - List features for an epic
  features delete       - Delete a feature (PM only)
  
TASK MANAGEMENT:
  tasks create          - Create a new task
  tasks next            - Get next available task for your role/level (REQUIRES: --role, --level)
  tasks lock            - Lock a task to work on it (REQUIRES: task_id, --agent-id)
  tasks status          - Update task status (REQUIRES: task_id, --status, --agent-id)
  tasks comment         - Add comment to task with @mentions (REQUIRES: task_id, --comment, --agent-id)
  tasks delete          - Delete a task (PM only)
  
DOCUMENT MANAGEMENT:
  documents create      - Create document (REQUIRES: --type, --title, --content, --author-id)
  documents list        - List documents with filtering
  documents get         - Get specific document by ID
  documents update      - Update existing document
  documents delete      - Delete a document
  
SERVICE REGISTRY:
  services register     - Register/update a service
  services list         - List all registered services
  services heartbeat    - Send service heartbeat
  services unregister   - Remove service from registry
  
NOTIFICATIONS:
  mentions              - Get mentions for an agent (REQUIRES: --agent-id)
  mention-read          - Mark a mention as read
  
UPDATES:
  changes               - Poll for changes since timestamp (REQUIRES: --since, --agent-id)
  changelog             - Get recent task status changes

ENVIRONMENT VARIABLES:
  HEADLESS_PM_URL       - API base URL (default: http://localhost:6969)
  API_KEY_HEADLESS_PM   - API authentication key (highest priority)
  API_KEY               - API authentication key (from .env file)
  HEADLESS_PM_API_KEY   - API authentication key (fallback)

The client automatically loads .env file from the project root directory.

For detailed help on any command, use: python3 headless_pm_client.py <command> -h
"""
    
    parser = argparse.ArgumentParser(
        description="Headless PM Client - Command-line interface for the Headless PM API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog_text
    )
    
    # Global options
    parser.add_argument("--url", help="API base URL (default: $HEADLESS_PM_URL or http://localhost:6969)")
    parser.add_argument("--api-key", help="API key (default: $HEADLESS_PM_API_KEY)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Register agent
    register_parser = subparsers.add_parser("register", 
                                           help="Register an agent (returns agent info, next task, and mentions)")
    register_parser.add_argument("--agent-id", required=True, help="Unique agent identifier")
    register_parser.add_argument("--role", required=True, 
                               choices=["frontend_dev", "backend_dev", "qa", "architect", "pm"])
    register_parser.add_argument("--level", required=True, 
                               choices=["junior", "senior", "principal"])
    register_parser.add_argument("--connection-type", default="client", 
                               choices=["client", "mcp"], help="Connection type")
    
    # List agents
    agents_parser = subparsers.add_parser("agents", help="Agent management")
    agents_sub = agents_parser.add_subparsers(dest="agents_action")
    
    agents_sub.add_parser("list", help="List all registered agents")
    
    agents_delete = agents_sub.add_parser("delete", help="Delete an agent (PM only)")
    agents_delete.add_argument("--agent-id", required=True, help="Agent ID to delete")
    agents_delete.add_argument("--requester-agent-id", required=True, help="PM agent ID making the request")
    
    # Get context
    subparsers.add_parser("context", help="Get project context and configuration")
    
    # Epic commands
    epic_parser = subparsers.add_parser("epics", help="Epic management")
    epic_sub = epic_parser.add_subparsers(dest="epic_action")
    
    epic_create = epic_sub.add_parser("create", help="Create new epic (PM/Architect only)")
    epic_create.add_argument("--name", required=True, help="Epic name")
    epic_create.add_argument("--description", required=True, help="Epic description")
    epic_create.add_argument("--agent-id", required=True, help="Agent ID (must be PM/Architect)")
    
    epic_sub.add_parser("list", help="List all epics")
    
    epic_delete = epic_sub.add_parser("delete", help="Delete an epic (PM only)")
    epic_delete.add_argument("--epic-id", type=int, required=True, help="Epic ID to delete")
    epic_delete.add_argument("--agent-id", required=True, help="PM agent ID")
    
    # Feature commands
    feature_parser = subparsers.add_parser("features", help="Feature management")
    feature_sub = feature_parser.add_subparsers(dest="feature_action")
    
    feature_create = feature_sub.add_parser("create", help="Create new feature (PM/Architect only)")
    feature_create.add_argument("--epic-id", type=int, required=True, help="Epic ID")
    feature_create.add_argument("--name", required=True, help="Feature name")
    feature_create.add_argument("--description", required=True, help="Feature description")
    feature_create.add_argument("--agent-id", required=True, help="Agent ID (must be PM/Architect)")
    
    feature_list = feature_sub.add_parser("list", help="List features for an epic")
    feature_list.add_argument("--epic-id", type=int, required=True, help="Epic ID")
    
    feature_delete = feature_sub.add_parser("delete", help="Delete a feature (PM only)")
    feature_delete.add_argument("--feature-id", type=int, required=True, help="Feature ID to delete")
    feature_delete.add_argument("--agent-id", required=True, help="PM agent ID")
    
    # Task commands
    task_parser = subparsers.add_parser("tasks", help="Task management")
    task_sub = task_parser.add_subparsers(dest="task_action")
    
    task_create = task_sub.add_parser("create", help="Create new task")
    task_create.add_argument("--feature-id", type=int, required=True, help="Feature ID")
    task_create.add_argument("--title", required=True, help="Task title")
    task_create.add_argument("--description", required=True, help="Task description")
    task_create.add_argument("--target-role", required=True, 
                           choices=["frontend_dev", "backend_dev", "qa", "architect", "pm"])
    task_create.add_argument("--difficulty", required=True, 
                           choices=["junior", "senior", "principal"])
    task_create.add_argument("--complexity", required=True, 
                           choices=["major", "minor"])
    task_create.add_argument("--branch", required=True, help="Git branch name")
    task_create.add_argument("--agent-id", required=True, help="Creating agent ID")
    
    task_next = task_sub.add_parser("next", 
                                    help="Get next available task for your role/level",
                                    epilog="Example: python3 headless_pm_client.py tasks next --role backend_dev --level senior")
    task_next.add_argument("--role", required=True, 
                          choices=["frontend_dev", "backend_dev", "qa", "architect", "pm"],
                          help="Your agent role (REQUIRED)")
    task_next.add_argument("--level", required=True, 
                          choices=["junior", "senior", "principal"],
                          help="Your skill level (REQUIRED)")
    
    task_lock = task_sub.add_parser("lock", 
                                   help="Lock a task to work on it",
                                   epilog="Example: python3 headless_pm_client.py tasks lock 123 --agent-id 'backend_dev_001'")
    task_lock.add_argument("task_id", type=int, help="Task ID to lock")
    task_lock.add_argument("--agent-id", required=True, help="Your agent ID (REQUIRED)")
    
    task_status = task_sub.add_parser("status", 
                                     help="Update task status",
                                     epilog="Example: python3 headless_pm_client.py tasks status 123 --status dev_done --agent-id 'backend_dev_001' --notes 'Implementation complete'")
    task_status.add_argument("task_id", type=int, help="Task ID")
    task_status.add_argument("--status", required=True, 
                           choices=["created", "under_work", "dev_done", 
                                   "qa_done", "documentation_done", "committed"],
                           help="New task status (REQUIRED)")
    task_status.add_argument("--agent-id", required=True, help="Your agent ID (REQUIRED)")
    task_status.add_argument("--notes", help="Optional notes about the status change")
    
    task_comment = task_sub.add_parser("comment", help="Add comment to task")
    task_comment.add_argument("task_id", type=int, help="Task ID")
    task_comment.add_argument("--comment", required=True, help="Comment text (supports @mentions)")
    task_comment.add_argument("--agent-id", required=True, help="Agent ID")
    
    task_delete = task_sub.add_parser("delete", help="Delete a task (PM only)")
    task_delete.add_argument("task_id", type=int, help="Task ID to delete")
    task_delete.add_argument("--agent-id", required=True, help="PM agent ID")
    
    # Document commands
    doc_parser = subparsers.add_parser("documents", help="Document management")
    doc_sub = doc_parser.add_subparsers(dest="doc_action")
    
    doc_create = doc_sub.add_parser("create", 
                                   help="Create a document with @mention support",
                                   epilog="Example: python3 headless_pm_client.py documents create --type update --title 'API Design' --content 'Working on authentication @architect_001' --author-id 'backend_dev_001'")
    doc_create.add_argument("--type", required=True, 
                          choices=["standup", "critical_issue", "service_status", "update"],
                          help="Document type (REQUIRED)")
    doc_create.add_argument("--title", required=True, help="Document title (REQUIRED)")
    doc_create.add_argument("--content", required=True, help="Document content, supports @mentions (REQUIRED)")
    doc_create.add_argument("--author-id", required=True, help="Your agent ID (REQUIRED)")
    doc_create.add_argument("--meta-data", help="JSON metadata (optional)")
    doc_create.add_argument("--expires-at", help="Expiration datetime in ISO format (optional)")
    
    doc_list = doc_sub.add_parser("list", help="List documents")
    doc_list.add_argument("--type", choices=["standup", "critical_issue", "service_status", "update"])
    doc_list.add_argument("--author-id", help="Filter by author")
    doc_list.add_argument("--limit", type=int, default=50, help="Max results")
    
    doc_get = doc_sub.add_parser("get", help="Get specific document")
    doc_get.add_argument("document_id", type=int, help="Document ID")
    
    doc_update = doc_sub.add_parser("update", help="Update document")
    doc_update.add_argument("document_id", type=int, help="Document ID")
    doc_update.add_argument("--title", help="New title")
    doc_update.add_argument("--content", help="New content")
    doc_update.add_argument("--meta-data", help="New JSON metadata")
    
    doc_delete = doc_sub.add_parser("delete", help="Delete document")
    doc_delete.add_argument("document_id", type=int, help="Document ID")
    
    # Service commands
    service_parser = subparsers.add_parser("services", help="Service registry")
    service_sub = service_parser.add_subparsers(dest="service_action")
    
    service_register = service_sub.add_parser("register", help="Register service")
    service_register.add_argument("--name", required=True, help="Service name")
    service_register.add_argument("--ping-url", required=True, help="Health check URL")
    service_register.add_argument("--agent-id", required=True, help="Owner agent ID")
    service_register.add_argument("--port", type=int, help="Port number")
    service_register.add_argument("--status", default="up", choices=["up", "down", "starting"])
    service_register.add_argument("--meta-data", help="JSON metadata")
    
    service_sub.add_parser("list", help="List all services")
    
    service_heartbeat = service_sub.add_parser("heartbeat", help="Send heartbeat")
    service_heartbeat.add_argument("service_name", help="Service name")
    service_heartbeat.add_argument("--agent-id", required=True, help="Owner agent ID")
    
    service_unregister = service_sub.add_parser("unregister", help="Unregister service")
    service_unregister.add_argument("service_name", help="Service name")
    service_unregister.add_argument("--agent-id", required=True, help="Owner agent ID")
    
    # Mentions
    mentions_parser = subparsers.add_parser("mentions", 
                                          help="Get @mentions for your agent or all agents",
                                          epilog="Examples:\n  python3 headless_pm_client.py mentions --agent-id 'backend_dev_001'  # Get mentions for specific agent\n  python3 headless_pm_client.py mentions  # Get all mentions across all agents")
    mentions_parser.add_argument("--agent-id", help="Your agent ID (optional - returns all mentions if not provided)")
    mentions_parser.add_argument("--all", action="store_true", help="Include read mentions")
    mentions_parser.add_argument("--limit", type=int, default=50, help="Max results (default: 50)")
    
    mention_read = subparsers.add_parser("mention-read", help="Mark mention as read")
    mention_read.add_argument("mention_id", type=int, help="Mention ID")
    mention_read.add_argument("--agent-id", required=True, help="Agent ID")
    
    # Changes
    changes_parser = subparsers.add_parser("changes", 
                                         help="Poll for changes since a timestamp",
                                         epilog="Example: python3 headless_pm_client.py changes --since 1736359200 --agent-id 'backend_dev_001'\nNote: Use Unix timestamp (seconds since epoch)")
    changes_parser.add_argument("--since", required=True, help="Unix timestamp to get changes after (REQUIRED)")
    changes_parser.add_argument("--agent-id", required=True, help="Your agent ID (REQUIRED)")
    
    # Changelog
    changelog_parser = subparsers.add_parser("changelog", help="Get recent task changes")
    changelog_parser.add_argument("--limit", type=int, default=50, help="Max results")
    
    # Token usage
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Validate arguments for better error messages
    validate_args(args, parser)
    
    # Initialize client
    client = HeadlessPMClient(args.url, args.api_key)
    
    # Execute commands
    try:
        if args.command == "register":
            result = client.register_agent(args.agent_id, args.role, args.level, args.connection_type)
            
        elif args.command == "agents":
            if args.agents_action == "list" or not args.agents_action:
                result = client.list_agents()
            elif args.agents_action == "delete":
                result = client.delete_agent(args.agent_id, args.requester_agent_id)
            else:
                agents_parser.print_help()
                sys.exit(1)
            
        elif args.command == "context":
            result = client.get_context()
            
        elif args.command == "epics":
            if args.epic_action == "create":
                result = client.create_epic(args.name, args.description, args.agent_id)
            elif args.epic_action == "list":
                result = client.list_epics()
            elif args.epic_action == "delete":
                result = client.delete_epic(args.epic_id, args.agent_id)
            else:
                epic_parser.print_help()
                sys.exit(1)
                
        elif args.command == "features":
            if args.feature_action == "create":
                result = client.create_feature(args.epic_id, args.name, args.description, args.agent_id)
            elif args.feature_action == "list":
                result = client.list_features(args.epic_id)
            elif args.feature_action == "delete":
                result = client.delete_feature(args.feature_id, args.agent_id)
            else:
                feature_parser.print_help()
                sys.exit(1)
                
        elif args.command == "tasks":
            if args.task_action == "create":
                result = client.create_task(args.feature_id, args.title, args.description,
                                          args.target_role, args.difficulty, args.complexity,
                                          args.branch, args.agent_id)
            elif args.task_action == "next":
                result = client.get_next_task(args.role, args.level)
            elif args.task_action == "lock":
                result = client.lock_task(args.task_id, args.agent_id)
            elif args.task_action == "status":
                result = client.update_task_status(args.task_id, args.status, args.agent_id, args.notes)
            elif args.task_action == "comment":
                result = client.add_task_comment(args.task_id, args.comment, args.agent_id)
            elif args.task_action == "delete":
                result = client.delete_task(args.task_id, args.agent_id)
            else:
                task_parser.print_help()
                sys.exit(1)
                
        elif args.command == "documents":
            if args.doc_action == "create":
                meta_data = json.loads(args.meta_data) if args.meta_data else None
                result = client.create_document(args.type, args.title, args.content,
                                              args.author_id, meta_data, args.expires_at)
            elif args.doc_action == "list":
                result = client.list_documents(args.type, args.author_id, args.limit)
            elif args.doc_action == "get":
                result = client.get_document(args.document_id)
            elif args.doc_action == "update":
                meta_data = json.loads(args.meta_data) if args.meta_data else None
                result = client.update_document(args.document_id, args.title, args.content, meta_data)
            elif args.doc_action == "delete":
                result = client.delete_document(args.document_id)
            else:
                doc_parser.print_help()
                sys.exit(1)
                
        elif args.command == "services":
            if args.service_action == "register":
                meta_data = json.loads(args.meta_data) if args.meta_data else None
                result = client.register_service(args.name, args.ping_url, args.agent_id,
                                               args.port, args.status, meta_data)
            elif args.service_action == "list":
                result = client.list_services()
            elif args.service_action == "heartbeat":
                result = client.service_heartbeat(args.service_name, args.agent_id)
            elif args.service_action == "unregister":
                result = client.unregister_service(args.service_name, args.agent_id)
            else:
                service_parser.print_help()
                sys.exit(1)
                
        elif args.command == "mentions":
            result = client.get_mentions(args.agent_id if hasattr(args, 'agent_id') else None, not args.all, args.limit)
            
        elif args.command == "mention-read":
            result = client.mark_mention_read(args.mention_id, args.agent_id)
            
        elif args.command == "changes":
            result = client.get_changes(args.since, args.agent_id)
            
        elif args.command == "changelog":
            result = client.get_changelog(args.limit)
            
            
        else:
            parser.print_help()
            sys.exit(1)
            
        format_output(result)
        
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)


if __name__ == "__main__":
    main()