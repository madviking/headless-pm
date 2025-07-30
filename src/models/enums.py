from enum import Enum

class TaskStatus(str, Enum):
    CREATED = "CREATED"
    UNDER_WORK = "UNDER_WORK"
    DEV_DONE = "DEV_DONE"
    TESTING = "TESTING"
    QA_DONE = "QA_DONE"
    DOCUMENTATION_DONE = "DOCUMENTATION_DONE"
    COMMITTED = "COMMITTED"
    # Legacy statuses (deprecated but kept for backward compatibility)
    EVALUATION = "EVALUATION"
    APPROVED = "APPROVED"

class AgentRole(str, Enum):
    FRONTEND_DEV = "frontend_dev"
    BACKEND_DEV = "backend_dev"
    QA = "qa"
    ARCHITECT = "architect"
    PM = "pm"

class DifficultyLevel(str, Enum):
    JUNIOR = "junior"
    SENIOR = "senior"
    PRINCIPAL = "principal"

class TaskComplexity(str, Enum):
    MINOR = "minor"  # Commit directly to main
    MAJOR = "major"  # Requires PR

class ConnectionType(str, Enum):
    MCP = "mcp"      # Model Context Protocol
    CLIENT = "client"  # Direct API client

class TaskType(str, Enum):
    REGULAR = "regular"   # Normal development task
    WAITING = "waiting"   # Synthetic waiting task for polling