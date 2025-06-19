# Sample Agent Workflow

## Frontend Developer Agent Session

This example shows how a Frontend Developer agent would interact with the Headless PM system.

### 1. Session Start (Paste to Claude)

```
You are a Senior Frontend Developer agent. Your first task is to register with the project management system and get your assignments.

API Endpoint: http://localhost:8000
API Key: dev-api-key-123

Start by:
1. Registering as frontend_dev role with senior level
2. Getting project context
3. Retrieving your next task
```

### 2. Agent Registers

```bash
# Agent calls registration
curl -X POST http://localhost:8000/api/register \
  -H "X-API-Key: dev-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{"role": "frontend_dev", "level": "senior"}'
```

**Response:**
```json
{
  "agent_id": "frontend_dev_senior_001",
  "role": "frontend_dev",
  "level": "senior",
  "instructions": "... full instructions ...",
  "project_docs": "/project/docs",
  "shared_path": "/shared"
}
```

### 3. Agent Gets Context

```bash
curl http://localhost:8000/api/context \
  -H "X-API-Key: dev-api-key-123"
```

**Response:**
```json
{
  "project_name": "E-Commerce Platform",
  "main_branch": "main",
  "documentation": {
    "project_docs": "/project/docs",
    "shared_path": "/shared"
  }
}
```

### 4. Agent Creates a Task for Backend

Before getting assigned tasks, the frontend dev realizes they need an API endpoint.

```bash
curl -X POST http://localhost:8000/api/tasks/create \
  -H "X-API-Key: dev-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Create login API endpoint",
    "description": "Need POST /api/auth/login endpoint that accepts email/password and returns JWT token",
    "target_role": "backend_dev",
    "difficulty": "senior",
    "feature_id": 5,
    "branch": "feature/user-auth"
  }'
```

**Response:**
```json
{
  "status": "created",
  "task": {
    "id": 41,
    "status": "created",
    "created_by": "frontend_dev"
  }
}
```

### 5. Agent Gets Their Task

```bash
curl http://localhost:8000/api/tasks/next \
  -H "X-API-Key: dev-api-key-123"
```

**Response:**
```json
{
  "id": 42,
  "feature_id": 5,
  "title": "Implement login form",
  "description": "Create a login form with email/password fields and validation",
  "created_by": "pm",
  "target_role": "frontend_dev",
  "difficulty": "senior",
  "branch": "feature/user-auth",
  "status": "created",
  "locked_by": null,
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 6. Agent Locks Task

```bash
curl -X POST http://localhost:8000/api/tasks/42/lock \
  -H "X-API-Key: dev-api-key-123"
```

**Response:**
```json
{
  "status": "locked",
  "task": {
    "id": 42,
    "status": "under_work",
    "locked_by": "frontend_dev_senior_001"
  }
}
```

### 7. Agent Works on Task

```bash
# Agent switches branch
git checkout feature/user-auth

# Agent implements the feature
# ... coding work ...

# Agent takes screenshot
# Saves to: /shared/screenshots/login-form-42.png
```

### 8. Agent Updates Status

```bash
curl -X PUT http://localhost:8000/api/tasks/42/status \
  -H "X-API-Key: dev-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "dev_done",
    "notes": "Login form implemented with validation. Screenshot saved at /shared/screenshots/login-form-42.png"
  }'
```

**Response:**
```json
{
  "status": "updated",
  "task": {
    "id": 42,
    "status": "dev_done",
    "locked_by": null
  }
}
```

### 9. Agent Gets Next Task

The cycle repeats - agent asks for next task and continues working.

## Simplified Task Workflow (No Approval Needed)

In the new simplified workflow, developers can pick up tasks directly from `created` status without needing PM approval. This eliminates bottlenecks and speeds up development.

### PM/Architect Role

PMs and Architects focus on:
- Creating well-defined tasks
- Providing guidance through comments
- Monitoring progress
- Removing blockers

They can still add comments to tasks for clarification:

```bash
curl -X POST http://localhost:8000/api/tasks/41/comment \
  -H "X-API-Key: pm-api-key-789" \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "Good task description. Please also include rate limiting and proper error responses."
  }'
```

## QA Agent Workflow

### 1. QA Picks Up Dev-Complete Task

```bash
# QA agent queries for tasks ready for testing
curl http://localhost:8000/api/tasks/next \
  -H "X-API-Key: qa-api-key-456"
```

**Note:** The API automatically returns tasks with `dev_done` status for QA role.

### 2. QA Tests and Updates

```bash
# Lock task
curl -X POST http://localhost:8000/api/tasks/42/lock \
  -H "X-API-Key: qa-api-key-456"

# After testing
curl -X PUT http://localhost:8000/api/tasks/42/status \
  -H "X-API-Key: qa-api-key-456" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "qa_done",
    "notes": "Tested login form - all validations working correctly"
  }'
```

## Complete Status Flow

```
created → under_work (dev) → dev_done → under_work (qa) → qa_done → documentation_done → committed
```

Task routing by role:
- **PM/Architect**: Create tasks and provide guidance
- **Developers**: Pick up `created` tasks matching their skill level (no approval needed)
- **QA**: Pick up `dev_done` tasks
- **Technical Writers**: Pick up `qa_done` tasks

### Failed QA Process
When QA fails, tasks return to `created` status and developers can pick them up directly for fixes.

## Difficulty Level Matching

- **Junior agents**: Can only work on `junior` level tasks
- **Senior agents**: Can work on `junior` and `senior` tasks (can take junior tasks when no junior developers available)
- **Principal agents**: Can work on all difficulty levels

Example: A junior backend developer registering will only receive junior-level backend tasks. Senior developers can step in to help with junior tasks when needed.

## CLI Usage for Monitoring

```bash
# Check overall status
python -m headless_pm status

# Output:
Project Status
========================================
planning                10
under_work               2
dev_done                 3
qa_done                  1
documentation_done       0
committed               15

# View all tasks
python -m headless_pm tasks

# Output:
+----+------------------+-------------+-----------+--------------------+-------------+
| ID | Title            | Role        | Status    | Branch             | Locked By   |
+====+==================+=============+===========+====================+=============+
| 42 | Implement login  | frontend_dev| qa_done   | feature/user-auth  | -           |
| 43 | Add validation   | frontend_dev| under_work| feature/user-auth  | frontend_001|
+----+------------------+-------------+-----------+--------------------+-------------+
```