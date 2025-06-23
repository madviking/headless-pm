'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useApi } from '@/lib/hooks/useApi';
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { useDroppable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, User, Clock, GitBranch, Flag, Calendar } from 'lucide-react';
import { Task, TaskStatus, AgentRole, TaskDifficulty, TaskComplexity } from '@/lib/types';
import { format } from 'date-fns';
import { TaskFilters } from './task-filters';
import { HeadlessPMClient } from '@/lib/api/client';

const TASK_STATUSES = [
  { key: TaskStatus.Created, label: 'CREATED', color: 'bg-slate-100 text-slate-700' },
  { key: TaskStatus.UnderWork, label: 'UNDER WORK', color: 'bg-blue-100 text-blue-700' },
  { key: TaskStatus.DevDone, label: 'DEV DONE', color: 'bg-green-100 text-green-700' },
  { key: TaskStatus.QADone, label: 'QA DONE', color: 'bg-purple-100 text-purple-700' },
  { key: TaskStatus.DocumentationDone, label: 'DOCS DONE', color: 'bg-orange-100 text-orange-700' },
  { key: TaskStatus.Committed, label: 'COMMITTED', color: 'bg-emerald-100 text-emerald-700' }
];

const ROLE_COLORS = {
  [AgentRole.FrontendDev]: 'bg-blue-500 text-white',
  [AgentRole.BackendDev]: 'bg-green-500 text-white',
  [AgentRole.QA]: 'bg-purple-500 text-white',
  [AgentRole.Architect]: 'bg-orange-500 text-white',
  [AgentRole.PM]: 'bg-red-500 text-white'
};

const DIFFICULTY_COLORS = {
  [TaskDifficulty.Junior]: 'bg-green-500 text-white',
  [TaskDifficulty.Senior]: 'bg-yellow-500 text-white',
  [TaskDifficulty.Principal]: 'bg-red-500 text-white'
};

const COMPLEXITY_COLORS = {
  [TaskComplexity.Minor]: 'bg-blue-500 text-white',
  [TaskComplexity.Major]: 'bg-orange-500 text-white'
};

function DraggableTaskCard({ task, onStatusChange }: { task: Task; onStatusChange?: (task: Task, newStatus: TaskStatus) => void }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: task.id.toString(),
    data: {
      type: 'task',
      task,
    },
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  if (isDragging) {
    return (
      <div
        ref={setNodeRef}
        style={style}
        className="mb-3 opacity-50"
      >
        <Card className="border-dashed border-2">
          <CardContent className="p-4 h-32" />
        </Card>
      </div>
    );
  }

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <TaskCard task={task} onStatusChange={onStatusChange} />
    </div>
  );
}

function TaskCard({ task, onStatusChange }: { task: Task; onStatusChange?: (task: Task, newStatus: TaskStatus) => void }) {
  const getTaskIcon = (title: string) => {
    const lower = title.toLowerCase();
    if (lower.includes('navigation') || lower.includes('ui')) return '🎨';
    if (lower.includes('login') || lower.includes('auth')) return '🔐';
    if (lower.includes('profile') || lower.includes('user')) return '👤';
    if (lower.includes('payment') || lower.includes('webhook')) return '💳';
    if (lower.includes('shopping') || lower.includes('cart')) return '🛒';
    if (lower.includes('database') || lower.includes('migration')) return '🗄️';
    if (lower.includes('search') || lower.includes('filter')) return '🔍';
    if (lower.includes('analytics') || lower.includes('dashboard')) return '📊';
    if (lower.includes('email') || lower.includes('template')) return '📧';
    if (lower.includes('error') || lower.includes('handling')) return '🔧';
    if (lower.includes('mobile') || lower.includes('responsive')) return '📱';
    if (lower.includes('test') || lower.includes('unit')) return '🧪';
    if (lower.includes('homepage') || lower.includes('home')) return '🏠';
    return '📋';
  };

  return (
    <Card className="mb-2 cursor-pointer hover:shadow-md transition-shadow">
      <CardContent className="p-3">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg">{getTaskIcon(task.title)}</span>
              <span className="text-sm font-medium text-muted-foreground">#{task.id}</span>
            </div>
            {task.status === TaskStatus.Committed && (
              <Badge variant="secondary" className="text-xs">
                ✅ Deployed
              </Badge>
            )}
          </div>
          
          <div>
            <h4 className="font-medium text-sm leading-tight">{task.title}</h4>
            {task.description && (
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                {task.description}
              </p>
            )}
          </div>

          <div className="space-y-2">
            {task.target_role && (
              <div className="flex items-center gap-2">
                <User className="h-3 w-3" />
                <Badge variant="outline" className={`text-xs ${ROLE_COLORS[task.target_role]}`}>
                  {task.target_role.replace('_', ' ')}
                </Badge>
              </div>
            )}

            <div className="flex items-center gap-2">
              <Flag className="h-3 w-3" />
              <Badge variant="outline" className={`text-xs ${DIFFICULTY_COLORS[task.difficulty]}`}>
                {task.difficulty.toUpperCase()}
              </Badge>
            </div>

            <div className="flex items-center gap-2">
              <GitBranch className="h-3 w-3" />
              <Badge variant="outline" className={`text-xs ${COMPLEXITY_COLORS[task.complexity]}`}>
                {task.complexity.toUpperCase()}
              </Badge>
            </div>

            {task.updated_at && (
              <div className="flex items-center gap-2">
                <Calendar className="h-3 w-3" />
                <span className="text-xs text-muted-foreground">
                  {format(new Date(task.updated_at), 'MMM dd')}
                </span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function TaskColumn({ 
  status, 
  label, 
  color, 
  tasks, 
  onStatusChange 
}: { 
  status: TaskStatus; 
  label: string; 
  color: string; 
  tasks: Task[]; 
  onStatusChange?: (task: Task, newStatus: TaskStatus) => void;
}) {
  const tasksInStatus = tasks.filter(task => task.status === status);
  
  const { isOver, setNodeRef } = useDroppable({
    id: `column-${status}`,
    data: {
      type: 'column',
      status,
    },
  });

  return (
    <div className="flex-1 min-w-[300px]" ref={setNodeRef}>
      <Card className={`h-full transition-all ${
        isOver ? 'ring-2 ring-blue-400 bg-blue-50/20' : ''
      }`}>
        <CardHeader className="pb-2 px-3">
          <CardTitle className="flex items-center justify-between">
            <span className={`text-sm font-medium px-2 py-1 rounded-md ${color}`}>
              {label} ({tasksInStatus.length})
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0 px-2">
          <SortableContext 
            items={tasksInStatus.map(t => t.id.toString())} 
            strategy={verticalListSortingStrategy}
          >
            <div className="space-y-2 min-h-[500px] p-1 rounded-lg">
              {tasksInStatus.map(task => (
                <DraggableTaskCard 
                  key={task.id} 
                  task={task} 
                  onStatusChange={onStatusChange}
                />
              ))}
              
              {/* Empty space to ensure droppable area */}
              {tasksInStatus.length === 0 && (
                <div className="h-20 flex items-center justify-center text-muted-foreground text-sm">
                  Drop tasks here
                </div>
              )}
              
            </div>
          </SortableContext>
        </CardContent>
      </Card>
    </div>
  );
}

export function TaskBoard({ filters = {} }: { filters?: TaskFilters }) {
  const { data: tasks = [], isLoading, error, mutate } = useApi(
    'tasks',
    (client) => client.getTasks(),
    {
      refreshInterval: 5000, // Refresh every 5 seconds
      revalidateOnFocus: true,
      revalidateOnReconnect: true
    }
  );

  const { data: agents = [] } = useApi(
    'agents',
    (client) => client.getAgents(),
    {
      refreshInterval: 30000 // Refresh agents every 30 seconds
    }
  );

  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [localTasks, setLocalTasks] = useState<Task[]>(() => tasks || []);
  const [lastTasksUpdate, setLastTasksUpdate] = useState<string>('');
  const [selectedAgentId, setSelectedAgentId] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      const storedAgentId = localStorage.getItem('agent_id') || '';
      // Clear invalid agent IDs that might have extra characters
      if (storedAgentId && storedAgentId.includes(':')) {
        localStorage.removeItem('agent_id');
        return '';
      }
      return storedAgentId;
    }
    return '';
  });

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  // Save selected agent ID to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined' && selectedAgentId) {
      localStorage.setItem('agent_id', selectedAgentId);
    }
  }, [selectedAgentId]);

  // Only update localTasks when tasks actually change to prevent infinite loops
  useEffect(() => {
    if (tasks && tasks.length >= 0) {
      const tasksString = JSON.stringify(tasks);
      if (tasksString !== lastTasksUpdate) {
        setLocalTasks(tasks);
        setLastTasksUpdate(tasksString);
      }
    }
  }, [tasks, lastTasksUpdate]);

  // Apply filters to tasks with memoization to prevent unnecessary recalculations
  const filteredTasks = useMemo(() => {
    return localTasks.filter(task => {
      if (filters.role && task.target_role !== filters.role) return false;
      if (filters.difficulty && task.difficulty !== filters.difficulty) return false;
      if (filters.status && task.status !== filters.status) return false;
      if (filters.complexity && task.complexity !== filters.complexity) return false;
      if (filters.assignee && task.locked_by !== filters.assignee) return false;
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        const titleMatch = task.title.toLowerCase().includes(searchLower);
        const descMatch = task.description?.toLowerCase().includes(searchLower);
        if (!titleMatch && !descMatch) return false;
      }
      return true;
    });
  }, [localTasks, filters]);

  const handleStatusChange = useCallback(async (task: Task, newStatus: TaskStatus) => {
    // Validate status before proceeding
    if (typeof newStatus !== 'string') {
      console.error('Invalid status type:', typeof newStatus, 'Value:', newStatus);
      throw new Error('Status must be a string');
    }
    
    const validStatuses = Object.values(TaskStatus) as string[];
    if (!validStatuses.includes(newStatus)) {
      console.error('Invalid status value:', newStatus, 'Expected one of:', validStatuses);
      throw new Error(`Invalid status: ${newStatus}`);
    }
    
    // Get agent ID from state or localStorage
    let agentId = selectedAgentId || (typeof window !== 'undefined' ? localStorage.getItem('agent_id') : '');
    
    // Clear invalid agent IDs that contain colons
    if (typeof window !== 'undefined' && agentId && agentId.includes(':')) {
      localStorage.removeItem('agent_id');
      agentId = '';
    }
    
    console.log('HandleStatusChange debug:', {
      selectedAgentId,
      localStorageAgentId: localStorage.getItem('agent_id'),
      finalAgentId: agentId,
      taskId: task.id,
      newStatus,
      newStatusType: typeof newStatus
    });
    
    if (!agentId) {
      alert('Please select an agent ID to update task status');
      throw new Error('No agent ID selected');
    }
    
    try {
      const apiClient = new HeadlessPMClient();
      await apiClient.updateTaskStatus(task.id, newStatus, agentId);
      return true;
    } catch (error) {
      console.error('Failed to update task status:', error);
      throw error;
    }
  }, [selectedAgentId]);

  const handleDragStart = useCallback((event: DragStartEvent) => {
    const { active } = event;
    const task = localTasks.find(t => t.id.toString() === active.id);
    setActiveTask(task || null);
  }, [localTasks]);

  const handleDragEnd = useCallback(async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTask(null);

    if (!over) return;

    // Check if agent is selected before allowing drop
    const agentId = selectedAgentId || (typeof window !== 'undefined' ? localStorage.getItem('agent_id') : '');
    if (!agentId) {
      alert('Please select an agent to move tasks. Use the dropdown above to select an agent.');
      return; // Prevent the drop
    }

    const taskId = active.id.toString();
    const task = localTasks.find(t => t.id.toString() === taskId);
    
    if (!task) return;

    // Get the status from the drop target data
    let newStatus: TaskStatus | null = null;
    
    console.log('Drop target debug:', {
      overId: over.id,
      overData: over.data.current,
      overType: over.data.current?.type
    });
    
    if (over.data.current?.type === 'column') {
      newStatus = over.data.current.status;
    } else if (typeof over.id === 'string' && over.id.startsWith('column-')) {
      // Extract status from column ID
      const extractedStatus = over.id.replace('column-', '');
      newStatus = extractedStatus as TaskStatus;
    } else {
      console.warn('Could not determine status from drop target:', over.id, over.data.current);
      return;
    }

    console.log('Extracted newStatus:', newStatus, 'Type:', typeof newStatus);

    // Ensure newStatus is a valid string value
    if (!newStatus || typeof newStatus !== 'string' || newStatus === task.status) return;
    
    // Validate that the status is one of the expected values
    const validStatuses = Object.values(TaskStatus) as string[];
    if (!validStatuses.includes(newStatus)) {
      console.error('Invalid status value:', newStatus, 'Expected one of:', validStatuses);
      return;
    }

    console.log('About to update task status:', {
      taskId: task.id,
      currentStatus: task.status,
      newStatus: newStatus,
      newStatusType: typeof newStatus,
      agentId
    });

    // Optimistically update the local state
    const updatedTasks = localTasks.map(t => 
      t.id === task.id ? { ...t, status: newStatus } : t
    );
    setLocalTasks(updatedTasks);
    setLastTasksUpdate(JSON.stringify(updatedTasks));

    try {
      // Call the API to update the task status
      await handleStatusChange(task, newStatus);
      // Refresh the data from the server
      mutate();
    } catch (error) {
      // Revert the optimistic update on error
      setLocalTasks(localTasks);
      setLastTasksUpdate(JSON.stringify(localTasks));
      console.error('Failed to update task status:', error);
      alert(`Failed to update task status: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [localTasks, mutate, handleStatusChange, selectedAgentId]);

  if (isLoading && localTasks.length === 0) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {TASK_STATUSES.map((status) => (
          <div key={status.key} className="space-y-4">
            <Skeleton className="h-12 w-full" />
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-32 w-full" />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">Failed to load tasks. Please try again later.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Agent Selector */}
      <div className="flex items-center gap-2 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <span className="text-sm font-medium">Acting as Agent:</span>
        <select 
          value={selectedAgentId} 
          onChange={(e) => setSelectedAgentId(e.target.value)}
          className="px-3 py-1 border rounded-md text-sm"
        >
          <option value="">Select an agent...</option>
          {agents?.map(agent => (
            <option key={agent.id} value={agent.agent_id}>
              {agent.name || agent.agent_id} ({agent.role})
            </option>
          ))}
        </select>
        {!selectedAgentId && (
          <span className="text-xs text-amber-600">⚠️ Select an agent to move tasks</span>
        )}
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 overflow-x-auto pb-4">
          {TASK_STATUSES.map((statusConfig) => (
            <TaskColumn
              key={statusConfig.key}
              status={statusConfig.key}
              label={statusConfig.label}
              color={statusConfig.color}
              tasks={filteredTasks}
              onStatusChange={handleStatusChange}
            />
          ))}
        </div>
        
        <DragOverlay>
          {activeTask ? (
            <TaskCard task={activeTask} />
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
}