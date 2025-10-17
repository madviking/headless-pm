#!/usr/bin/env python3
"""
Headless PM CLI - Command-line interface for project management
"""

import typer
from typing import Optional
from sqlmodel import Session, select
from tabulate import tabulate
from datetime import datetime
import os

from src.models.database import get_session, create_db_and_tables
from src.models.models import Agent, Epic, Feature, Task, Service, Document
from src.models.enums import TaskStatus, AgentRole, DifficultyLevel
from src.models.document_enums import DocumentType, ServiceStatus

app = typer.Typer(help="Headless PM - Project Management for LLM Agents")

def get_db() -> Session:
    """Get database session"""
    return next(get_session())

@app.command()
def status():
    """Show project status overview"""
    db = get_db()
    
    # Count tasks by status
    task_counts = {}
    for status in TaskStatus:
        count = len(db.exec(select(Task).where(Task.status == status)).all())
        task_counts[status.value] = count
    
    # Count active agents
    agent_count = len(db.exec(select(Agent)).all())
    
    # Count active services
    active_services = len(db.exec(
        select(Service).where(Service.status == ServiceStatus.UP)
    ).all())
    
    # Recent documents
    recent_docs = len(db.exec(
        select(Document).where(
            Document.created_at > datetime.now().replace(hour=0, minute=0, second=0)
        )
    ).all())
    
    typer.echo("🚀 Headless PM Status")
    typer.echo("=" * 50)
    typer.echo(f"Registered Agents: {agent_count}")
    typer.echo(f"Active Services: {active_services}")
    typer.echo(f"Documents Today: {recent_docs}")
    typer.echo("\nTask Breakdown:")
    
    for status, count in task_counts.items():
        typer.echo(f"  {status.replace('_', ' ').title()}: {count}")

@app.command()
def tasks(
    status: Optional[str] = typer.Option(None, help="Filter by task status"),
    role: Optional[str] = typer.Option(None, help="Filter by target role")
):
    """Show task assignments"""
    db = get_db()
    
    query = select(Task).order_by(Task.created_at.desc())
    
    if status:
        try:
            task_status = TaskStatus(status)
            query = query.where(Task.status == task_status)
        except ValueError:
            typer.echo(f"Invalid status: {status}")
            return
    
    if role:
        try:
            agent_role = AgentRole(role)
            query = query.where(Task.target_role == agent_role)
        except ValueError:
            typer.echo(f"Invalid role: {role}")
            return
    
    tasks = db.exec(query.limit(20)).all()
    
    if not tasks:
        typer.echo("No tasks found matching criteria")
        return
    
    # Prepare table data
    table_data = []
    for task in tasks:
        table_data.append([
            task.id,
            task.title[:30] + "..." if len(task.title) > 30 else task.title,
            task.target_role.value,
            task.difficulty.value,
            task.status.value.replace('_', ' '),
            task.creator.agent_id if task.creator else "unknown",
            task.locked_by_agent.agent_id if task.locked_by_agent else "-"
        ])
    
    headers = ["ID", "Title", "Role", "Level", "Status", "Creator", "Locked By"]
    typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

@app.command()
def reset():
    """Reset database (WARNING: Deletes all data)"""
    confirm = typer.confirm("This will delete ALL data. Are you sure?")
    if not confirm:
        typer.echo("Operation cancelled")
        return
    
    db = get_db()
    
    # Drop and recreate tables
    from src.models.database import engine
    from sqlmodel import SQLModel
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    
    typer.echo("✅ Database reset successfully")

@app.command()
def agents():
    """List registered agents"""
    db = get_db()
    
    agents = db.exec(select(Agent).order_by(Agent.last_seen.desc())).all()
    
    if not agents:
        typer.echo("No agents registered")
        return
    
    table_data = []
    for agent in agents:
        last_seen = agent.last_seen.strftime("%Y-%m-%d %H:%M") if agent.last_seen else "Never"
        table_data.append([
            agent.agent_id,
            agent.role.value,
            agent.level.value,
            last_seen
        ])
    
    headers = ["Agent ID", "Role", "Level", "Last Seen"]
    typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

@app.command()
def services():
    """List registered services"""
    db = get_db()
    
    services = db.exec(select(Service).order_by(Service.service_name)).all()
    
    if not services:
        typer.echo("No services registered")
        return
    
    table_data = []
    for service in services:
        port_str = str(service.port) if service.port else "-"
        last_heartbeat = service.last_heartbeat.strftime("%H:%M:%S") if service.last_heartbeat else "Never"
        
        table_data.append([
            service.service_name,
            service.owner_agent_id,
            port_str,
            service.status.value,
            last_heartbeat
        ])
    
    headers = ["Service", "Owner", "Port", "Status", "Last Heartbeat"]
    typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

@app.command()
def documents(
    doc_type: Optional[str] = typer.Option(None, help="Filter by document type")
):
    """List recent documents"""
    db = get_db()
    
    query = select(Document).order_by(Document.created_at.desc())
    
    if doc_type:
        try:
            document_type = DocumentType(doc_type)
            query = query.where(Document.doc_type == document_type)
        except ValueError:
            typer.echo(f"Invalid document type: {doc_type}")
            return
    
    docs = db.exec(query.limit(20)).all()
    
    if not docs:
        typer.echo("No documents found")
        return
    
    table_data = []
    for doc in docs:
        created = doc.created_at.strftime("%m-%d %H:%M")
        title = doc.title[:40] + "..." if len(doc.title) > 40 else doc.title
        
        table_data.append([
            doc.id,
            doc.doc_type.value,
            title,
            doc.author_id,
            created
        ])
    
    headers = ["ID", "Type", "Title", "Author", "Created"]
    typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

@app.command()
def seed():
    """Create sample data for testing"""
    db = get_db()
    
    typer.echo("Creating sample data...")
    
    # Create sample epic and feature
    epic = Epic(
        name="User Authentication",
        description="Implement complete user authentication system"
    )
    db.add(epic)
    db.commit()
    db.refresh(epic)
    
    feature = Feature(
        epic_id=epic.id,
        name="Login System",
        description="User login with JWT authentication"
    )
    db.add(feature)
    db.commit()
    db.refresh(feature)
    
    # Create sample agents
    agents = [
        Agent(
            agent_id="architect_principal_001",
            role=AgentRole.ARCHITECT,
            level=DifficultyLevel.PRINCIPAL
        ),
        Agent(
            agent_id="frontend_dev_senior_001",
            role=AgentRole.FRONTEND_DEV,
            level=DifficultyLevel.SENIOR
        ),
        Agent(
            agent_id="backend_dev_senior_001",
            role=AgentRole.BACKEND_DEV,
            level=DifficultyLevel.SENIOR
        ),
        Agent(
            agent_id="qa_senior_001",
            role=AgentRole.QA,
            level=DifficultyLevel.SENIOR
        )
    ]
    
    for agent in agents:
        db.add(agent)
    db.commit()
    
    # Create sample tasks
    architect = agents[0]
    
    tasks = [
        Task(
            feature_id=feature.id,
            title="Design login UI mockups",
            description="Create wireframes and mockups for login interface",
            created_by_id=architect.id,
            target_role=AgentRole.FRONTEND_DEV,
            difficulty=DifficultyLevel.SENIOR,
            branch="feature/login-ui"
        ),
        Task(
            feature_id=feature.id,
            title="Implement JWT authentication API",
            description="Create login/logout endpoints with JWT tokens",
            created_by_id=architect.id,
            target_role=AgentRole.BACKEND_DEV,
            difficulty=DifficultyLevel.SENIOR,
            branch="feature/jwt-auth"
        ),
        Task(
            feature_id=feature.id,
            title="Write authentication tests",
            description="Create comprehensive test suite for auth system",
            created_by_id=architect.id,
            target_role=AgentRole.QA,
            difficulty=DifficultyLevel.SENIOR,
            branch="feature/auth-tests"
        )
    ]
    
    for task in tasks:
        db.add(task)
    db.commit()
    
    # Create sample documents
    docs = [
        Document(
            doc_type=DocumentType.STANDUP,
            author_id="architect_principal_001",
            title="Daily Standup - Architecture",
            content="## Yesterday\n- Reviewed authentication requirements\n- Created initial task breakdown\n\n## Today\n- Finalizing API design\n- Creating detailed tasks\n\n## Blockers\n- None"
        ),
        Document(
            doc_type=DocumentType.CRITICAL_ISSUE,
            author_id="qa_senior_001",
            title="Test Environment Down",
            content="The test environment is currently down. @backend_dev_senior_001 please investigate."
        )
    ]
    
    for doc in docs:
        db.add(doc)
    db.commit()
    
    typer.echo("✅ Sample data created successfully!")
    typer.echo(f"Created: 1 epic, 1 feature, {len(tasks)} tasks, {len(agents)} agents, {len(docs)} documents")

@app.command()
def init():
    """Initialize database and create tables"""
    create_db_and_tables()
    typer.echo("✅ Database initialized successfully")

@app.command()
def dashboard():
    """Launch real-time dashboard"""
    from src.cli.dashboard import HeadlessPMDashboard
    dashboard = HeadlessPMDashboard()
    dashboard.run()

def main():
    """Main entry point for headless-pm-cli command"""
    app()

if __name__ == "__main__":
    main()

