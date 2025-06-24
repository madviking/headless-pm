"""
Unit tests for API schemas
"""
import pytest
from datetime import datetime
from src.api.schemas import *


class TestRequestSchemas:
    """Test request schema validation"""
    
    def test_agent_register_request(self):
        """Test AgentRegisterRequest schema"""
        data = {
            "agent_id": "test_agent_001",
            "role": "backend_dev",
            "level": "senior",
            "connection_type": "client"
        }
        
        request = AgentRegisterRequest(**data)
        assert request.agent_id == "test_agent_001"
        assert request.role == "backend_dev"
        assert request.level == "senior"
        assert request.connection_type == "client"
        
    def test_agent_register_request_defaults(self):
        """Test AgentRegisterRequest with default values"""
        data = {
            "agent_id": "test_agent_002",
            "role": "frontend_dev",
            "level": "junior"
        }
        
        request = AgentRegisterRequest(**data)
        assert request.connection_type == "client"  # default value
        
    def test_epic_create_request(self):
        """Test EpicCreateRequest schema"""
        data = {
            "name": "Test Epic",
            "description": "This is a test epic"
        }
        
        request = EpicCreateRequest(**data)
        assert request.name == "Test Epic"
        assert request.description == "This is a test epic"
        
    def test_task_create_request(self):
        """Test TaskCreateRequest schema"""
        data = {
            "feature_id": 1,
            "title": "Test Task",
            "description": "Test task description",
            "target_role": "backend_dev",
            "difficulty": "senior",
            "branch": "feature/test-task"
        }
        
        request = TaskCreateRequest(**data)
        assert request.feature_id == 1
        assert request.title == "Test Task"
        assert request.description == "Test task description"
        assert request.target_role == "backend_dev"
        assert request.difficulty == "senior"
        assert request.branch == "feature/test-task"
        assert request.complexity == "major"  # default value
        
    def test_task_status_update_request(self):
        """Test TaskStatusUpdateRequest schema"""
        data = {
            "status": "dev_done",
            "notes": "Task completed successfully"
        }
        
        request = TaskStatusUpdateRequest(**data)
        assert request.status == "dev_done"
        assert request.notes == "Task completed successfully"
        
    def test_document_create_request(self):
        """Test DocumentCreateRequest schema"""
        data = {
            "doc_type": "update",
            "title": "Test Document",
            "content": "This is test content with @mention"
        }
        
        request = DocumentCreateRequest(**data)
        assert request.doc_type == "update"
        assert request.title == "Test Document"
        assert request.content == "This is test content with @mention"
        
    def test_service_register_request(self):
        """Test ServiceRegisterRequest schema"""
        data = {
            "service_name": "test-service",
            "ping_url": "http://localhost:8080/health",
            "port": 8080
        }
        
        request = ServiceRegisterRequest(**data)
        assert request.service_name == "test-service"
        assert request.ping_url == "http://localhost:8080/health"
        assert request.port == 8080
        assert request.status == "up"  # default value


class TestResponseSchemas:
    """Test response schema serialization"""
    
    def test_agent_response(self):
        """Test AgentResponse schema"""
        data = {
            "id": 1,
            "agent_id": "test_agent",
            "role": "backend_dev",
            "level": "senior",
            "connection_type": "client",
            "last_seen": datetime.utcnow()
        }
        
        response = AgentResponse(**data)
        assert response.id == 1
        assert response.agent_id == "test_agent"
        assert response.role == "backend_dev"
        assert response.level == "senior"
        assert response.connection_type == "client"
        assert isinstance(response.last_seen, datetime)
        
    def test_epic_response(self):
        """Test EpicResponse schema"""
        data = {
            "id": 1,
            "name": "Test Epic",
            "description": "Test description",
            "created_at": datetime.utcnow()
        }
        
        response = EpicResponse(**data)
        assert response.id == 1
        assert response.name == "Test Epic"
        assert response.description == "Test description"
        assert isinstance(response.created_at, datetime)
        
    def test_task_response(self):
        """Test TaskResponse schema"""
        data = {
            "id": 1,
            "feature_id": 1,
            "title": "Test Task",
            "description": "Test description",
            "created_by": "test_agent",
            "target_role": "backend_dev",
            "difficulty": "senior",
            "complexity": "minor",
            "branch": "main",
            "status": "created",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        response = TaskResponse(**data)
        assert response.id == 1
        assert response.feature_id == 1
        assert response.title == "Test Task"
        assert response.target_role == "backend_dev"
        assert response.status == "created"
        
    def test_document_response(self):
        """Test DocumentResponse schema"""
        data = {
            "id": 1,
            "doc_type": "update",
            "author_id": "author_agent",
            "title": "Test Document",
            "content": "Test content",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        response = DocumentResponse(**data)
        assert response.id == 1
        assert response.doc_type == "update"
        assert response.author_id == "author_agent"
        assert response.title == "Test Document"
        assert response.content == "Test content"
        
    def test_service_response(self):
        """Test ServiceResponse schema"""
        data = {
            "id": 1,
            "service_name": "test-service",
            "owner_agent_id": "owner",
            "ping_url": "http://localhost:8080/health",
            "port": 8080,
            "status": "up",
            "updated_at": datetime.utcnow()
        }
        
        response = ServiceResponse(**data)
        assert response.id == 1
        assert response.service_name == "test-service"
        assert response.owner_agent_id == "owner"
        assert response.ping_url == "http://localhost:8080/health"
        assert response.status == "up"


class TestValidation:
    """Test schema validation and error handling"""
    
    def test_invalid_agent_role(self):
        """Test validation with invalid agent role"""
        with pytest.raises(ValueError):
            AgentRegisterRequest(
                agent_id="test",
                role="invalid_role",
                level="senior"
            )
            
    def test_invalid_difficulty_level(self):
        """Test validation with invalid difficulty level"""
        with pytest.raises(ValueError):
            TaskCreateRequest(
                feature_id=1,
                title="Test",
                description="Test",
                created_by="agent",
                target_role="backend_dev",
                difficulty="invalid_level",
                complexity="minor"
            )
            
    def test_invalid_task_status(self):
        """Test validation with invalid task status"""
        with pytest.raises(ValueError):
            TaskStatusUpdateRequest(
                status="invalid_status",
                agent_id="agent"
            )
            
    def test_missing_required_field(self):
        """Test validation with missing required field"""
        with pytest.raises(ValueError):
            AgentRegisterRequest(
                role="backend_dev",
                level="senior"
                # Missing agent_id
            )
            
    def test_empty_string_validation(self):
        """Test validation with empty strings"""
        # Empty strings are actually allowed in these schemas
        request = EpicCreateRequest(
            name="",  # Empty name is allowed
            description="Valid description"
        )
        assert request.name == ""
        assert request.description == "Valid description"