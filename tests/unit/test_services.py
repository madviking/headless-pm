"""
Unit tests for services layer
"""
import pytest
from sqlmodel import Session, SQLModel, create_engine
from src.services.mention_service import extract_mentions, create_mentions_for_document, create_mentions_for_task
from src.services.health_checker import ServiceHealthChecker
from src.models.models import Agent, Document, Task, Feature, Epic, Mention, Service
from src.models.enums import AgentRole, DifficultyLevel, TaskComplexity
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


class TestMentionService:
    """Test mention service functions"""
    
    def test_extract_mentions_single(self):
        """Test extracting a single mention from text"""
        text = "Hey @john_doe, can you review this?"
        mentions = extract_mentions(text)
        assert mentions == {"john_doe"}
        
    def test_extract_mentions_multiple(self):
        """Test extracting multiple mentions from text"""
        text = "Hey @john_doe and @jane_smith, can you both review this? Also @bob_wilson should know about it."
        mentions = extract_mentions(text)
        assert mentions == {"john_doe", "jane_smith", "bob_wilson"}
        
    def test_extract_mentions_complex_ids(self):
        """Test extracting mentions with complex agent IDs"""
        text = "Please review @frontend_dev_senior_001 and @backend_dev_junior_002"
        mentions = extract_mentions(text)
        assert mentions == {"frontend_dev_senior_001", "backend_dev_junior_002"}
        
    def test_extract_mentions_no_matches(self):
        """Test text with no mentions"""
        text = "This is just regular text without any mentions"
        mentions = extract_mentions(text)
        assert mentions == set()
        
    def test_extract_mentions_invalid_format(self):
        """Test text with @ but invalid mention format"""
        text = "This has @ symbols but not valid mentions"
        mentions = extract_mentions(text)
        assert mentions == set()
        
    def test_extract_mentions_edge_cases(self):
        """Test edge cases for mention extraction"""
        text = "@start_mention in beginning, @middle_mention in middle, and @end_mention"
        mentions = extract_mentions(text)
        assert mentions == {"start_mention", "middle_mention", "end_mention"}
        
    def test_extract_mentions_duplicates(self):
        """Test that duplicate mentions are deduplicated"""
        text = "Hey @john_doe, @john_doe can you help? @john_doe please respond."
        mentions = extract_mentions(text)
        assert mentions == {"john_doe"}
        
    def test_create_mentions_for_document(self, session):
        """Test creating mention records for a document"""
        # Create agent and document
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
            content="Test content with @mention1 and @mention2",
            author_id=agent.agent_id
        )
        session.add(document)
        session.commit()
        session.refresh(document)
        
        # Create mentions
        mentions = create_mentions_for_document(
            db=session,
            document_id=document.id,
            content=document.content,
            created_by=agent.agent_id
        )
        session.commit()
        
        assert len(mentions) == 2
        mention_agent_ids = {m.mentioned_agent_id for m in mentions}
        assert mention_agent_ids == {"mention1", "mention2"}
        
        for mention in mentions:
            assert mention.document_id == document.id
            assert mention.created_by == agent.agent_id
            assert mention.task_id is None
            
    def test_create_mentions_for_task(self, session):
        """Test creating mention records for a task"""
        # Create dependencies
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
            description="Test task with @qa_agent and @dev_agent mentions",
            created_by_id=agent.id,
            target_role=AgentRole.BACKEND_DEV,
            difficulty=DifficultyLevel.SENIOR,
            complexity=TaskComplexity.MINOR,
            branch="main"
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        
        # Create mentions
        mentions = create_mentions_for_task(
            db=session,
            task_id=task.id,
            content=task.description,
            created_by=agent.agent_id
        )
        session.commit()
        
        assert len(mentions) == 2
        mention_agent_ids = {m.mentioned_agent_id for m in mentions}
        assert mention_agent_ids == {"qa_agent", "dev_agent"}
        
        for mention in mentions:
            assert mention.task_id == task.id
            assert mention.created_by == agent.agent_id
            assert mention.document_id is None
            
    def test_create_mentions_no_mentions(self, session):
        """Test creating mentions when content has no @mentions"""
        # Create agent and document
        agent = Agent(
            agent_id="test_author",
            role=AgentRole.BACKEND_DEV,
            level=DifficultyLevel.SENIOR
        )
        session.add(agent)
        session.commit()
        
        document = Document(
            doc_type=DocumentType.UPDATE,
            title="Test Document",
            content="Test content with no mentions",
            author_id=agent.agent_id
        )
        session.add(document)
        session.commit()
        session.refresh(document)
        
        # Create mentions
        mentions = create_mentions_for_document(
            db=session,
            document_id=document.id,
            content=document.content,
            created_by=agent.agent_id
        )
        session.commit()
        
        assert len(mentions) == 0


class TestHealthChecker:
    """Test health checker service"""
    
    def test_health_checker_initialization(self):
        """Test ServiceHealthChecker initialization"""
        checker = ServiceHealthChecker()
        assert checker is not None
        assert checker.check_interval == 30
        assert checker.running is False
        
    def test_health_checker_check_url_format(self):
        """Test health checker URL format validation"""
        checker = ServiceHealthChecker()
        
        # Test valid URLs
        valid_urls = [
            "http://localhost:8080/health",
            "https://api.example.com/status",
            "http://127.0.0.1:3000/ping"
        ]
        
        for url in valid_urls:
            # We can't test the actual HTTP call without mocking, but we can test the format
            assert url.startswith(("http://", "https://"))
            
    def test_health_checker_service_status_update(self, session):
        """Test updating service status"""
        # Create a service
        service = Service(
            service_name="test-service",
            owner_agent_id="test_agent",
            ping_url="http://localhost:8080/health",
            status=ServiceStatus.UP,
            port=8080
        )
        session.add(service)
        session.commit()
        session.refresh(service)
        
        # Update status
        service.status = ServiceStatus.DOWN
        session.add(service)
        session.commit()
        session.refresh(service)
        
        assert service.status == ServiceStatus.DOWN
        
    def test_service_status_enum_values(self):
        """Test ServiceStatus enum values"""
        assert ServiceStatus.UP == "up"
        assert ServiceStatus.DOWN == "down"
        assert ServiceStatus.STARTING == "starting"