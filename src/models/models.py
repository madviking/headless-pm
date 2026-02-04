from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from sqlalchemy import Text
from typing import Optional, List, Dict, Any
from datetime import datetime
from .enums import TaskStatus, AgentRole, DifficultyLevel, TaskComplexity, ConnectionType
from .document_enums import DocumentType, ServiceStatus
from .sa_types import EnumValueString

class Agent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str = Field(index=True, unique=True)  # e.g., "frontend_dev_senior_001"
    role: AgentRole
    level: DifficultyLevel
    connection_type: Optional[ConnectionType] = Field(default=ConnectionType.CLIENT)  # MCP or Client
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    
    tasks_created: List["Task"] = Relationship(back_populates="creator", sa_relationship_kwargs={"foreign_keys": "[Task.created_by_id]"})
    tasks_locked: List["Task"] = Relationship(back_populates="locked_by_agent", sa_relationship_kwargs={"foreign_keys": "[Task.locked_by_id]"})

class Epic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    features: List["Feature"] = Relationship(back_populates="epic", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Feature(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    epic_id: int = Field(foreign_key="epic.id")
    name: str
    description: str = Field(sa_column=Column(Text))
    
    epic: Epic = Relationship(back_populates="features")
    tasks: List["Task"] = Relationship(back_populates="feature", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    feature_id: int = Field(foreign_key="feature.id")
    title: str
    description: str = Field(sa_column=Column(Text))
    created_by_id: int = Field(foreign_key="agent.id")
    target_role: AgentRole
    difficulty: DifficultyLevel
    complexity: TaskComplexity = Field(default=TaskComplexity.MAJOR)
    branch: str
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        sa_column=Column(EnumValueString(TaskStatus, length=32)),
    )
    locked_by_id: Optional[int] = Field(default=None, foreign_key="agent.id")
    locked_at: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    feature: Feature = Relationship(back_populates="tasks")
    creator: Agent = Relationship(back_populates="tasks_created", sa_relationship_kwargs={"foreign_keys": "[Task.created_by_id]"})
    locked_by_agent: Optional[Agent] = Relationship(back_populates="tasks_locked", sa_relationship_kwargs={"foreign_keys": "[Task.locked_by_id]"})
    evaluations: List["TaskEvaluation"] = Relationship(back_populates="task", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    changelogs: List["Changelog"] = Relationship(back_populates="task", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    mentions: List["Mention"] = Relationship(back_populates="task", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class TaskEvaluation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    evaluated_by: str  # agent_id
    approved: bool
    comment: Optional[str] = Field(default=None, sa_column=Column(Text))
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    
    task: Task = Relationship(back_populates="evaluations")

class Changelog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    old_status: TaskStatus = Field(sa_column=Column(EnumValueString(TaskStatus, length=32)))
    new_status: TaskStatus = Field(sa_column=Column(EnumValueString(TaskStatus, length=32)))
    changed_by: str  # agent_id
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    
    task: Task = Relationship(back_populates="changelogs")

class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    doc_type: DocumentType = Field(index=True)
    author_id: str = Field(index=True)  # agent_id
    title: str = Field(max_length=200)
    content: str = Field(sa_column=Column(Text))  # Markdown supported
    meta_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # For auto-cleanup
    
    mentions: List["Mention"] = Relationship(back_populates="document", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Service(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    service_name: str = Field(unique=True, index=True, max_length=100)
    owner_agent_id: str  # agent_id
    ping_url: str  # URL to ping for health check
    port: Optional[int] = None
    status: ServiceStatus = Field(default=ServiceStatus.DOWN)
    last_heartbeat: Optional[datetime] = None
    last_ping_at: Optional[datetime] = None
    last_ping_success: Optional[bool] = None
    meta_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Mention(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: Optional[int] = Field(default=None, foreign_key="document.id")
    task_id: Optional[int] = Field(default=None, foreign_key="task.id")
    mentioned_agent_id: str = Field(index=True)  # agent_id
    created_by: str  # agent_id
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    document: Optional[Document] = Relationship(back_populates="mentions")
    task: Optional[Task] = Relationship(back_populates="mentions")
