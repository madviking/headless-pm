# Shared Agent Instructions

This file contains common instructions for all Headless PM agents, whether using MCP or Python client.

## Getting Started with MCP in Claude Code

**⚠️ CRITICAL: Read `CLAUDE_CODE_IMPORTANT.md` first if you're using Claude Code!**

**IMPORTANT**: When using Claude Code with MCP, use natural language. Do NOT try to run commands.

### How to Register (Example)
Say: "I need to register as a backend developer named backend_001 with senior level"
(Claude Code will automatically use the MCP register_agent tool)

### How to Get Tasks (Example)  
Say: "Show me the next available task"
(Claude Code will automatically use the MCP get_next_task tool)

### What NOT to do
- Don't try: `python mcp-bridge.py register_agent ...`
- Don't try: `Register me as agent ...` (as a command)
- Don't try to call MCP tools directly

### What TO do
- Use conversational language: "I'd like to register as..."
- Be descriptive: "Please create a new task for..."
- Let Claude Code handle the MCP protocol

## Core Responsibilities
### Register yourself (CRITICAL)
- Register yourself based on your agent role
- Register any services you manage (refer to service_responsibilities.md)

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
- Check for available tasks
- Lock the task before starting
- Update status to `under_work`
- Create a document announcing what you're working on

### 2. During Work
- Post hourly progress updates
- Document any blockers immediately
- Share technical decisions
- Ask for help when needed

### 3. Completing Work
- Update status to `dev_done` (for devs) or appropriate status
- Create completion document with deliverables
- Notify relevant team members
- Commit code if applicable

### 4. Continuous Work Loop (CRITICAL)
**🔄 NEVER STOP WORKING - MAINTAIN CONTINUOUS OPERATION**:
- **IMMEDIATELY** check for next task after completing one
- If no real tasks available, continue monitoring (system will provide waiting tasks)
- Poll for new tasks every 5 minutes during waiting periods
- Never end your session - maintain continuous operation
- The enhanced task status update API automatically provides your next task
- Always transition directly from one task to the next without gaps

## Status Progression

### Development Flow
- `created` → `under_work` → `dev_done` → `testing` → `qa_done` → `documentation_done` → `committed` → `completed`

### Key Status Rules
- Developers can pick up tasks directly from `created` status (no approval needed)
- Senior developers can take junior-level tasks when no junior developers are available
- Only ONE task in `under_work` at a time
- Always include detailed notes when updating status
- Status automatically unlocks task when moving from `under_work`
- If QA fails, tasks return to `created` status for rework

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
- Register with name, URL, and health check
- Send heartbeats every 30 seconds
- Update status if service goes down

### Monitoring & Continuous Operation
- **CONTINUOUS POLLING**: Check for new tasks every 5 minutes when waiting
- Poll for changes regularly (every 10-30 seconds) during active work
- Check for mentions and respond immediately
- Respond to critical issues quickly
- **NEVER GO IDLE**: Always have either a real task or waiting task active
- Use the enhanced APIs that automatically provide next tasks

## Error Handling

Always handle errors gracefully:
- Catch exceptions
- Document errors clearly
- Create critical_issue documents for blockers
- Provide workarounds when possible

## Best Practices

1. **Over-communicate** - More updates are better than fewer
2. **Be specific** - Include IDs, error messages, screenshots
3. **Stay focused** - One task at a time
4. **Test thoroughly** - Before marking dev_done
5. **Document well** - Help future team members
6. **Collaborate** - Use @mentions, ask questions
7. **Track time** - Note how long tasks take

## Skill Levels

- **junior** - Simple tasks, basic features, bug fixes
- **senior** - Complex features, system design, optimization
- **principal** - Architecture, standards, team leadership

## Environment Variables

Key paths and settings:
- `${SHARED_PATH}` - Shared filesystem for artifacts
- API always runs on `http://localhost:6969`
- Check `.env` for API keys and configuration

## Remember

The goal is efficient, asynchronous collaboration. Your updates and documents are how the team stays synchronized. When in doubt, communicate more rather than less.
