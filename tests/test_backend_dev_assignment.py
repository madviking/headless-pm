#!/usr/bin/env python3
"""
Test script to demonstrate backend_dev task assignment scenarios
"""

import time
import os
import pytest
import tempfile

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from src.main import app
from src.api.dependencies import get_session

# API configuration
API_KEY = os.getenv("API_KEY", "XXXXXX")
headers = {"X-API-Key": API_KEY}

# --- Fixtures copied from other tests for consistency ---

@pytest.fixture(name="session")
def session_fixture():
    """Create a new database session for each test."""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_file.close()
    engine = create_engine(
        f"sqlite:///{db_file.name}",
        connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        # Cleanup - guaranteed to run even if test fails/times out
        try:
            engine.dispose()
        except Exception:
            pass
        try:
            os.unlink(db_file.name)
        except Exception:
            pass

@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client that uses the test database session."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# --- Helper functions refactored to use the client fixture ---

def api_request(client: TestClient, method, endpoint, data=None, params=None):
    """Make API request using TestClient"""
    if method.upper() == "GET":
        response = client.get(f"/api/v1{endpoint}", headers=headers, params=params)
    elif method.upper() == "POST":
        response = client.post(f"/api/v1{endpoint}", json=data, headers=headers, params=params)
    elif method.upper() == "PUT":
        response = client.put(f"/api/v1{endpoint}", json=data, headers=headers, params=params)
    else:
        raise ValueError(f"Unsupported method: {method}")

    if response.status_code == 200:
        return response.json()
    else:
        print(f"API Error {response.status_code}: {response.text}")
        return None

def register_agent_api(client: TestClient, agent_id, role, level):
    """Register agent via TestClient"""
    data = {
        "agent_id": agent_id,
        "role": role,
        "level": level,
        "connection_type": "client"
    }
    return api_request(client, "POST", "/register", data=data)

def get_next_task_api(client: TestClient, role, level, simulate=True, timeout=None):
    """Get next task via TestClient"""
    params = {"role": role, "level": level}
    if simulate:
        params["simulate"] = "true"
    if timeout is not None:
        params["timeout"] = timeout
    return api_request(client, "GET", "/tasks/next", params=params)

def lock_task_api(client: TestClient, task_id, agent_id):
    """Lock task via TestClient"""
    return api_request(client, "POST", f"/tasks/{task_id}/lock", params={"agent_id": agent_id})

# --- The main test function, now using fixtures ---

def test_backend_dev_scenarios(client: TestClient):
    """Test different backend_dev task assignment scenarios"""
    print("=== Backend Developer Task Assignment Test ===\n")

    # Register different level backend devs
    agents = [
        ("backend_junior_1", "junior"),
        ("backend_senior_1", "senior"),
        ("backend_principal_1", "principal")
    ]

    print("1. Registering backend developers at different levels:")
    for agent_id, level in agents:
        result = register_agent_api(client, agent_id, "backend_dev", level)
        # This assertion is important to ensure registration works before proceeding
        assert result is not None, f"Failed to register agent {agent_id}"
        task = result.get("next_task", {})
        if task and task.get("id", -1) > 0:
            print(f"   ✓ {agent_id} ({level}) - Got task: {task['title']} (difficulty: {task['difficulty']})")
        else:
            print(f"   ✓ {agent_id} ({level}) - No tasks available")

    print("\n2. Testing task assignment via /tasks/next endpoint:")
    for _, level in agents:
        result = get_next_task_api(client, "backend_dev", level, simulate=True)
        if result and result.get("id", -1) > 0:
            print(f"   ✓ {level} developer would get: {result['title']} (difficulty: {result['difficulty']})")
        else:
            print(f"   ✓ {level} developer - No tasks available")

    print("\n3. Testing task locking:")
    # First, find an available task
    available_task = get_next_task_api(client, "backend_dev", "junior", simulate=True)
    if available_task and available_task.get("id", -1) > 0:
        task_id = available_task["id"]
        # Lock the task
        result = lock_task_api(client, task_id, "backend_junior_1")
        assert result is not None, "Failed to lock task"
        print(f"   ✓ Task locked by backend_junior_1: {result['title']}")

        # Try to get next task as another junior dev
        result = get_next_task_api(client, "backend_dev", "junior", simulate=True)
        if result and result.get("id", -1) > 0:
            print(f"   ✓ Another junior dev would now get: {result['title']}")
        else:
            print(f"   ✓ No more junior tasks available (as expected)")
    else:
        print("   ⚠ No tasks available to test locking")

    print("\n4. Current task distribution:")
    # Query all backend_dev tasks
    response = client.get("/api/v1/tasks", headers=headers, params={"role": "backend_dev"})
    assert response.status_code == 200

    tasks = response.json()
    status_count = {}
    difficulty_count = {}

    for task in tasks:
        status = task["status"]
        difficulty = task["difficulty"]
        status_count[status] = status_count.get(status, 0) + 1
        difficulty_count[difficulty] = difficulty_count.get(difficulty, 0) + 1

    print("   Task statuses:")
    for status, count in status_count.items():
        print(f"     - {status}: {count}")

    print("   Task difficulties:")
    for difficulty, count in difficulty_count.items():
        print(f"     - {difficulty}: {count}")

    print(f"\n   Total backend_dev tasks: {len(tasks)}")

    # Show available tasks
    available = [t for t in tasks if t["status"] == "created" and not t["locked_by"]]
    print(f"   Available (unlocked) tasks: {len(available)}")
    for task in available[:5]:  # Show first 5
        print(f"     - {task['title']} (difficulty: {task['difficulty']})")

    print("\n5. Testing wait functionality (with 3-second timeout):")
    # Test waiting behavior with a role that has no tasks
    start_time = time.time()
    result = get_next_task_api(client, "architect", "senior", simulate=False, timeout=3)
    elapsed = time.time() - start_time

    if result and result.get("id", -1) > 0:
        print(f"   ✓ Found architect task after {elapsed:.1f}s: {result['title']}")
    else:
        print(f"   ✓ No architect tasks found after waiting {elapsed:.1f}s (expected behavior)")
        assert 2.5 <= elapsed <= 4.0, f"Wait time unexpected: {elapsed:.1f}s (expected ~3s)"
        print(f"   ✓ Wait time is correct (~3s)")
