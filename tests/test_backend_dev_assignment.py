#!/usr/bin/env python3
"""
Test script to demonstrate backend_dev task assignment scenarios
"""

import subprocess
import json
import time
from datetime import datetime

# API configuration
API_KEY = "fi12jsm1212"
BASE_URL = "http://localhost:6969/api/v1"

def run_client_command(cmd):
    """Run headless_pm_client.py command and return JSON output"""
    full_cmd = ["python", "agents/client/headless_pm_client.py"] + cmd
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"Error: {result.stderr}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Could not parse JSON from: {result.stdout}")
        return None

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
        result = run_client_command([
            "register", 
            "--agent-id", agent_id,
            "--role", "backend_dev",
            "--level", level
        ])
        if result:
            task = result.get("next_task", {})
            if task.get("id", -1) > 0:
                print(f"   ✓ {agent_id} ({level}) - Got task: {task['title']} (difficulty: {task['difficulty']})")
            else:
                print(f"   ✓ {agent_id} ({level}) - No tasks available")
    
    print("\n2. Testing task assignment via /tasks/next endpoint:")
    for _, level in agents:
        result = run_client_command([
            "tasks", "next",
            "--role", "backend_dev", 
            "--level", level
        ])
        if result and result.get("id", -1) > 0:
            print(f"   ✓ {level} developer would get: {result['title']} (difficulty: {result['difficulty']})")
        else:
            print(f"   ✓ {level} developer - No tasks available")
    
    print("\n3. Testing task locking:")
    # Lock a task
    result = run_client_command([
        "tasks", "lock", "76",
        "--agent-id", "backend_junior_1"
    ])
    if result:
        print(f"   ✓ Task locked by backend_junior_1: {result['title']}")
    
    # Try to get next task as another junior dev
    result = run_client_command([
        "tasks", "next",
        "--role", "backend_dev",
        "--level", "junior"
    ])
    if result and result.get("id", -1) > 0:
        print(f"   ✓ Another junior dev would now get: {result['title']}")
    else:
        print(f"   ✓ No more junior tasks available (as expected)")
    
    print("\n4. Current task distribution:")
    # Query all backend_dev tasks
    import requests
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

if __name__ == "__main__":
    # Ensure we're in the venv
    import sys
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Please run this script in the virtual environment:")
        print("source venv/bin/activate")
        sys.exit(1)
    
    test_backend_dev_scenarios()