from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
import os

from src.models.database import get_session
from src.api.dependencies import get_db
from src.models.models import Agent, Task, Epic, Feature, Changelog, Mention, Document
from src.models.enums import TaskStatus, AgentRole, DifficultyLevel, TaskType
from src.api.schemas import (
    AgentRegisterRequest, AgentResponse, AgentRegistrationResponse,
    EpicCreateRequest, FeatureCreateRequest,
    TaskCreateRequest, TaskResponse, TaskStatusUpdateRequest, TaskStatusUpdateResponse,
    TaskCommentRequest,
    ProjectContextResponse, EpicResponse, FeatureResponse,
    ChangelogResponse, MentionResponse
)
from src.api.dependencies import verify_api_key
from src.services.mention_service import create_mentions_for_task
import json
from pathlib import Path

router = APIRouter(prefix="/api/v1", dependencies=[Depends(verify_api_key)])

def get_next_task_for_agent(agent: Agent, db: Session) -> Optional[TaskResponse]:
    """Helper function to get the next available task for an agent"""
    # Determine which statuses to look for based on role
    if agent.role == AgentRole.QA:
        # QA tests dev_done tasks
        query = select(Task).where(
            Task.status == TaskStatus.DEV_DONE,
            Task.locked_by_id.is_(None)
        )
    else:
        # Developers (including PM/Architect) work on created tasks
        # Check if there are available agents at lower skill levels for this role
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)  # Consider agent active if seen in last 30 min
        
        # Get active agents for this role at different skill levels
        active_agents = db.exec(
            select(Agent).where(
                Agent.role == agent.role,
                Agent.last_seen > cutoff_time
            )
        ).all()
        
        # Determine available skill levels
        active_skill_levels = {ag.level for ag in active_agents}
        
        # Define skill hierarchy
        skill_hierarchy = [DifficultyLevel.JUNIOR, DifficultyLevel.SENIOR, DifficultyLevel.PRINCIPAL]
        current_skill_index = skill_hierarchy.index(agent.level)
        
        # Determine which difficulties this agent can work on
        allowed_difficulties = []
        for i, skill in enumerate(skill_hierarchy):
            if i <= current_skill_index:  # Can always do tasks at or below their level
                allowed_difficulties.append(skill)
            elif skill not in active_skill_levels:  # Can do higher-level tasks if no one else available
                continue
        
        # For architects and PMs, also include legacy APPROVED status for backward compatibility
        if agent.role in [AgentRole.ARCHITECT, AgentRole.PM]:
            query = select(Task).where(
                (Task.status == TaskStatus.CREATED) | (Task.status == TaskStatus.APPROVED),
                Task.target_role == agent.role,
                Task.difficulty.in_(allowed_difficulties),
                Task.locked_by_id.is_(None)
            )
        else:
            query = select(Task).where(
                (Task.status == TaskStatus.CREATED) | (Task.status == TaskStatus.APPROVED),
                Task.target_role == agent.role,
                Task.difficulty.in_(allowed_difficulties),
                Task.locked_by_id.is_(None)
            )
    
    # Get oldest unlocked task
    task = db.exec(query.order_by(Task.created_at)).first()
    
    if task:
        return TaskResponse(
            id=task.id,
            feature_id=task.feature_id,
            title=task.title,
            description=task.description,
            created_by=task.creator.agent_id,
            target_role=task.target_role,
            difficulty=task.difficulty,
            complexity=task.complexity,
            branch=task.branch,
            status=task.status,
            locked_by=None,
            locked_at=None,
            notes=task.notes,
            created_at=task.created_at,
            updated_at=task.updated_at,
            task_type=TaskType.REGULAR
        )
    
    return None

def create_waiting_task(agent: Agent, poll_interval: int = 300) -> TaskResponse:
    """Create a synthetic waiting task for continuous polling"""
    return TaskResponse(
        id=-1,  # Negative ID to indicate synthetic task
        feature_id=-1,
        title=f"Monitoring for new {agent.role.value} tasks",
        description=f"No active tasks available. Polling for new {agent.role.value} tasks every {poll_interval} seconds. This is a synthetic task to keep agents active.",
        created_by="system",
        target_role=agent.role,
        difficulty=agent.level,
        complexity="minor",
        branch="main",
        status=TaskStatus.UNDER_WORK,
        locked_by=agent.agent_id,
        locked_at=datetime.utcnow(),
        notes=f"Poll interval: {poll_interval} seconds",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        task_type=TaskType.WAITING,
        poll_interval=poll_interval
    )

@router.post("/register", response_model=AgentRegistrationResponse, 
    summary="Register an agent",
    description="Register a new agent or update existing agent's last seen timestamp. Returns agent info, next available task, and any unread mentions.")
def register_agent(request: AgentRegisterRequest, db: Session = Depends(get_session)):
    # Check if agent exists
    agent = db.exec(select(Agent).where(Agent.agent_id == request.agent_id)).first()
    
    if agent:
        # Update last seen and connection type
        agent.last_seen = datetime.utcnow()
        agent.connection_type = request.connection_type
    else:
        # Create new agent
        agent = Agent(
            agent_id=request.agent_id,
            role=request.role,
            level=request.level,
            connection_type=request.connection_type
        )
        db.add(agent)
    
    db.commit()
    db.refresh(agent)
    
    # Get next available task for this agent (or waiting task if none available)
    next_task = get_next_task_for_agent(agent, db)
    if not next_task:
        next_task = create_waiting_task(agent, poll_interval=300)
    
    # Get unread mentions for this agent
    mention_query = select(Mention).where(
        Mention.mentioned_agent_id == agent.agent_id,
        Mention.is_read == False
    ).order_by(Mention.created_at.desc()).limit(10)
    mentions_data = db.exec(mention_query).all()
    
    # Build mention responses with document/task titles
    mentions = []
    for mention in mentions_data:
        response = MentionResponse(
            id=mention.id,
            document_id=mention.document_id,
            task_id=mention.task_id,
            mentioned_agent_id=mention.mentioned_agent_id,
            created_by=mention.created_by,
            is_read=mention.is_read,
            created_at=mention.created_at
        )
        
        # Add document title if it's a document mention
        if mention.document_id:
            document = db.get(Document, mention.document_id)
            if document:
                response.document_title = document.title
        
        # Add task title if it's a task mention
        if mention.task_id:
            task_obj = db.get(Task, mention.task_id)
            if task_obj:
                response.task_title = task_obj.title
        
        mentions.append(response)
    
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
    agents = db.exec(select(Agent).order_by(Agent.last_seen.desc())).all()
    return agents

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

@router.post("/epics", response_model=EpicResponse,
    summary="Create a new epic",
    description="PMs and architects can create epics")
def create_epic(request: EpicCreateRequest, agent_id: str, db: Session = Depends(get_session)):
    # Verify agent is PM or architect
    agent = db.exec(select(Agent).where(Agent.agent_id == agent_id)).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found. Please ensure the agent is registered using POST /api/v1/register before attempting this operation.")
    
    if agent.role not in [AgentRole.PM, AgentRole.ARCHITECT]:
        raise HTTPException(status_code=403, detail="Only PMs and architects can create epics")
    
    # Create epic
    epic = Epic(
        name=request.name,
        description=request.description
    )
    db.add(epic)
    db.commit()
    db.refresh(epic)
    
    return EpicResponse(
        id=epic.id,
        name=epic.name,
        description=epic.description,
        created_at=epic.created_at,
        task_count=0,
        completed_count=0
    )

@router.post("/features", response_model=FeatureResponse,
    summary="Create a new feature",
    description="PMs and architects can create features within epics")
def create_feature(request: FeatureCreateRequest, agent_id: str, db: Session = Depends(get_session)):
    # Verify agent is PM or architect
    agent = db.exec(select(Agent).where(Agent.agent_id == agent_id)).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found. Please ensure the agent is registered using POST /api/v1/register before attempting this operation.")
    
    if agent.role not in [AgentRole.PM, AgentRole.ARCHITECT]:
        raise HTTPException(status_code=403, detail="Only PMs and architects can create features")
    
    # Verify epic exists
    epic = db.get(Epic, request.epic_id)
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
    
    # Create feature
    feature = Feature(
        epic_id=request.epic_id,
        name=request.name,
        description=request.description
    )
    db.add(feature)
    db.commit()
    db.refresh(feature)
    
    return feature

@router.get("/tasks", response_model=List[TaskResponse],
    summary="List all tasks",
    description="Get all tasks with optional filtering by status and role")
def list_tasks(
    status: Optional[TaskStatus] = None,
    role: Optional[AgentRole] = None,
    db: Session = Depends(get_session)
):
    """List all tasks with optional filtering"""
    query = select(Task).order_by(Task.created_at.desc())
    
    if status:
        query = query.where(Task.status == status)
    
    if role:
        query = query.where(Task.target_role == role)
    
    tasks = db.exec(query).all()
    
    # Convert to TaskResponse objects
    return [
        TaskResponse(
            id=task.id,
            feature_id=task.feature_id,
            title=task.title,
            description=task.description,
            created_by=task.creator.agent_id if task.creator else "unknown",
            target_role=task.target_role,
            difficulty=task.difficulty,
            complexity=task.complexity,
            branch=task.branch,
            status=task.status,
            locked_by=task.locked_by_agent.agent_id if task.locked_by_agent else None,
            locked_at=task.locked_at,
            notes=task.notes,
            created_at=task.created_at,
            updated_at=task.updated_at
        )
        for task in tasks
    ]

@router.post("/tasks/create", response_model=TaskResponse,
    summary="Create a new task",
    description="Any agent can create a task for any role")
def create_task(request: TaskCreateRequest, agent_id: str, db: Session = Depends(get_session)):
    # Find creator agent
    creator = db.exec(select(Agent).where(Agent.agent_id == agent_id)).first()
    if not creator:
        raise HTTPException(status_code=404, detail="Creator agent not found")
    
    # Verify feature exists
    feature = db.get(Feature, request.feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    # Create task
    task = Task(
        feature_id=request.feature_id,
        title=request.title,
        description=request.description,
        created_by_id=creator.id,
        target_role=request.target_role,
        difficulty=request.difficulty,
        complexity=request.complexity,
        branch=request.branch
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Create initial changelog
    changelog = Changelog(
        task_id=task.id,
        old_status=TaskStatus.CREATED,
        new_status=TaskStatus.CREATED,
        changed_by=creator.agent_id,
        notes="Task created"
    )
    db.add(changelog)
    db.commit()
    
    return TaskResponse(
        id=task.id,
        feature_id=task.feature_id,
        title=task.title,
        description=task.description,
        created_by=task.creator.agent_id,
        target_role=task.target_role,
        difficulty=task.difficulty,
        complexity=task.complexity,
        branch=task.branch,
        status=task.status,
        locked_by=task.locked_by_agent.agent_id if task.locked_by_agent else None,
        locked_at=task.locked_at,
        notes=task.notes,
        created_at=task.created_at,
        updated_at=task.updated_at
    )

@router.get("/tasks/next", response_model=TaskResponse,
    summary="Get next available task",
    description="Get the next task based on agent's role and skill level, or a waiting task if none available. Both 'role' and 'level' query parameters are required.")
def get_next_task(role: AgentRole = None, level: DifficultyLevel = None, 
                  db: Session = Depends(get_session)):
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
    
    # Create a temporary agent object for the helper functions
    temp_agent = Agent(
        agent_id=f"temp_{role.value}_{level.value}",
        role=role,
        level=level,
        last_seen=datetime.utcnow()
    )
    
    # Try to get a real task
    next_task = get_next_task_for_agent(temp_agent, db)
    
    if next_task:
        return next_task
    else:
        # Return a waiting task to keep agents active
        return create_waiting_task(temp_agent, poll_interval=300)

@router.post("/tasks/{task_id}/lock", response_model=TaskResponse,
    summary="Lock a task",
    description="Lock a task to prevent other agents from working on it")
def lock_task(task_id: int, agent_id: str, db: Session = Depends(get_session)):
    # Get task
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found. Please verify the task ID exists.")
    
    # Check if already locked
    if task.locked_by_id:
        raise HTTPException(status_code=409, detail=f"Task {task_id} is already locked by another agent. The task must be unlocked before you can lock it.")
    
    # Get agent
    agent = db.exec(select(Agent).where(Agent.agent_id == agent_id)).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found. Please ensure the agent is registered using POST /api/v1/register before attempting this operation.")
    
    # Lock the task
    task.locked_by_id = agent.id
    task.locked_at = datetime.utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        feature_id=task.feature_id,
        title=task.title,
        description=task.description,
        created_by=task.creator.agent_id,
        target_role=task.target_role,
        difficulty=task.difficulty,
        complexity=task.complexity,
        branch=task.branch,
        status=task.status,
        locked_by=agent.agent_id,
        locked_at=task.locked_at,
        notes=task.notes,
        created_at=task.created_at,
        updated_at=task.updated_at
    )

@router.put("/tasks/{task_id}/status", response_model=TaskStatusUpdateResponse,
    summary="Update task status",
    description="Update task status, automatically release lock when moving from UNDER_WORK, and return next available task")
def update_task_status(task_id: int, request: TaskStatusUpdateRequest, 
                      agent_id: str, db: Session = Depends(get_session)):
    # Get task
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found. Please verify the task ID exists.")
    
    # Get agent
    agent = db.exec(select(Agent).where(Agent.agent_id == agent_id)).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found. Please ensure the agent is registered using POST /api/v1/register before attempting this operation.")
    
    # Store old status
    old_status = task.status
    
    # Update status
    task.status = request.status
    task.updated_at = datetime.utcnow()
    
    # Add notes if provided
    if request.notes:
        task.notes = request.notes
    
    # Release lock if moving from UNDER_WORK
    if old_status == TaskStatus.UNDER_WORK and request.status != TaskStatus.UNDER_WORK:
        task.locked_by_id = None
        task.locked_at = None
    
    db.add(task)
    
    # Create changelog
    changelog = Changelog(
        task_id=task.id,
        old_status=old_status,
        new_status=request.status,
        changed_by=agent_id,
        notes=request.notes
    )
    db.add(changelog)
    
    db.commit()
    db.refresh(task)
    
    # Create the current task response
    task_response = TaskResponse(
        id=task.id,
        feature_id=task.feature_id,
        title=task.title,
        description=task.description,
        created_by=task.creator.agent_id,
        target_role=task.target_role,
        difficulty=task.difficulty,
        complexity=task.complexity,
        branch=task.branch,
        status=task.status,
        locked_by=task.locked_by_agent.agent_id if task.locked_by_agent else None,
        locked_at=task.locked_at,
        notes=task.notes,
        created_at=task.created_at,
        updated_at=task.updated_at,
        task_type=TaskType.REGULAR
    )
    
    # Get next available task for this agent
    next_task = get_next_task_for_agent(agent, db)
    
    # Determine workflow status
    if next_task:
        workflow_status = "continue"
    else:
        # Create a waiting task
        next_task = create_waiting_task(agent, poll_interval=300)
        workflow_status = "waiting"
    
    return TaskStatusUpdateResponse(
        task=task_response,
        next_task=next_task,
        workflow_status=workflow_status
    )


@router.post("/tasks/{task_id}/comment",
    summary="Add comment to task",
    description="Add a comment during evaluation phase with @mention detection")
def add_comment(task_id: int, request: TaskCommentRequest,
               agent_id: str, db: Session = Depends(get_db)):
    # Get task
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found. Please verify the task ID exists.")
    
    # Add comment to notes
    if task.notes:
        task.notes = f"{task.notes}\n\n{agent_id}: {request.comment}"
    else:
        task.notes = f"{agent_id}: {request.comment}"
    
    # Extract and create mentions from the comment
    create_mentions_for_task(db, task_id, request.comment, agent_id)
    
    task.updated_at = datetime.utcnow()
    db.add(task)
    db.commit()
    
    return {"message": "Comment added successfully"}

@router.get("/epics", response_model=List[EpicResponse],
    summary="List all epics",
    description="Get all epics with task progress information")
def list_epics(db: Session = Depends(get_session)):
    epics = db.exec(select(Epic)).all()
    
    epic_responses = []
    for epic in epics:
        # Count tasks for this epic
        task_count = 0
        completed_task_count = 0
        in_progress_task_count = 0
        
        for feature in epic.features:
            tasks = db.exec(select(Task).where(Task.feature_id == feature.id)).all()
            task_count += len(tasks)
            completed_task_count += len([t for t in tasks if t.status == TaskStatus.COMMITTED])
            in_progress_task_count += len([t for t in tasks if t.status in [TaskStatus.UNDER_WORK, TaskStatus.DEV_DONE, TaskStatus.QA_DONE, TaskStatus.DOCUMENTATION_DONE]])
        
        epic_response = EpicResponse(
            id=epic.id,
            name=epic.name,
            description=epic.description,
            created_at=epic.created_at,
            task_count=task_count,
            completed_task_count=completed_task_count,
            in_progress_task_count=in_progress_task_count
        )
        epic_responses.append(epic_response)
    
    return epic_responses

@router.get("/features/{epic_id}", response_model=List[FeatureResponse],
    summary="List features for an epic",
    description="Get all features belonging to a specific epic")
def list_features(epic_id: int, db: Session = Depends(get_session)):
    features = db.exec(select(Feature).where(Feature.epic_id == epic_id)).all()
    return features

@router.get("/changelog", response_model=List[ChangelogResponse],
    summary="Get recent changes",
    description="Get recent task status changes across the project")
def get_changelog(limit: int = 50, db: Session = Depends(get_session)):
    changelogs = db.exec(
        select(Changelog)
        .order_by(Changelog.changed_at.desc())
        .limit(limit)
    ).all()
    return changelogs


# Delete endpoints (PM only)
@router.delete("/epics/{epic_id}",
    summary="Delete an epic (PM only)",
    description="Delete an epic and all its features and tasks. Only PM agents can perform this action.")
def delete_epic(epic_id: int, agent_id: str, db: Session = Depends(get_session)):
    # Verify agent is PM
    agent = db.exec(select(Agent).where(Agent.agent_id == agent_id)).first()
    if not agent or agent.role != AgentRole.PM:
        raise HTTPException(status_code=403, detail="Only PM agents can delete epics")
    
    epic = db.exec(select(Epic).where(Epic.id == epic_id)).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
    
    db.delete(epic)
    db.commit()
    return {"message": f"Epic {epic_id} deleted successfully"}


@router.delete("/features/{feature_id}",
    summary="Delete a feature (PM only)",
    description="Delete a feature and all its tasks. Only PM agents can perform this action.")
def delete_feature(feature_id: int, agent_id: str, db: Session = Depends(get_session)):
    # Verify agent is PM
    agent = db.exec(select(Agent).where(Agent.agent_id == agent_id)).first()
    if not agent or agent.role != AgentRole.PM:
        raise HTTPException(status_code=403, detail="Only PM agents can delete features")
    
    feature = db.exec(select(Feature).where(Feature.id == feature_id)).first()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    db.delete(feature)
    db.commit()
    return {"message": f"Feature {feature_id} deleted successfully"}


@router.delete("/tasks/{task_id}",
    summary="Delete a task (PM only)",
    description="Delete a task. Only PM agents can perform this action.")
def delete_task(task_id: int, agent_id: str, db: Session = Depends(get_session)):
    # Verify agent is PM
    agent = db.exec(select(Agent).where(Agent.agent_id == agent_id)).first()
    if not agent or agent.role != AgentRole.PM:
        raise HTTPException(status_code=403, detail="Only PM agents can delete tasks")
    
    task = db.exec(select(Task).where(Task.id == task_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return {"message": f"Task {task_id} deleted successfully"}


@router.delete("/agents/{agent_id}",
    summary="Delete an agent (PM only)",
    description="Delete an agent record. Only PM agents can perform this action.")
def delete_agent(agent_id: str, requester_agent_id: str, db: Session = Depends(get_session)):
    # Verify requester is PM
    requester = db.exec(select(Agent).where(Agent.agent_id == requester_agent_id)).first()
    if not requester or requester.role != AgentRole.PM:
        raise HTTPException(status_code=403, detail="Only PM agents can delete other agents")
    
    # Prevent PM from deleting themselves
    if agent_id == requester_agent_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own agent record")
    
    agent = db.exec(select(Agent).where(Agent.agent_id == agent_id)).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    return {"message": f"Agent {agent_id} deleted successfully"}

