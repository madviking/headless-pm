# Headless PM Dashboard Project Plan

## Overview

This document outlines the comprehensive plan for building a read-only dashboard system for the Headless PM project. The dashboard will provide real-time visualization of project status, task progress, agent activity, and communication flows.

## Architecture & Separation of Concerns

### Core Principles
- **Complete separation** between UI and backend concerns
- **Read-only dashboard** - no mutations, only data visualization
- **Separate API layer** for dashboard-specific endpoints
- **Independent deployment** capability

### Folder Structure
```
headless-pm/
├── ui/                           # Frontend React application (main level)
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   │   ├── ui/             # Shadcn/ui components
│   │   │   ├── charts/         # Chart components (recharts)
│   │   │   ├── layout/         # Layout components
│   │   │   └── common/         # Common components
│   │   ├── pages/              # Page components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── lib/                # Utilities & API client
│   │   ├── types/              # TypeScript type definitions
│   │   ├── stores/             # Zustand stores
│   │   └── styles/             # Global styles
│   ├── public/                 # Static assets
│   ├── package.json            # Frontend dependencies
│   ├── vite.config.ts          # Vite configuration
│   ├── tailwind.config.js      # Tailwind configuration
│   └── tsconfig.json           # TypeScript configuration
└── src/
    ├── ui/                     # Dashboard-specific Python backend (inside src)
    │   ├── __init__.py
    │   ├── api/                # Dashboard API routes
    │   │   ├── __init__.py
    │   │   ├── dashboard_routes.py
    │   │   ├── analytics_routes.py
    │   │   └── metrics_routes.py
    │   ├── services/           # Dashboard business logic
    │   │   ├── __init__.py
    │   │   ├── dashboard_service.py
    │   │   ├── analytics_service.py
    │   │   └── metrics_service.py
    │   └── schemas/            # Dashboard-specific schemas
    │       ├── __init__.py
    │       ├── dashboard_schemas.py
    │       └── analytics_schemas.py
    └── [existing main API structure remains unchanged]
```

## Technology Stack

### Frontend
- **React 18** with TypeScript for type safety
- **Vite** for fast development and building
- **Tailwind CSS** for utility-first styling
- **Shadcn/ui** components with **Radix UI** primitives
- **Lucide Icons** for consistent iconography
- **Recharts** for data visualization
- **TanStack Query** for server state management
- **Zustand** for client state management
- **React Router v6** for navigation
- **React Hook Form** + **Zod** for forms and validation

### Backend (Dashboard API)
- **FastAPI** for dashboard-specific endpoints
- **SQLModel** for database queries
- **Pydantic** for response schemas
- Reuse existing database models and connection

### Development Tools
- **OpenAPI TypeScript Codegen** for auto-generated API client
- **Prettier** + **ESLint** for code quality
- **Playwright** for E2E testing

## Dashboard Features & Pages

### 1. Project Overview Dashboard
**Route:** `/`
- **Epic Progress Cards**: Visual progress bars for each epic
- **Task Status Distribution**: Pie chart of task statuses across all projects
- **Active Agents Widget**: List of currently active agents with last seen timestamps
- **Recent Activity Feed**: Latest task status changes and document updates
- **System Health**: Service registry status overview

### 2. Task Management View
**Route:** `/tasks`
- **Task Board**: Kanban-style board with status columns (Created → Under Work → Dev Done → QA Done → Committed)
- **Task Filters**: By role, difficulty level, complexity, epic, feature
- **Task Timeline**: Gantt chart view of task progression
- **Workload Distribution**: Charts showing task distribution across agents and roles

### 3. Agent Activity Monitor
**Route:** `/agents`
- **Agent Status Grid**: Real-time status of all registered agents
- **Activity Heatmap**: Agent activity patterns over time
- **Skill Level Distribution**: Visual breakdown of agent levels per role
- **Connection Type Tracking**: MCP vs Client connection analytics
- **Workload Analytics**: Tasks per agent, completion rates

### 4. Communication Hub
**Route:** `/communications`
- **Document Timeline**: Chronological view of all documents
- **Mention Network**: Visual graph of @mention relationships
- **Communication Patterns**: Charts showing document types and frequencies
- **Notification Status**: Unread mentions overview

### 5. Analytics & Metrics
**Route:** `/analytics`
- **Velocity Metrics**: Task completion rates over time
- **Cycle Time Analysis**: Time spent in each task status
- **Quality Metrics**: Task failure/revision rates
- **Epic Burndown Charts**: Progress tracking for each epic
- **Agent Performance**: Completion rates, task types handled

### 6. System Health Monitor
**Route:** `/health`
- **Service Registry Dashboard**: All registered services with health status
- **Database Metrics**: Connection pools, query performance
- **Error Tracking**: Failed requests, service downtimes
- **Performance Metrics**: Response times, throughput

## Dashboard-Specific API Endpoints

### Analytics Endpoints (`/api/v1/dashboard/`)

```python
# Epic Analytics
GET /api/v1/dashboard/epics/progress
GET /api/v1/dashboard/epics/{epic_id}/metrics

# Task Analytics  
GET /api/v1/dashboard/tasks/distribution
GET /api/v1/dashboard/tasks/timeline
GET /api/v1/dashboard/tasks/velocity

# Agent Analytics
GET /api/v1/dashboard/agents/activity
GET /api/v1/dashboard/agents/workload
GET /api/v1/dashboard/agents/performance

# Communication Analytics
GET /api/v1/dashboard/communications/timeline
GET /api/v1/dashboard/communications/mentions/network
GET /api/v1/dashboard/communications/patterns

# System Health
GET /api/v1/dashboard/health/services
GET /api/v1/dashboard/health/database
GET /api/v1/dashboard/health/performance
```

### Real-time Data Endpoints
```python
# WebSocket or Server-Sent Events for real-time updates
GET /api/v1/dashboard/stream/tasks
GET /api/v1/dashboard/stream/agents
GET /api/v1/dashboard/stream/services
```

## Data Models & Schemas

### Dashboard-Specific Response Models

```python
# Epic Progress Schema
class EpicProgressResponse(BaseModel):
    epic_id: int
    epic_name: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    completion_percentage: float
    estimated_completion: Optional[datetime]

# Task Distribution Schema
class TaskDistributionResponse(BaseModel):
    status: TaskStatus
    count: int
    percentage: float
    by_role: Dict[AgentRole, int]
    by_difficulty: Dict[DifficultyLevel, int]

# Agent Activity Schema
class AgentActivityResponse(BaseModel):
    agent_id: str
    role: AgentRole
    level: DifficultyLevel
    connection_type: ConnectionType
    is_online: bool
    last_seen: datetime
    active_tasks: int
    completed_today: int
    activity_score: float

# Service Health Schema
class ServiceHealthResponse(BaseModel):
    service_name: str
    status: ServiceStatus
    last_ping_success: bool
    response_time_ms: Optional[float]
    uptime_percentage: float
    last_error: Optional[str]
```

## Implementation Phases

### Phase 1: Foundation (Week 1)
- Set up React + TypeScript + Vite project structure
- Configure Tailwind CSS and Shadcn/ui components
- Implement basic routing with React Router
- Set up dashboard API structure in `src/ui/`
- Create basic layout components

### Phase 2: Core Dashboard (Week 2)
- Implement Project Overview dashboard page
- Create basic Epic Progress cards
- Add Task Status Distribution charts
- Implement Active Agents widget
- Set up TanStack Query for API integration

### Phase 3: Task Management (Week 3)
- Build Task Board with Kanban view
- Implement task filtering and search
- Add Task Timeline visualization
- Create Workload Distribution charts

### Phase 4: Agent Monitoring (Week 4)
- Develop Agent Activity Monitor
- Implement Activity Heatmaps
- Add Agent Status Grid
- Create Connection Type tracking

### Phase 5: Communications & Analytics (Week 5)
- Build Communication Hub
- Implement Mention Network visualization
- Add Document Timeline
- Create Analytics dashboard with velocity metrics

### Phase 6: System Health & Real-time (Week 6)
- Develop System Health Monitor
- Implement real-time updates via WebSocket/SSE
- Add performance monitoring
- Polish UI and add responsive design

### Phase 7: Testing & Deployment (Week 7)
- Write comprehensive E2E tests with Playwright
- Performance optimization
- Production build configuration
- Deployment setup

## API Integration Strategy

### Existing API Usage
The dashboard will primarily consume existing APIs:
- `GET /api/v1/epics` - Epic data
- `GET /api/v1/agents` - Agent information  
- `GET /api/v1/changelog` - Recent changes
- `GET /api/v1/documents` - Communication data
- `GET /api/v1/services` - Service registry

### Dashboard-Specific APIs
New endpoints in `src/ui/api/` for:
- Aggregated analytics data
- Performance metrics
- Real-time data streams
- Dashboard-specific data transformations

### Auto-Generated API Client
Use OpenAPI TypeScript Codegen to generate type-safe API client:
```bash
# Generate types from OpenAPI spec
npx openapi-typescript-codegen --input http://localhost:6969/openapi.json --output ./src/lib/api
```

## Real-time Updates

### WebSocket Integration
```typescript
// Real-time task updates
const useTaskUpdates = () => {
  const queryClient = useQueryClient();
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:6969/ws/dashboard/tasks');
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      queryClient.setQueryData(['tasks'], (old) => 
        updateTasksData(old, update)
      );
    };
    
    return () => ws.close();
  }, [queryClient]);
};
```

### Server-Sent Events Alternative
```python
# FastAPI SSE endpoint
@router.get("/dashboard/stream/tasks")
async def stream_task_updates():
    async def event_generator():
        while True:
            # Check for task updates
            yield f"data: {json.dumps(task_update)}\n\n"
            await asyncio.sleep(1)
    
    return StreamingResponse(event_generator(), media_type="text/plain")
```

## State Management Strategy

### Server State (TanStack Query)
```typescript
// Epic progress query
export const useEpicProgress = () => {
  return useQuery({
    queryKey: ['epics', 'progress'],
    queryFn: () => dashboardApi.getEpicProgress(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

// Task distribution query  
export const useTaskDistribution = (filters?: TaskFilters) => {
  return useQuery({
    queryKey: ['tasks', 'distribution', filters],
    queryFn: () => dashboardApi.getTaskDistribution(filters),
    staleTime: 60000, // Consider fresh for 1 minute
  });
};
```

### Client State (Zustand)
```typescript
// Dashboard settings store
interface DashboardStore {
  autoRefresh: boolean;
  refreshInterval: number;
  selectedEpic: number | null;
  dateRange: DateRange;
  setAutoRefresh: (enabled: boolean) => void;
  setRefreshInterval: (interval: number) => void;
}

export const useDashboardStore = create<DashboardStore>((set) => ({
  autoRefresh: true,
  refreshInterval: 30000,
  selectedEpic: null,
  dateRange: { start: subDays(new Date(), 30), end: new Date() },
  // ... setters
}));
```

## Security Considerations

### Authentication
- Reuse existing API key authentication
- Add dashboard-specific permissions if needed
- Read-only access patterns

### Data Privacy
- No sensitive data exposure
- Audit logs for dashboard access
- Rate limiting for API endpoints

## Performance Optimization

### Frontend Optimization
- **Code Splitting**: Route-based lazy loading
- **Virtual Scrolling**: For large task lists
- **Memoization**: React.memo for expensive components
- **Bundle Analysis**: Vite bundle analyzer

### Backend Optimization
- **Query Optimization**: Efficient database queries for analytics
- **Caching**: Redis caching for aggregated data
- **Connection Pooling**: Optimized database connections
- **Response Compression**: Gzip compression for API responses

## Testing Strategy

### Frontend Testing
```typescript
// Component testing with React Testing Library
describe('EpicProgressCard', () => {
  it('displays progress correctly', () => {
    render(<EpicProgressCard epic={mockEpic} />);
    expect(screen.getByText('75% Complete')).toBeInTheDocument();
  });
});

// E2E testing with Playwright
test('dashboard loads and displays data', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('[data-testid="epic-progress"]')).toBeVisible();
  await expect(page.locator('[data-testid="task-distribution"]')).toBeVisible();
});
```

### Backend Testing
```python
# Dashboard API testing
def test_epic_progress_endpoint():
    response = client.get("/api/v1/dashboard/epics/progress")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all('completion_percentage' in epic for epic in data)
```

## Deployment & DevOps

### Development Environment
```bash
# Start backend
cd headless-pm
source venv/bin/activate
uvicorn src.main:app --reload --port 6969

# Start frontend (separate terminal)
cd ui
npm run dev
```

### Production Build
```bash
# Build frontend
cd ui
npm run build

# Serve static files from FastAPI
# Add static file serving to main FastAPI app
```

### Docker Configuration
```dockerfile
# Multi-stage build for production
FROM node:18-alpine as ui-builder
WORKDIR /app/ui
COPY ui/package*.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY src/ ./src/
COPY --from=ui-builder /app/ui/dist ./static
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "6969"]
```

## Success Metrics

### Technical Metrics
- **Page Load Time**: < 2 seconds initial load
- **Time to Interactive**: < 3 seconds
- **Bundle Size**: < 500KB initial JavaScript
- **API Response Time**: < 200ms for dashboard endpoints

### User Experience Metrics
- **Real-time Update Latency**: < 5 seconds
- **Data Refresh Rate**: 30-second intervals
- **Mobile Responsiveness**: Full functionality on tablet/mobile
- **Accessibility**: WCAG 2.1 AA compliance

### Business Metrics
- **Data Accuracy**: 100% consistency with source APIs
- **Uptime**: 99.9% dashboard availability
- **Coverage**: All existing API data represented
- **Performance**: No impact on main API performance

## Risks & Mitigation

### Technical Risks
1. **Performance Impact**: Dashboard queries affecting main API
   - *Mitigation*: Separate read-only database connections, query optimization
2. **Real-time Complexity**: WebSocket connection management
   - *Mitigation*: Fallback to polling, connection retry logic
3. **Data Consistency**: Dashboard showing stale data
   - *Mitigation*: Proper cache invalidation, shorter refresh intervals

### Project Risks
1. **Scope Creep**: Adding write operations to dashboard
   - *Mitigation*: Strict read-only enforcement, clear requirements
2. **Resource Allocation**: Frontend/backend development overlap
   - *Mitigation*: Clear phase separation, API-first development

## Conclusion

This dashboard project will provide comprehensive visibility into the Headless PM system while maintaining strict separation of concerns. The phased approach ensures manageable development cycles, while the modern tech stack provides excellent developer experience and user performance.

The read-only nature keeps the dashboard focused and prevents feature creep, while the separate API layer ensures the main system remains unaffected. Real-time updates and rich visualizations will make this dashboard an essential tool for project monitoring and management.