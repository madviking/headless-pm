#!/usr/bin/env python3
"""
Test script to demonstrate backend_dev task assignment scenarios
"""

import subprocess
import json
import time
import os
import requests
from datetime import datetime

# API configuration
API_KEY = "fi12jsm1212"
BASE_URL = "http://localhost:6969/api/v1"

def api_request(method, endpoint, data=None, params=None):
    """Make direct API request without using CLI"""
    
    headers = {"X-API-Key": API_KEY}
    url = f"{BASE_URL}{endpoint}"
    
    if method.upper() == "GET":
        response = requests.get(url, headers=headers, params=params)
    elif method.upper() == "POST":
        response = requests.post(url, json=data, headers=headers, params=params)
    elif method.upper() == "PUT":
        response = requests.put(url, json=data, headers=headers, params=params)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"API Error {response.status_code}: {response.text}")
        return None

def register_agent_api(agent_id, role, level):
    """Register agent via direct API call"""
    data = {
        "agent_id": agent_id,
        "role": role,
        "level": level,
        "connection_type": "client"
    }
    return api_request("POST", "/register", data=data)

def get_next_task_api(role, level, simulate=True, timeout=None):
    """Get next task via direct API call"""
    params = {"role": role, "level": level}
    if simulate:
        params["simulate"] = "true"
    if timeout is not None:
        params["timeout"] = timeout
    return api_request("GET", "/tasks/next", params=params)

def lock_task_api(task_id, agent_id):
    """Lock task via direct API call"""
    return api_request("POST", f"/tasks/{task_id}/lock", params={"agent_id": agent_id})

def test_backend_dev_scenarios():
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
        result = register_agent_api(agent_id, "backend_dev", level)
        if result:
            task = result.get("next_task", {})
            if task and task.get("id", -1) > 0:
                print(f"   ✓ {agent_id} ({level}) - Got task: {task['title']} (difficulty: {task['difficulty']})")
            else:
                print(f"   ✓ {agent_id} ({level}) - No tasks available")
    
    print("\n2. Testing task assignment via /tasks/next endpoint:")
    for _, level in agents:
        result = get_next_task_api("backend_dev", level, simulate=True)
        if result and result.get("id", -1) > 0:
            print(f"   ✓ {level} developer would get: {result['title']} (difficulty: {result['difficulty']})")
        else:
            print(f"   ✓ {level} developer - No tasks available")
    
    print("\n3. Testing task locking:")
    # First, find an available task
    available_task = get_next_task_api("backend_dev", "junior", simulate=True)
    if available_task and available_task.get("id", -1) > 0:
        task_id = available_task["id"]
        # Lock the task
        result = lock_task_api(task_id, "backend_junior_1")
        if result:
            print(f"   ✓ Task locked by backend_junior_1: {result['title']}")
        
        # Try to get next task as another junior dev
        result = get_next_task_api("backend_dev", "junior", simulate=True)
        if result and result.get("id", -1) > 0:
            print(f"   ✓ Another junior dev would now get: {result['title']}")
        else:
            print(f"   ✓ No more junior tasks available (as expected)")
    else:
        print("   ⚠ No tasks available to test locking")
    
    print("\n4. Current task distribution:")
    # Query all backend_dev tasks
    headers = {"X-API-Key": API_KEY}
    response = requests.get(f"{BASE_URL}/tasks?role=backend_dev", headers=headers)
    
    if response.status_code == 200:
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
    result = get_next_task_api("architect", "senior", simulate=False, timeout=3)  # Use actual waiting with 3s timeout
    elapsed = time.time() - start_time
    
    if result and result.get("id", -1) > 0:
        print(f"   ✓ Found architect task after {elapsed:.1f}s: {result['title']}")
    else:
        print(f"   ✓ No architect tasks found after waiting {elapsed:.1f}s (expected behavior)")
        if 2.5 <= elapsed <= 4.0:
            print(f"   ✓ Wait time is correct (~3s)")
        else:
            print(f"   ⚠ Wait time unexpected: {elapsed:.1f}s (expected ~3s)")

if __name__ == "__main__":
    # Ensure we're in the venv
    import sys
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Please run this script in the virtual environment:")
        print("source venv/bin/activate")
        sys.exit(1)
    
    test_backend_dev_scenarios()