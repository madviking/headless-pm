# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

```bash
# Setup virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r setup/requirements.txt

# Configure environment
cp env-example .env
# Edit .env with API keys and database configuration

# Initialize database
python -m src.cli.main init
python -m src.cli.main seed  # Optional: add sample data
```

### Running the Application

#### Quick Start (Recommended)
```bash
# Activate your virtual environment first
source venv/bin/activate  # or source claude_venv/bin/activate

# Use the automated start script (checks environment, DB, starts server)
./start.sh
```

#### Manual Start
```bash
# Run API server
bash start.sh
```

The `start.sh` script automatically:
- ✅ Validates Python 3.11+ requirement  
- ✅ Checks required packages are installed
- ✅ Creates .env from env-example if needed
- ✅ Tests database connection
- ✅ Initializes database if needed
- ✅ Checks port availability
- ✅ Starts server with proper configuration

**Note**: Activate your virtual environment before running the start script.

## Testing

### Running Tests
```bash
# IMPORTANT: Always use Claude virtual environment for testing
source claude_venv/bin/activate

# Run all tests with coverage
python -m pytest --cov=src --cov-report=term-missing

# Run specific test files
python -m pytest tests/test_api.py -v
python -m pytest tests/test_models.py -v

# Run tests without coverage (faster)
python -m pytest -q

# Run specific test patterns
python -m pytest -k "test_name_pattern"
```

### Test Coverage Status
- **Current Tests**: Client integration tests
- **Test Location**: `tests/test_headless_pm_client.py`
- **Additional Testing**: Comprehensive test suite planned

### Test Architecture Notes
- API tests use temporary file-based SQLite databases (not in-memory) to avoid connection issues
- All models, enums, and services have comprehensive test coverage
- Tests include document creation, mention detection, service registry, and task lifecycle

## Architecture Overview

Headless PM is a REST API for LLM agent task coordination with document-based communication. Key architectural decisions:

1. **Document-Based Communication**: Agents communicate via documents with @mention support
2. **Service Registry**: Track running services with heartbeat monitoring
3. **Git Workflow Integration**: Major tasks use feature branches with PRs, minor tasks commit directly to main
4. **Changes Polling**: Efficient polling endpoint for agents to get updates since last check
5. **Role-Based System**: Five roles (frontend_dev, backend_dev, qa, architect, pm) with multiple agents per role
6. **Task Complexity**: Major/minor classification determines Git workflow (PR vs direct commit)
7. **Comprehensive Testing**: 78 tests with 71% coverage including full API testing

### Enhanced Features
- **Epic/Feature/Task Hierarchy**: Three-level project organization
- **Documents Table**: Agent communication with mention detection
- **Service Registry**: Track microservices with heartbeat monitoring and ping URLs
- **Mentions System**: @username notifications across documents and tasks
- **Changes API**: Polling endpoint returning changes since timestamp
- **Task Complexity**: Major/minor enum driving branching strategies
- **Connection Types**: Distinguish between MCP and client connections
- **Task Comments**: Collaborative discussion on tasks with @mentions
- **Python Client Helper**: Complete CLI interface (`headless_pm_client.py`)
- **MCP Server**: Natural language interface for Claude Code
- **Database Migrations**: Schema evolution support

## Project Structure

```
headless-pm/
├── src/                    # Source code
│   ├── api/               # FastAPI routes
│   ├── models/            # SQLModel database models
│   ├── services/          # Business logic
│   ├── cli/               # CLI commands
│   ├── mcp/               # MCP server implementation
│   └── main.py            # FastAPI app entry point
├── tests/                 # Test files
├── migrations/            # Database migration scripts
├── agent_instructions/    # Per-role markdown instructions
├── agents/                # Agent tools and installers
│   └── claude/            # Claude Code specific tools
├── setup/                 # Installation and setup scripts
├── docs/                  # Project documentation
└── headless_pm_client.py  # Python CLI client
```

## Key API Endpoints

### Core Task Management
- `POST /api/v1/register` - Register agent with role/skill level and connection type
- `GET /api/v1/context` - Get project context and paths
- `DELETE /api/v1/agents/{agent_id}` - Delete agent (PM only)

### Epic/Feature/Task Endpoints
- `POST /api/v1/epics` - Create epic (PM/Architect only)
- `GET /api/v1/epics` - List epics with progress tracking
- `DELETE /api/v1/epics/{id}` - Delete epic (PM only)
- `POST /api/v1/features` - Create feature under epic
- `GET /api/v1/features/{epic_id}` - List features for epic
- `DELETE /api/v1/features/{id}` - Delete feature
- `POST /api/v1/tasks/create` - Create new task with complexity (major/minor)
- `GET /api/v1/tasks/next` - Get next available task for role
- `POST /api/v1/tasks/{id}/lock` - Lock task to prevent duplicate work
- `PUT /api/v1/tasks/{id}/status` - Update task status
- `POST /api/v1/tasks/{id}/comment` - Add comment with @mention support

### Document Communication
- `POST /api/v1/documents` - Create document with auto @mention detection
- `GET /api/v1/documents` - List documents with filtering
- `GET /api/v1/mentions` - Get mentions for an agent

### Service Registry
- `POST /api/v1/services/register` - Register a service with optional ping URL
- `GET /api/v1/services` - List all services with health status
- `POST /api/v1/services/{name}/heartbeat` - Send service heartbeat
- `DELETE /api/v1/services/{name}` - Unregister service

### Changes & Updates
- `GET /api/v1/changes` - Poll for changes since timestamp
- `GET /api/v1/changelog` - Get recent task status changes

## Technology Stack

- **FastAPI** - REST API framework
- **SQLModel** - ORM combining SQLAlchemy + Pydantic
- **Pydantic** - Data validation
- **SQLite/MySQL** - Database options
- **Python 3.11+** - Runtime requirement

## Development Notes

### Implementation Status
- ✅ **Fully Implemented**: Complete REST API with all endpoints
- ✅ **Database Models**: SQLModel with proper relationships
- ✅ **CLI Interface**: Full command-line management tools
- ✅ **Testing**: 78 tests with 71% coverage
- ✅ **Documentation**: Agent instructions and workflow guides

### Key Implementation Details
- **Task Organization**: Epic → Feature → Task hierarchy
- **Task Difficulty Levels**: junior, senior, principal
- **Task Complexity**: major (requires PR), minor (direct commit)
- **Agent Communication**: Via documents with @mention detection
- **Agent Types**: Client connections and MCP connections
- **Service Monitoring**: Heartbeat-based health tracking with optional ping URLs
- **Change Detection**: Efficient polling since timestamp
- **Git Integration**: Automated workflow based on task complexity
- **Database**: SQLModel for type safety, supports SQLite and MySQL
- **API Validation**: Pydantic models for all request/response data
- **MCP Transport**: Multiple protocols (HTTP, SSE, WebSocket, STDIO)
- **Token Tracking**: Usage statistics for MCP sessions

### Testing Environment
- Use `claude_venv` for all testing to ensure compatibility
- API tests use temporary file-based SQLite databases
- Run `python -m pytest tests/` for running tests
- Client integration tests implemented in `test_headless_pm_client.py`

## Python Client Helper

The `headless_pm_client.py` provides a complete CLI interface to the API:

### Basic Usage
```bash
# Register an agent
./headless_pm_client.py register --agent-id "dev_001" --role "backend_dev" --level "senior"

# Work with epics/features/tasks
./headless_pm_client.py epics create --name "Authentication" --description "User auth system"
./headless_pm_client.py tasks next --role backend_dev --level senior
./headless_pm_client.py tasks lock 123 --agent-id "dev_001"
./headless_pm_client.py tasks status 123 --status "dev_done" --agent-id "dev_001"

# Communicate with team
./headless_pm_client.py documents create --type "update" --title "Progress" \
  --content "Completed login API @qa_001 please test" --author-id "dev_001"
  
# Check for updates
./headless_pm_client.py mentions --agent-id "dev_001"
./headless_pm_client.py changes --since 1736359200 --agent-id "dev_001"
```

### Client Features
- Automatic `.env` file loading for API keys
- Comprehensive help with `--help` flag
- Support for all API endpoints
- Embedded agent instructions
- Multiple API key sources (checks in priority order)

## Connection Types

Agents can register with two connection types:

### CLIENT Connection
- Default for agents using the API directly
- Use when registering via `headless_pm_client.py` or direct API calls
- Example: `./headless_pm_client.py register --agent-id "dev_001" --role "backend_dev"`

### MCP Connection  
- Automatically set when using MCP server
- Used by Claude Code integration
- Provides natural language interface
- Token usage tracking included

The connection type helps distinguish between different agent interfaces and enables appropriate features for each type.

### Memories
- 8000 port is for another service entirely, leave that alone!
