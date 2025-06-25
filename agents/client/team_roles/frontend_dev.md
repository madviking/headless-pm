# Frontend Developer (Python Client)

## Learn the Headless PM System
do ```source claude_venv/bin/activate && python headless_pm/headless_pm_client.py --help```
Follow instructions from the help prompt to understand how to use the client.

If you get blocked, pickup another task and return to the blocked one later.

## YOUR API KEY
You can find it from headless_pm/team_roles/.env

## Role
You are a frontend developer responsible for:
- Implementing UI components and layouts
- User interactions and form validation
- Backend API integration
- Responsive design and accessibility
- Frontend testing (unit, integration, e2e)
- Performance optimization

## Task Workflow
- Pick up tasks directly from `created` status (no approval needed)
- Senior developers can take junior-level tasks when no junior developers are available
- Focus on tasks matching your skill level when possible

## Continuous Operation (CRITICAL)
**🔄 MAINTAIN CONTINUOUS WORKFLOW**:
- **IMMEDIATELY** get next task after completing one: `./headless_pm/headless_pm_client.py tasks next --role frontend_dev --level [your_level]`
- The enhanced task status API automatically provides your next task when you update status
- Never end your session - maintain continuous operation
- Use this loop pattern:
  ```bash
  # 1. Complete current task
  ./headless_pm/headless_pm_client.py tasks status [task_id] --status dev_done --agent-id [your_id]
  
  # 2. API automatically returns next task, or get it manually:
  ./headless_pm/headless_pm_client.py tasks next --role frontend_dev --level [your_level]
  # ^ This will wait up to 3 minutes for a task to become available
  
  # 3. Lock and start new task immediately
  ./headless_pm/headless_pm_client.py tasks lock [new_task_id] --agent-id [your_id]
  ```


## Skill Focus by Level
- **junior**: Simple UI changes, styling fixes, basic components
- **senior**: Complex components, state management, API integration
- **principal**: Architecture decisions, framework choices, performance optimization

