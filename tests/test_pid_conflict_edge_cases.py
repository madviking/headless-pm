#!/usr/bin/env python3
"""
Comprehensive edge case tests for PID conflict detection.
Extracted from TDD artifact test_pid_conflict_detection.py with generalized paths.
"""

import os
import time
from pathlib import Path

# Add project root to path for imports
import sys
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.process_registry import check_pid_conflict


def test_pid_conflict_empty_data():
    """Test that empty data allows registration."""
    empty_data = {}
    assert check_pid_conflict(empty_data, 12345, 'api_server') == False
    print("✅ Test 1: Empty data allows registration")


def test_pid_conflict_different_pids():
    """Test that different PIDs are allowed."""
    data_different_pids = {
        'processes': {
            '12345': {'type': 'api_server', 'started': time.time()}
        }
    }
    assert check_pid_conflict(data_different_pids, 12346, 'mcp_client') == False
    print("✅ Test 2: Different PIDs allowed")


def test_pid_conflict_same_pid_different_type():
    """Test that same PID with different type is detected as conflict."""
    data_same_pid = {
        'processes': {
            '12345': {'type': 'api_server', 'started': time.time()}
        }
    }
    assert check_pid_conflict(data_same_pid, 12345, 'mcp_client') == True
    print("✅ Test 3: Same PID conflict detected")


def test_pid_conflict_idempotent():
    """Test that same PID same type is OK (idempotent registration)."""
    data_same_pid = {
        'processes': {
            '12345': {'type': 'api_server', 'started': time.time()}
        }
    }
    assert check_pid_conflict(data_same_pid, 12345, 'api_server') == False
    print("✅ Test 4: Same PID same type allowed (idempotent)")


def test_legacy_api_pid_conflicts():
    """Test legacy api_pid conflict detection."""
    legacy_data = {'api_pid': 12345}
    assert check_pid_conflict(legacy_data, 12345, 'mcp_client') == True
    print("✅ Test 5: Legacy api_pid conflict detected")


def test_legacy_clients_conflicts():
    """Test legacy clients conflict detection."""
    legacy_clients = {
        'clients': {
            'mcp_12345_123': {'pid': 12345, 'timestamp': time.time()}
        }
    }
    assert check_pid_conflict(legacy_clients, 12345, 'api_server') == True
    print("✅ Test 6: Legacy clients conflict detected")


def test_pid_conflict_detection_comprehensive():
    """Run all PID conflict detection edge case tests."""
    print("=== Comprehensive PID Conflict Detection Tests ===")

    test_pid_conflict_empty_data()
    test_pid_conflict_different_pids()
    test_pid_conflict_same_pid_different_type()
    test_pid_conflict_idempotent()
    test_legacy_api_pid_conflicts()
    test_legacy_clients_conflicts()

    print("\n🎉 All PID conflict detection edge case tests passed!")
    # Do not return a value; pytest treats non-None returns as failures in pytest>=8


if __name__ == "__main__":
    test_pid_conflict_detection_comprehensive()
    print("✅ PID conflict edge case testing complete")
