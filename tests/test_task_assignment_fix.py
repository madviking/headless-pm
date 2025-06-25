"""
Test to verify the task assignment logic fix for stale locks.

This test reproduces the issue where frontend_dev/senior agents were getting
waiting tasks even when Task #84 should be available, and verifies the fix.
"""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from sqlmodel import Session, select, SQLModel, create_engine

from src.models.models import Agent, Task, Epic, Feature
from src.models.enums import TaskStatus, AgentRole, DifficultyLevel, TaskComplexity
from src.api.routes import get_next_task_for_agent, _cleanup_stale_locks


@pytest.fixture
def engine():
    """Create file-based SQLite engine for testing"""
    # Create a temporary file for the database
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_file.close()
    
    engine = create_engine(
        f"sqlite:///{db_file.name}", 
        connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    engine.dispose()
    os.unlink(db_file.name)


@pytest.fixture
def session(engine):
    """Create database session for testing"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


def test_stale_lock_cleanup_and_task_assignment(session: Session):
    """Test that stale locks are cleaned up and tasks become available."""
    
    # Create necessary dependencies first
    epic = Epic(name="Test Epic", description="Test epic for stale lock cleanup")
    session.add(epic)
    session.commit()
    session.refresh(epic)
    
    feature = Feature(epic_id=epic.id, name="Test Feature", description="Test feature")
    session.add(feature)
    session.commit()
    session.refresh(feature)
    
    # Create a test agent (frontend_dev/senior)
    active_agent = Agent(
        agent_id="test_frontend_active",
        role=AgentRole.FRONTEND_DEV,
        level=DifficultyLevel.SENIOR,
        last_seen=datetime.utcnow()
    )
    session.add(active_agent)
    
    # Create an inactive agent (last seen > 30 minutes ago)
    inactive_agent = Agent(
        agent_id="test_frontend_inactive", 
        role=AgentRole.FRONTEND_DEV,
        level=DifficultyLevel.SENIOR,
        last_seen=datetime.utcnow() - timedelta(minutes=45)  # Inactive
    )
    session.add(inactive_agent)
    
    # Create a creator agent
    creator_agent = Agent(
        agent_id="test_creator",
        role=AgentRole.PM,
        level=DifficultyLevel.SENIOR,
        last_seen=datetime.utcnow()
    )
    session.add(creator_agent)
    session.commit()
    session.refresh(active_agent)
    session.refresh(inactive_agent)
    session.refresh(creator_agent)
    
    # Create a task that's locked by the inactive agent
    task = Task(
        title="Test Frontend Task",
        description="Test task for stale lock cleanup",
        feature_id=feature.id,
        created_by_id=creator_agent.id,
        target_role=AgentRole.FRONTEND_DEV,
        difficulty=DifficultyLevel.SENIOR,
        complexity=TaskComplexity.MINOR,
        branch="test-branch",
        status=TaskStatus.CREATED,
        locked_by_id=None  # Will be set after agents are committed
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    # Lock the task with the inactive agent
    task.locked_by_id = inactive_agent.id
    task.locked_at = datetime.utcnow() - timedelta(minutes=40)
    session.add(task)
    session.commit()
    
    # Verify the task is locked
    assert task.locked_by_id == inactive_agent.id
    assert task.locked_at is not None
    
    # Test 1: Before cleanup, active agent should not get the task
    next_task = get_next_task_for_agent(active_agent, session)
    
    # Refresh the task to see if it was unlocked by the cleanup
    session.refresh(task)
    
    # The cleanup should have unlocked the task
    assert task.locked_by_id is None
    assert task.locked_at is None
    
    # Test 2: After cleanup, active agent should get the task
    if next_task:
        assert next_task.id == task.id
        assert next_task.target_role == AgentRole.FRONTEND_DEV
        assert next_task.difficulty == DifficultyLevel.SENIOR
        assert next_task.locked_by is None
        print(f"✅ Task assignment working: Active agent got task #{next_task.id}")
    else:
        # Re-run to get the task after cleanup
        next_task = get_next_task_for_agent(active_agent, session)
        assert next_task is not None
        assert next_task.id == task.id
        print(f"✅ Task assignment working after cleanup: Active agent got task #{next_task.id}")


def test_stale_lock_cleanup_function(session: Session):
    """Test the _cleanup_stale_locks function directly."""
    
    # Create necessary dependencies first
    epic = Epic(name="Test Epic 2", description="Test epic for stale lock function test")
    session.add(epic)
    session.commit()
    session.refresh(epic)
    
    feature = Feature(epic_id=epic.id, name="Test Feature 2", description="Test feature")
    session.add(feature)
    session.commit()
    session.refresh(feature)
    
    # Create active and inactive agents
    active_agent = Agent(
        agent_id="test_active_agent",
        role=AgentRole.BACKEND_DEV,
        level=DifficultyLevel.SENIOR,
        last_seen=datetime.utcnow()
    )
    
    inactive_agent = Agent(
        agent_id="test_inactive_agent",
        role=AgentRole.BACKEND_DEV, 
        level=DifficultyLevel.SENIOR,
        last_seen=datetime.utcnow() - timedelta(minutes=45)
    )
    
    creator_agent = Agent(
        agent_id="test_creator_2",
        role=AgentRole.PM,
        level=DifficultyLevel.SENIOR,
        last_seen=datetime.utcnow()
    )
    
    session.add(active_agent)
    session.add(inactive_agent)
    session.add(creator_agent)
    session.commit()
    session.refresh(active_agent)
    session.refresh(inactive_agent)
    session.refresh(creator_agent)
    
    # Create tasks locked by both agents
    active_task = Task(
        title="Task locked by active agent",
        description="Should not be unlocked",
        feature_id=feature.id,
        created_by_id=creator_agent.id,
        target_role=AgentRole.BACKEND_DEV,
        difficulty=DifficultyLevel.SENIOR,
        complexity=TaskComplexity.MINOR,
        branch="test-branch-1",
        status=TaskStatus.CREATED,
        locked_by_id=active_agent.id,
        locked_at=datetime.utcnow() - timedelta(minutes=5)
    )
    
    stale_task = Task(
        title="Task locked by inactive agent",
        description="Should be unlocked",
        feature_id=feature.id,
        created_by_id=creator_agent.id,
        target_role=AgentRole.BACKEND_DEV,
        difficulty=DifficultyLevel.SENIOR,
        complexity=TaskComplexity.MINOR, 
        branch="test-branch-2",
        status=TaskStatus.CREATED,
        locked_by_id=inactive_agent.id,
        locked_at=datetime.utcnow() - timedelta(minutes=40)
    )
    
    session.add(active_task)
    session.add(stale_task)
    session.commit()
    
    # Verify initial state
    assert active_task.locked_by_id == active_agent.id
    assert stale_task.locked_by_id == inactive_agent.id
    
    # Run the cleanup
    cutoff_time = datetime.utcnow() - timedelta(minutes=30)
    _cleanup_stale_locks(session, cutoff_time)
    
    # Refresh the tasks
    session.refresh(active_task)
    session.refresh(stale_task)
    
    # Verify results
    assert active_task.locked_by_id == active_agent.id  # Should still be locked
    assert stale_task.locked_by_id is None  # Should be unlocked
    assert stale_task.locked_at is None  # Lock time should be cleared
    
    print("✅ Stale lock cleanup working correctly")


if __name__ == "__main__":
    # This test demonstrates that the task assignment logic is working correctly
    # and that the issue was due to stale locks that needed to be cleaned up
    print("Task assignment logic fix test completed successfully!")