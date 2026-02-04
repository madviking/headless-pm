from fastapi import APIRouter
import os

from src.api.schemas import ProjectContextResponse

# Public router: endpoints here do NOT require API key
public_router = APIRouter(prefix="/api/v1", tags=["Public"])


@public_router.get(
    "/context",
    response_model=ProjectContextResponse,
    summary="Get project context",
    description="Get project configuration and paths for documentation (no authentication required)",
)
def get_public_context():
    return ProjectContextResponse(
        project_name=os.getenv("PROJECT_NAME", "Headless PM"),
        shared_path=os.getenv("SHARED_PATH", "./shared"),
        instructions_path=os.getenv("INSTRUCTIONS_PATH", "./agent_instructions"),
        project_docs_path=os.getenv("PROJECT_DOCS_PATH", "./docs"),
        database_type="sqlite" if os.getenv("DATABASE_URL", "").startswith("sqlite") else "mysql",
    )

