from sqlmodel import Session, select
from typing import List

from src.models.models import Epic, Feature, Task
from src.models.enums import TaskStatus, AgentRole
from src.api.schemas import EpicCreateRequest, EpicResponse, FeatureCreateRequest, FeatureResponse
from src.api.dependencies import HTTPException
from src.services.agent_service import verify_agent_role


def create_epic(request: EpicCreateRequest, agent_id: str, db: Session) -> EpicResponse:
    """
    Create a new epic. Only PMs and architects can create epics.
    
    Args:
        request: Epic creation request data
        agent_id: ID of the agent creating the epic
        db: Database session
        
    Returns:
        The created epic response
        
    Raises:
        HTTPException: If agent doesn't have required role
    """
    # Verify agent is PM or architect
    verify_agent_role(agent_id, [AgentRole.PM, AgentRole.ARCHITECT], db)
    
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
        completed_task_count=0,
        in_progress_task_count=0
    )


def list_epics(db: Session) -> List[EpicResponse]:
    """
    Get all epics with task progress information.
    
    Args:
        db: Database session
        
    Returns:
        List of epic responses with progress stats
    """
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
            in_progress_task_count += len([t for t in tasks if t.status in [
                TaskStatus.UNDER_WORK, TaskStatus.DEV_DONE, TaskStatus.QA_DONE, TaskStatus.DOCUMENTATION_DONE
            ]])
        
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


def create_feature(request: FeatureCreateRequest, agent_id: str, db: Session) -> FeatureResponse:
    """
    Create a new feature within an epic. Only PMs and architects can create features.
    
    Args:
        request: Feature creation request data
        agent_id: ID of the agent creating the feature
        db: Database session
        
    Returns:
        The created feature
        
    Raises:
        HTTPException: If agent doesn't have required role or epic not found
    """
    # Verify agent is PM or architect
    verify_agent_role(agent_id, [AgentRole.PM, AgentRole.ARCHITECT], db)
    
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


def list_features_for_epic(epic_id: int, db: Session) -> List[Feature]:
    """
    Get all features belonging to a specific epic.
    
    Args:
        epic_id: ID of the epic
        db: Database session
        
    Returns:
        List of features for the epic
    """
    return db.exec(select(Feature).where(Feature.epic_id == epic_id)).all()


def delete_epic(epic_id: int, agent_id: str, db: Session) -> dict:
    """
    Delete an epic and all its features and tasks. Only PM agents can perform this action.
    
    Args:
        epic_id: ID of the epic to delete
        agent_id: ID of the agent making the request
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If unauthorized or epic not found
    """
    # Verify agent is PM
    verify_agent_role(agent_id, [AgentRole.PM], db)
    
    epic = db.exec(select(Epic).where(Epic.id == epic_id)).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
    
    db.delete(epic)
    db.commit()
    
    return {"message": f"Epic {epic_id} deleted successfully"}


def delete_feature(feature_id: int, agent_id: str, db: Session) -> dict:
    """
    Delete a feature and all its tasks. Only PM agents can perform this action.
    
    Args:
        feature_id: ID of the feature to delete
        agent_id: ID of the agent making the request
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If unauthorized or feature not found
    """
    # Verify agent is PM
    verify_agent_role(agent_id, [AgentRole.PM], db)
    
    feature = db.exec(select(Feature).where(Feature.id == feature_id)).first()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    db.delete(feature)
    db.commit()
    
    return {"message": f"Feature {feature_id} deleted successfully"}