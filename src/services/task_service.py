from sqlmodel import Session, select
from typing import Optional, List
from datetime import datetime, timedelta
import time

from src.models.models import Agent, Task
from src.models.enums import TaskStatus, AgentRole, DifficultyLevel
from src.api.schemas import TaskResponse
from src.models.database import engine


def cleanup_stale_locks(db: Session, stale_threshold_minutes: int = 30) -> int:
    """
    Find and unlock tasks that have been locked by inactive agents.
    Returns the number of tasks that were unlocked.
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=stale_threshold_minutes)
    
    # Find tasks locked by inactive agents
    stale_locked_tasks = db.exec(
        select(Task).join(Agent, Task.locked_by_id == Agent.id).where(
            Task.locked_by_id.isnot(None),
            Agent.last_seen < cutoff_time
        )
    ).all()
    
    # Unlock the stale tasks
    for task in stale_locked_tasks:
        task.locked_by_id = None
        task.locked_at = None
        db.add(task)
    
    db.commit()
    return len(stale_locked_tasks)


def get_next_task_for_agent(agent: Agent, db: Session) -> Optional[TaskResponse]:
    """Helper function to get the next available task for an agent"""
    
    # Clean up any stale locks first
    cleanup_stale_locks(db)
    
    # Determine which statuses to look for based on role
    if agent.role == AgentRole.QA:
        # QA tests ALL dev_done tasks regardless of target role
        query = select(Task).where(
            Task.status == TaskStatus.DEV_DONE,
            Task.locked_by_id.is_(None)
        )
    else:
        # Developers (including PM/Architect) work on created tasks
        # Check if there are available agents at lower skill levels for this role
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
            updated_at=task.updated_at
        )
    
    return None


def wait_for_next_task(role: AgentRole, level: DifficultyLevel, timeout_seconds: int = 180) -> Optional[TaskResponse]:
    """
    Wait for a task to become available for the given role and level.
    Uses fresh database sessions to avoid MySQL connection issues.
    
    Args:
        role: The agent's role
        level: The agent's difficulty level
        timeout_seconds: How long to wait before giving up (default 3 minutes)
        
    Returns:
        TaskResponse if a task becomes available, None otherwise
    """
    # Create a temporary agent object for the helper functions
    temp_agent = Agent(
        agent_id=f"temp_{role.value}_{level.value}",
        role=role,
        level=level,
        last_seen=datetime.utcnow()
    )
    
    # Check immediately with a fresh session
    with Session(engine) as db:
        next_task = get_next_task_for_agent(temp_agent, db)
        if next_task:
            return next_task
    
    # If no task available immediately, wait with polling
    start_time = time.time()
    
    while True:
        # Check if we've exceeded the timeout
        elapsed = time.time() - start_time
        if elapsed >= timeout_seconds:
            break
        
        # Wait before checking again, but not longer than remaining time
        wait_time = min(5, timeout_seconds - elapsed)
        if wait_time <= 0:
            break
        time.sleep(wait_time)
        
        # Get a fresh database session for each check
        with Session(engine) as fresh_db:
            # Try to get a real task again
            next_task = get_next_task_for_agent(temp_agent, fresh_db)
            
            if next_task:
                return next_task
    
    # No task found within timeout
    return None