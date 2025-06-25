from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Optional
import os

from src.models.database import get_session
from src.models.enums import TaskStatus, AgentRole, DifficultyLevel
from src.api.schemas import (
    AgentRegisterRequest, AgentResponse, AgentRegistrationResponse,
    EpicCreateRequest, FeatureCreateRequest,
    TaskCreateRequest, TaskResponse, TaskStatusUpdateRequest, TaskStatusUpdateResponse,
    TaskCommentRequest,
    ProjectContextResponse, EpicResponse, FeatureResponse,
    ChangelogResponse, MentionResponse
)
from src.api.dependencies import verify_api_key

# Import service functions
from src.services.agent_service import (
    register_or_update_agent, get_unread_mentions, list_all_agents, delete_agent
)
from src.services.task_service import (
    get_next_task_for_agent, wait_for_next_task
)
from src.services.task_management_service import (
    create_task, list_tasks, lock_task, update_task_status, 
    add_task_comment, delete_task, get_recent_changelog
)
from src.services.epic_feature_service import (
    create_epic, list_epics, create_feature, list_features_for_epic,
    delete_epic, delete_feature
)

router = APIRouter(prefix="/api/v1", dependencies=[Depends(verify_api_key)])


# Agent endpoints
@router.post("/register", response_model=AgentRegistrationResponse, 
    summary="Register an agent",
    description="Register a new agent or update existing agent's last seen timestamp. Returns agent info, next available task, and any unread mentions.")
def register_agent(request: AgentRegisterRequest, db: Session = Depends(get_session)):
    # Register or update agent
    agent = register_or_update_agent(request, db)
    
    # Get next available task for this agent
    next_task = get_next_task_for_agent(agent, db)
    
    # Get unread mentions
    mentions = get_unread_mentions(agent.agent_id, db)
    
    return AgentRegistrationResponse(
        agent=AgentResponse(
            id=agent.id,
            agent_id=agent.agent_id,
            role=agent.role,
            level=agent.level,
            connection_type=agent.connection_type,
            last_seen=agent.last_seen
        ),
        next_task=next_task,
        mentions=mentions
    )


@router.get("/agents", response_model=List[AgentResponse],
    summary="List all agents", 
    description="Get a list of all registered agents")
def list_agents(db: Session = Depends(get_session)):
    return list_all_agents(db)


@router.delete("/agents/{agent_id}",
    summary="Delete an agent (PM only)",
    description="Delete an agent record. Only PM agents can perform this action.")
def delete_agent_endpoint(agent_id: str, requester_agent_id: str, db: Session = Depends(get_session)):
    return delete_agent(agent_id, requester_agent_id, db)


# Project context endpoint
@router.get("/context", response_model=ProjectContextResponse,
    summary="Get project context",
    description="Get project configuration and paths for documentation")
def get_context():
    return ProjectContextResponse(
        project_name=os.getenv("PROJECT_NAME", "Headless PM"),
        shared_path=os.getenv("SHARED_PATH", "./shared"),
        instructions_path=os.getenv("INSTRUCTIONS_PATH", "./agent_instructions"),
        project_docs_path=os.getenv("PROJECT_DOCS_PATH", "./docs"),
        database_type="sqlite" if os.getenv("DATABASE_URL", "").startswith("sqlite") else "mysql"
    )


# Epic endpoints
@router.post("/epics", response_model=EpicResponse,
    summary="Create a new epic",
    description="PMs and architects can create epics")
def create_epic_endpoint(request: EpicCreateRequest, agent_id: str, db: Session = Depends(get_session)):
    return create_epic(request, agent_id, db)


@router.get("/epics", response_model=List[EpicResponse],
    summary="List all epics",
    description="Get all epics with task progress information")
def list_epics_endpoint(db: Session = Depends(get_session)):
    return list_epics(db)


@router.delete("/epics/{epic_id}",
    summary="Delete an epic (PM only)",
    description="Delete an epic and all its features and tasks. Only PM agents can perform this action.")
def delete_epic_endpoint(epic_id: int, agent_id: str, db: Session = Depends(get_session)):
    return delete_epic(epic_id, agent_id, db)


# Feature endpoints
@router.post("/features", response_model=FeatureResponse,
    summary="Create a new feature",
    description="PMs and architects can create features within epics")
def create_feature_endpoint(request: FeatureCreateRequest, agent_id: str, db: Session = Depends(get_session)):
    return create_feature(request, agent_id, db)


@router.get("/features/{epic_id}", response_model=List[FeatureResponse],
    summary="List features for an epic",
    description="Get all features belonging to a specific epic")
def list_features_endpoint(epic_id: int, db: Session = Depends(get_session)):
    return list_features_for_epic(epic_id, db)


@router.delete("/features/{feature_id}",
    summary="Delete a feature (PM only)",
    description="Delete a feature and all its tasks. Only PM agents can perform this action.")
def delete_feature_endpoint(feature_id: int, agent_id: str, db: Session = Depends(get_session)):
    return delete_feature(feature_id, agent_id, db)


# Task endpoints
@router.post("/tasks/create", response_model=TaskResponse,
    summary="Create a new task",
    description="Any agent can create a task for any role")
def create_task_endpoint(request: TaskCreateRequest, agent_id: str, db: Session = Depends(get_session)):
    return create_task(request, agent_id, db)


@router.get("/tasks", response_model=List[TaskResponse],
    summary="List all tasks",
    description="Get all tasks with optional filtering by status and role")
def list_tasks_endpoint(
    status: Optional[TaskStatus] = None,
    role: Optional[AgentRole] = None,
    db: Session = Depends(get_session)
):
    return list_tasks(status, role, db)


@router.get("/tasks/next", response_model=Optional[TaskResponse],
    summary="Get next available task",
    description="Get the next task based on agent's role and skill level. Waits up to 3 minutes if no tasks are available, returns null if none found. Both 'role' and 'level' query parameters are required. Use 'simulate=true' to skip waiting for testing. Use 'timeout' to override wait duration (in seconds).")
def get_next_task(role: AgentRole = None, level: DifficultyLevel = None, 
                  simulate: bool = False, timeout: Optional[int] = None,
                  db: Session = Depends(get_session)) -> Optional[TaskResponse]:
    # Validate required parameters
    if role is None:
        raise HTTPException(
            status_code=400, 
            detail="Missing required parameter 'role'. Please provide a valid role (e.g., ?role=frontend_dev)"
        )
    if level is None:
        raise HTTPException(
            status_code=400, 
            detail="Missing required parameter 'level'. Please provide a valid level (e.g., ?level=senior)"
        )
    
    # Close the current session as we'll use fresh sessions in the service
    db.close()
    
    if simulate:
        # For testing/simulation, just check once without waiting
        from src.services.task_service import get_next_task_for_agent
        from src.models.models import Agent
        from src.models.database import engine
        from sqlmodel import Session
        from datetime import datetime
        
        temp_agent = Agent(
            agent_id=f"temp_{role.value}_{level.value}",
            role=role,
            level=level,
            last_seen=datetime.utcnow()
        )
        
        with Session(engine) as fresh_db:
            return get_next_task_for_agent(temp_agent, fresh_db)
    else:
        # Use the service function that handles waiting with fresh DB sessions
        # Use provided timeout or default to 180 seconds (3 minutes)
        wait_timeout = timeout if timeout is not None else 180
        return wait_for_next_task(role, level, timeout_seconds=wait_timeout)


@router.post("/tasks/{task_id}/lock", response_model=TaskResponse,
    summary="Lock a task",
    description="Lock a task to prevent other agents from working on it")
def lock_task_endpoint(task_id: int, agent_id: str, db: Session = Depends(get_session)):
    return lock_task(task_id, agent_id, db)


@router.put("/tasks/{task_id}/status", response_model=TaskStatusUpdateResponse,
    summary="Update task status",
    description="Update task status, automatically release lock when moving from UNDER_WORK, and return next available task")
def update_task_status_endpoint(task_id: int, request: TaskStatusUpdateRequest, 
                               agent_id: str, db: Session = Depends(get_session)):
    return update_task_status(task_id, request, agent_id, db)


@router.post("/tasks/{task_id}/comment",
    summary="Add comment to task",
    description="Add a comment during evaluation phase with @mention detection")
def add_comment_endpoint(task_id: int, request: TaskCommentRequest,
                        agent_id: str, db: Session = Depends(get_session)):
    return add_task_comment(task_id, request, agent_id, db)


@router.delete("/tasks/{task_id}",
    summary="Delete a task (PM only)",
    description="Delete a task. Only PM agents can perform this action.")
def delete_task_endpoint(task_id: int, agent_id: str, db: Session = Depends(get_session)):
    return delete_task(task_id, agent_id, db)


# Changelog endpoint
@router.get("/changelog", response_model=List[ChangelogResponse],
    summary="Get recent changes",
    description="Get recent task status changes across the project")
def get_changelog(limit: int = 50, db: Session = Depends(get_session)):
    return get_recent_changelog(limit, db)