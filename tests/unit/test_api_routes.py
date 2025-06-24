"""
Unit tests for API routes and endpoints
"""
import pytest
import json
import tempfile
import os
from datetime import datetime
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from src.main import app
from src.api.dependencies import get_session
from src.models.models import Agent, Epic, Feature, Task, Document, Service
from src.models.enums import AgentRole, DifficultyLevel, TaskStatus, TaskComplexity, ConnectionType
from src.models.document_enums import DocumentType, ServiceStatus


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


@pytest.fixture
def client(session):
    """Create test client with overridden dependencies"""
    def override_get_session():
        yield session
    
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def api_headers():
    """API headers with authentication"""
    return {"X-API-Key": "fi12jsm1212"}


class TestAgentRoutes:
    """Test agent-related API endpoints"""
    
    def test_register_agent(self, client, api_headers):
        """Test agent registration endpoint"""
        agent_data = {
            "agent_id": "test_agent_001",
            "role": "backend_dev",
            "level": "senior",
            "connection_type": "client"
        }
        
        response = client.post("/api/v1/register", json=agent_data, headers=api_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "agent" in data
        assert data["agent"]["agent_id"] == "test_agent_001"
        assert data["agent"]["role"] == "backend_dev"
        assert data["agent"]["level"] == "senior"
        assert data["agent"]["connection_type"] == "client"
        
    def test_register_agent_duplicate(self, client, api_headers, session):
        """Test registering duplicate agent"""
        # Create agent first
        agent = Agent(
            agent_id="duplicate_agent",
            role=AgentRole.BACKEND_DEV,
            level=DifficultyLevel.SENIOR
        )
        session.add(agent)
        session.commit()
        
        # Try to register same agent
        agent_data = {
            "agent_id": "duplicate_agent",
            "role": "frontend_dev",
            "level": "junior"
        }
        
        response = client.post("/api/v1/register", json=agent_data, headers=api_headers)
        assert response.status_code == 200  # Should update existing agent
        
    def test_list_agents(self, client, api_headers, session):
        """Test listing agents endpoint"""
        # Create test agents
        agents = [
            Agent(agent_id="agent_1", role=AgentRole.BACKEND_DEV, level=DifficultyLevel.SENIOR),
            Agent(agent_id="agent_2", role=AgentRole.FRONTEND_DEV, level=DifficultyLevel.JUNIOR),
        ]
        for agent in agents:
            session.add(agent)
        session.commit()
        
        response = client.get("/api/v1/agents", headers=api_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        agent_ids = [agent["agent_id"] for agent in data]
        assert "agent_1" in agent_ids
        assert "agent_2" in agent_ids
        
    def test_delete_agent_as_pm(self, client, api_headers, session):
        """Test deleting agent as PM"""
        # Create PM agent
        pm_agent = Agent(
            agent_id="pm_agent",
            role=AgentRole.PM,
            level=DifficultyLevel.SENIOR
        )
        session.add(pm_agent)
        
        # Create target agent to delete
        target_agent = Agent(
            agent_id="target_agent",
            role=AgentRole.BACKEND_DEV,
            level=DifficultyLevel.JUNIOR
        )
        session.add(target_agent)
        session.commit()
        
        # Delete agent
        response = client.delete(
            f"/api/v1/agents/{target_agent.agent_id}?requester_agent_id=pm_agent",
            headers=api_headers
        )
        if response.status_code != 200:
            print(f"Error response: {response.json()}")
        assert response.status_code == 200
        
    def test_get_context(self, client, api_headers):
        """Test getting project context"""
        response = client.get("/api/v1/context", headers=api_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "project_name" in data
        assert "database_type" in data
        assert "instructions_path" in data
        assert "project_docs_path" in data


class TestEpicRoutes:
    """Test epic-related API endpoints"""
    
    def test_create_epic_as_pm(self, client, api_headers, session):
        """Test creating epic as PM"""
        # Create PM agent
        pm_agent = Agent(
            agent_id="pm_agent",
            role=AgentRole.PM,
            level=DifficultyLevel.SENIOR
        )
        session.add(pm_agent)
        session.commit()
        
        epic_data = {
            "name": "Test Epic",
            "description": "This is a test epic"
        }
        
        response = client.post("/api/v1/epics?agent_id=pm_agent", json=epic_data, headers=api_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Test Epic"
        assert data["description"] == "This is a test epic"
        
    def test_create_epic_unauthorized(self, client, api_headers, session):
        """Test creating epic as non-PM (should fail)"""
        # Create non-PM agent
        dev_agent = Agent(
            agent_id="dev_agent",
            role=AgentRole.BACKEND_DEV,
            level=DifficultyLevel.SENIOR
        )
        session.add(dev_agent)
        session.commit()
        
        epic_data = {
            "name": "Test Epic",
            "description": "This is a test epic"
        }
        
        response = client.post("/api/v1/epics?agent_id=dev_agent", json=epic_data, headers=api_headers)
        assert response.status_code == 403
        
    def test_list_epics(self, client, api_headers, session):
        """Test listing epics"""
        # Create test epics
        epics = [
            Epic(name="Epic 1", description="First epic"),
            Epic(name="Epic 2", description="Second epic"),
        ]
        for epic in epics:
            session.add(epic)
        session.commit()
        
        response = client.get("/api/v1/epics", headers=api_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        epic_names = [epic["name"] for epic in data]
        assert "Epic 1" in epic_names
        assert "Epic 2" in epic_names


class TestTaskRoutes:
    """Test task-related API endpoints"""
    
    def test_create_task(self, client, api_headers, session):
        """Test creating a task"""
        # Create dependencies
        agent = Agent(agent_id="creator", role=AgentRole.PM, level=DifficultyLevel.SENIOR)
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
        
        task_data = {
            "feature_id": feature.id,
            "title": "Test Task",
            "description": "Test task description",
            "target_role": "backend_dev",
            "difficulty": "senior",
            "complexity": "minor",
            "branch": "main"
        }
        
        response = client.post("/api/v1/tasks/create?agent_id=creator", json=task_data, headers=api_headers)
        if response.status_code != 200:
            print(f"Error response: {response.json()}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "Test task description"
        assert data["target_role"] == "backend_dev"
        assert data["difficulty"] == "senior"
        assert data["complexity"] == "minor"
        
    def test_get_next_task(self, client, api_headers, session):
        """Test getting next available task"""
        # Create dependencies
        agent = Agent(agent_id="creator", role=AgentRole.PM, level=DifficultyLevel.SENIOR)
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
            title="Available Task",
            description="Test",
            created_by_id=agent.id,
            target_role=AgentRole.BACKEND_DEV,
            difficulty=DifficultyLevel.SENIOR,
            complexity=TaskComplexity.MINOR,
            branch="main",
            status=TaskStatus.CREATED
        )
        session.add(task)
        session.commit()
        
        response = client.get(
            "/api/v1/tasks/next?role=backend_dev&level=senior",
            headers=api_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Available Task"
        assert data["target_role"] == "backend_dev"
        
    def test_lock_task(self, client, api_headers, session):
        """Test locking a task"""
        # Create dependencies
        agent = Agent(agent_id="creator", role=AgentRole.PM, level=DifficultyLevel.SENIOR)
        session.add(agent)
        
        locker_agent = Agent(agent_id="locker", role=AgentRole.BACKEND_DEV, level=DifficultyLevel.SENIOR)
        session.add(locker_agent)
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
            title="Lockable Task",
            description="Test",
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
        
        response = client.post(
            f"/api/v1/tasks/{task.id}/lock?agent_id=locker",
            headers=api_headers
        )
        assert response.status_code == 200
        
    def test_update_task_status(self, client, api_headers, session):
        """Test updating task status"""
        # Create dependencies
        agent = Agent(agent_id="creator", role=AgentRole.PM, level=DifficultyLevel.SENIOR)
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
            title="Status Task",
            description="Test",
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
        
        status_data = {
            "status": "under_work",
            "notes": "Started working on this task"
        }
        
        response = client.put(
            f"/api/v1/tasks/{task.id}/status?agent_id=creator",
            json=status_data,
            headers=api_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "task" in data
        assert data["task"]["status"] == "under_work"
        assert data["task"]["notes"] == "Started working on this task"


class TestDocumentRoutes:
    """Test document-related API endpoints"""
    
    def test_create_document(self, client, api_headers, session):
        """Test creating a document"""
        # Create author agent
        agent = Agent(
            agent_id="doc_author",
            role=AgentRole.BACKEND_DEV,
            level=DifficultyLevel.SENIOR
        )
        session.add(agent)
        session.commit()
        
        doc_data = {
            "doc_type": "update",
            "title": "Test Document",
            "content": "This is a test document with @mention"
        }
        
        response = client.post("/api/v1/documents?author_id=doc_author", json=doc_data, headers=api_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Test Document"
        assert data["content"] == "This is a test document with @mention"
        assert data["author_id"] == "doc_author"
        assert data["doc_type"] == "update"
        
    def test_list_documents(self, client, api_headers, session):
        """Test listing documents"""
        # Create author agent
        agent = Agent(
            agent_id="doc_author",
            role=AgentRole.BACKEND_DEV,
            level=DifficultyLevel.SENIOR
        )
        session.add(agent)
        session.commit()
        
        # Create test documents
        documents = [
            Document(
                doc_type=DocumentType.UPDATE,
                title="Doc 1",
                content="Content 1",
                author_id=agent.agent_id
            ),
            Document(
                doc_type=DocumentType.STANDUP,
                title="Doc 2",
                content="Content 2",
                author_id=agent.agent_id
            ),
        ]
        for doc in documents:
            session.add(doc)
        session.commit()
        
        response = client.get("/api/v1/documents", headers=api_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        doc_titles = [doc["title"] for doc in data]
        assert "Doc 1" in doc_titles
        assert "Doc 2" in doc_titles


class TestServiceRoutes:
    """Test service-related API endpoints"""
    
    def test_register_service(self, client, api_headers):
        """Test service registration"""
        service_data = {
            "service_name": "test-service",
            "ping_url": "http://localhost:8080/health",
            "port": 8080
        }
        
        response = client.post("/api/v1/services/register?agent_id=test_agent", json=service_data, headers=api_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["service_name"] == "test-service"
        assert data["owner_agent_id"] == "test_agent"
        assert data["ping_url"] == "http://localhost:8080/health"
        assert data["port"] == 8080
        
    def test_list_services(self, client, api_headers, session):
        """Test listing services"""
        # Create test services
        services = [
            Service(
                service_name="service-1",
                owner_agent_id="test_agent",
                ping_url="http://localhost:8001/health",
                status=ServiceStatus.UP,
                port=8001
            ),
            Service(
                service_name="service-2",
                owner_agent_id="test_agent",
                ping_url="http://localhost:8002/health",
                status=ServiceStatus.DOWN,
                port=8002
            ),
        ]
        for service in services:
            session.add(service)
        session.commit()
        
        response = client.get("/api/v1/services", headers=api_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        service_names = [service["service_name"] for service in data]
        assert "service-1" in service_names
        assert "service-2" in service_names
        
    def test_service_heartbeat(self, client, api_headers, session):
        """Test service heartbeat"""
        # Create service
        service = Service(
            service_name="heartbeat-service",
            owner_agent_id="test_agent",
            ping_url="http://localhost:8080/health",
            status=ServiceStatus.UP,
            port=8080
        )
        session.add(service)
        session.commit()
        
        response = client.post(
            "/api/v1/services/heartbeat-service/heartbeat?agent_id=test_agent",
            headers=api_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["service_name"] == "heartbeat-service"
        assert data["status"] == "up"


class TestAuthenticationAndErrors:
    """Test authentication and error handling"""
    
    def test_missing_api_key(self, client):
        """Test API calls without API key"""
        response = client.get("/api/v1/agents")
        assert response.status_code == 401
        
    def test_invalid_api_key(self, client):
        """Test API calls with invalid API key"""
        headers = {"X-API-Key": "invalid-key"}
        response = client.get("/api/v1/agents", headers=headers)
        assert response.status_code == 401
        
    def test_not_found_endpoints(self, client, api_headers):
        """Test non-existent endpoints"""
        response = client.get("/api/v1/nonexistent", headers=api_headers)
        assert response.status_code == 404