"""
Unit tests for database models
"""
import pytest
from datetime import datetime
from sqlmodel import Session, SQLModel, create_engine
from src.models.models import Agent, Epic, Feature, Task, Document, Service, Mention, TaskEvaluation, Changelog
from src.models.enums import TaskStatus, AgentRole, DifficultyLevel, TaskComplexity, ConnectionType, TaskType
from src.models.document_enums import DocumentType, ServiceStatus


@pytest.fixture
def engine():
    """Create in-memory SQLite engine for testing"""
    engine = create_engine(
        "sqlite:///:memory:", 
        connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create database session for testing"""
    with Session(engine) as session:
        yield session


class TestEnums:
    """Test enum classes"""
    
    def test_task_status_enum(self):
        """Test TaskStatus enum values"""
        assert TaskStatus.CREATED == "created"
        assert TaskStatus.UNDER_WORK == "under_work"
        assert TaskStatus.DEV_DONE == "dev_done"
        assert TaskStatus.QA_DONE == "qa_done"
        assert TaskStatus.DOCUMENTATION_DONE == "documentation_done"
        assert TaskStatus.COMMITTED == "committed"
        
    def test_agent_role_enum(self):
        """Test AgentRole enum values"""
        assert AgentRole.FRONTEND_DEV == "frontend_dev"
        assert AgentRole.BACKEND_DEV == "backend_dev"
        assert AgentRole.QA == "qa"
        assert AgentRole.ARCHITECT == "architect"
        assert AgentRole.PM == "pm"
        
    def test_difficulty_level_enum(self):
        """Test DifficultyLevel enum values"""
        assert DifficultyLevel.JUNIOR == "junior"
        assert DifficultyLevel.SENIOR == "senior"
        assert DifficultyLevel.PRINCIPAL == "principal"
        
    def test_task_complexity_enum(self):
        """Test TaskComplexity enum values"""
        assert TaskComplexity.MINOR == "minor"
        assert TaskComplexity.MAJOR == "major"
        
    def test_connection_type_enum(self):
        """Test ConnectionType enum values"""
        assert ConnectionType.MCP == "mcp"
        assert ConnectionType.CLIENT == "client"
        
    def test_task_type_enum(self):
        """Test TaskType enum values"""
        assert TaskType.REGULAR == "regular"
        assert TaskType.WAITING == "waiting"


class TestModels:
    """Test database models"""
    
    def test_agent_model_creation(self, session):
        """Test Agent model creation and fields"""
        agent = Agent(
            agent_id="test_agent_001",
            role=AgentRole.BACKEND_DEV,
            level=DifficultyLevel.SENIOR,
            connection_type=ConnectionType.CLIENT
        )
        session.add(agent)
        session.commit()
        session.refresh(agent)
        
        assert agent.id is not None
        assert agent.agent_id == "test_agent_001"
        assert agent.role == AgentRole.BACKEND_DEV
        assert agent.level == DifficultyLevel.SENIOR
        assert agent.connection_type == ConnectionType.CLIENT
        assert isinstance(agent.last_seen, datetime)
        
    def test_agent_default_connection_type(self, session):
        """Test Agent model default connection type"""
        agent = Agent(
            agent_id="test_agent_002",
            role=AgentRole.FRONTEND_DEV,
            level=DifficultyLevel.JUNIOR
        )
        session.add(agent)
        session.commit()
        session.refresh(agent)
        
        assert agent.connection_type == ConnectionType.CLIENT
        
    def test_epic_model_creation(self, session):
        """Test Epic model creation and fields"""
        epic = Epic(
            name="Test Epic",
            description="This is a test epic for the unit tests"
        )
        session.add(epic)
        session.commit()
        session.refresh(epic)
        
        assert epic.id is not None
        assert epic.name == "Test Epic"
        assert epic.description == "This is a test epic for the unit tests"
        assert isinstance(epic.created_at, datetime)
        
    def test_feature_model_creation(self, session):
        """Test Feature model creation and relationships"""
        # Create epic first
        epic = Epic(name="Test Epic", description="Test epic description")
        session.add(epic)
        session.commit()
        session.refresh(epic)
        
        # Create feature
        feature = Feature(
            epic_id=epic.id,
            name="Test Feature",
            description="Test feature description"
        )
        session.add(feature)
        session.commit()
        session.refresh(feature)
        
        assert feature.id is not None
        assert feature.epic_id == epic.id
        assert feature.name == "Test Feature"
        assert feature.description == "Test feature description"
        
    def test_task_model_creation(self, session):
        """Test Task model creation and fields"""
        # Create agent first
        agent = Agent(
            agent_id="test_creator",
            role=AgentRole.PM,
            level=DifficultyLevel.SENIOR
        )
        session.add(agent)
        session.commit()
        session.refresh(agent)
        
        # Create epic and feature
        epic = Epic(name="Test Epic", description="Test description")
        session.add(epic)
        session.commit()
        session.refresh(epic)
        
        feature = Feature(epic_id=epic.id, name="Test Feature", description="Test feature")
        session.add(feature)
        session.commit()
        session.refresh(feature)
        
        # Create task
        task = Task(
            feature_id=feature.id,
            title="Test Task",
            description="Test task description",
            created_by_id=agent.id,
            target_role=AgentRole.BACKEND_DEV,
            difficulty=DifficultyLevel.SENIOR,
            complexity=TaskComplexity.MINOR,
            branch="main",
            status=TaskStatus.CREATED
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        
        assert task.id is not None
        assert task.feature_id == feature.id
        assert task.title == "Test Task"
        assert task.description == "Test task description"
        assert task.created_by_id == agent.id
        assert task.target_role == AgentRole.BACKEND_DEV
        assert task.difficulty == DifficultyLevel.SENIOR
        assert task.complexity == TaskComplexity.MINOR
        assert task.status == TaskStatus.CREATED
        assert task.branch == "main"
        
    def test_document_model_creation(self, session):
        """Test Document model creation"""
        # Create agent first
        agent = Agent(
            agent_id="test_author",
            role=AgentRole.BACKEND_DEV,
            level=DifficultyLevel.SENIOR
        )
        session.add(agent)
        session.commit()
        session.refresh(agent)
        
        # Create document
        document = Document(
            doc_type=DocumentType.UPDATE,
            title="Test Document",
            content="This is a test document with @test_mention",
            author_id=agent.agent_id
        )
        session.add(document)
        session.commit()
        session.refresh(document)
        
        assert document.id is not None
        assert document.doc_type == DocumentType.UPDATE
        assert document.title == "Test Document"
        assert document.content == "This is a test document with @test_mention"
        assert document.author_id == agent.agent_id
        assert isinstance(document.created_at, datetime)
        
    def test_service_model_creation(self, session):
        """Test Service model creation"""
        service = Service(
            service_name="test-service",
            owner_agent_id="test_agent",
            ping_url="http://localhost:8080/health",
            port=8080,
            status=ServiceStatus.UP
        )
        session.add(service)
        session.commit()
        session.refresh(service)
        
        assert service.id is not None
        assert service.service_name == "test-service"
        assert service.owner_agent_id == "test_agent"
        assert service.ping_url == "http://localhost:8080/health"
        assert service.status == ServiceStatus.UP
        assert service.port == 8080
        assert isinstance(service.updated_at, datetime)
        
    def test_mention_model_creation(self, session):
        """Test Mention model creation"""
        # Create agent and document first
        agent = Agent(
            agent_id="test_author",
            role=AgentRole.BACKEND_DEV,
            level=DifficultyLevel.SENIOR
        )
        session.add(agent)
        session.commit()
        session.refresh(agent)
        
        document = Document(
            doc_type=DocumentType.UPDATE,
            title="Test Document",
            content="Test content",
            author_id=agent.agent_id
        )
        session.add(document)
        session.commit()
        session.refresh(document)
        
        # Create mention
        mention = Mention(
            document_id=document.id,
            mentioned_agent_id="mentioned_agent_001",
            created_by=agent.agent_id
        )
        session.add(mention)
        session.commit()
        session.refresh(mention)
        
        assert mention.id is not None
        assert mention.document_id == document.id
        assert mention.mentioned_agent_id == "mentioned_agent_001"
        assert mention.created_by == agent.agent_id
        assert isinstance(mention.created_at, datetime)
        
    def test_task_evaluation_model_creation(self, session):
        """Test TaskEvaluation model creation"""
        # Create necessary dependencies
        agent = Agent(
            agent_id="test_creator",
            role=AgentRole.PM,
            level=DifficultyLevel.SENIOR
        )
        session.add(agent)
        session.commit()
        session.refresh(agent)
        
        epic = Epic(name="Test Epic", description="Test")
        session.add(epic)
        session.commit()
        session.refresh(epic)
        
        feature = Feature(epic_id=epic.id, name="Test Feature", description="Test")
        session.add(feature)
        session.commit()
        session.refresh(feature)
        
        task = Task(
            feature_id=feature.id,
            title="Test Task",
            description="Test",
            created_by_id=agent.id,
            target_role=AgentRole.BACKEND_DEV,
            difficulty=DifficultyLevel.SENIOR,
            complexity=TaskComplexity.MINOR,
            branch="main"
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        
        # Create evaluation
        evaluation = TaskEvaluation(
            task_id=task.id,
            evaluated_by=agent.agent_id,
            approved=True,
            comment="This task looks good"
        )
        session.add(evaluation)
        session.commit()
        session.refresh(evaluation)
        
        assert evaluation.id is not None
        assert evaluation.task_id == task.id
        assert evaluation.evaluated_by == agent.agent_id
        assert evaluation.approved is True
        assert evaluation.comment == "This task looks good"
        assert isinstance(evaluation.evaluated_at, datetime)
        
    def test_model_relationships(self, session):
        """Test model relationships work correctly"""
        # Create agent
        agent = Agent(
            agent_id="test_creator",
            role=AgentRole.PM,
            level=DifficultyLevel.SENIOR
        )
        session.add(agent)
        session.commit()
        session.refresh(agent)
        
        # Create epic with feature and task
        epic = Epic(name="Test Epic", description="Test")
        session.add(epic)
        session.commit()
        session.refresh(epic)
        
        feature = Feature(epic_id=epic.id, name="Test Feature", description="Test")
        session.add(feature)
        session.commit()
        session.refresh(feature)
        
        task = Task(
            feature_id=feature.id,
            title="Test Task",
            description="Test",
            created_by_id=agent.id,
            target_role=AgentRole.BACKEND_DEV,
            difficulty=DifficultyLevel.SENIOR,
            complexity=TaskComplexity.MINOR,
            branch="main"
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        
        # Test relationships
        assert len(agent.tasks_created) == 1
        assert agent.tasks_created[0].id == task.id
        assert len(epic.features) == 1
        assert epic.features[0].id == feature.id
        assert len(feature.tasks) == 1
        assert feature.tasks[0].id == task.id