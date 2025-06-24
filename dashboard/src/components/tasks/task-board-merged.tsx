'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, User, Clock, GitBranch, Flag, Calendar } from 'lucide-react';
import { Task, TaskStatus, AgentRole, TaskDifficulty, TaskComplexity } from '@/lib/types';
import { format } from 'date-fns';
import { TaskFilters } from './task-filters';
import { TaskDetailModal } from './task-detail-modal';
import { useTasks, useUpdateTaskStatus, useAgents } from '@/lib/hooks/useApi';

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

function TaskCard({ 
  task, 
  onTaskClick,
  isDragging 
}: { 
  task: Task; 
  onTaskClick?: (task: Task) => void;
  isDragging?: boolean;
}) {
  const [isHovered, setIsHovered] = useState(false);
  
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
    <Card 
      draggable
      className={`mb-2 cursor-grab hover:shadow-md transition-shadow relative ${
        isDragging ? 'opacity-50' : ''
      }`}
      onDoubleClick={(e) => {
        e.stopPropagation();
        onTaskClick?.(task);
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <CardContent className="p-3">
        {isHovered && (
          <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded whitespace-nowrap z-10">
            Double-click to view details
            <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45"></div>
          </div>
        )}
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
  onTaskClick,
  onDragOver,
  onDragLeave,
  onDrop,
  isDragOver,
  onDragStart
}: { 
  status: TaskStatus; 
  label: string; 
  color: string; 
  tasks: Task[];
  onTaskClick?: (task: Task) => void;
  onDragOver: (e: React.DragEvent, status: TaskStatus) => void;
  onDragLeave: () => void;
  onDrop: (e: React.DragEvent, status: TaskStatus) => void;
  isDragOver: boolean;
  onDragStart: (e: React.DragEvent, task: Task) => void;
}) {
  const tasksInStatus = tasks.filter(task => task.status === status);
  
  return (
    <div className="flex-1 min-w-[300px]">
      <Card 
        className={`h-full flex flex-col transition-all ${
          isDragOver ? 'ring-2 ring-blue-400 bg-blue-50/20' : ''
        }`}
        onDragOver={(e) => onDragOver(e, status)}
        onDragLeave={onDragLeave}
        onDrop={(e) => onDrop(e, status)}
      >
        <CardHeader className="pb-2 px-3">
          <CardTitle className="flex items-center justify-between">
            <span className={`text-sm font-medium px-2 py-1 rounded-md ${color}`}>
              {label} ({tasksInStatus.length})
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0 px-2 flex-1 flex flex-col">
          <div className="flex flex-col flex-1 gap-2 min-h-[500px] p-1 rounded-lg">
            {tasksInStatus.map(task => (
              <div
                key={task.id}
                onDragStart={(e) => onDragStart(e, task)}
              >
                <TaskCard 
                  task={task} 
                  onTaskClick={onTaskClick}
                />
              </div>
            ))}
            
            {/* Flexible empty space to make entire column droppable */}
            <div className="flex-1 min-h-[100px]">
              {tasksInStatus.length === 0 && (
                <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
                  Drop tasks here
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function TaskBoard({ filters = {} }: { filters?: TaskFilters }) {
  const { data: tasks = [], isLoading, error, refetch } = useTasks();
  const { data: agents = [] } = useAgents();
  const updateTaskStatus = useUpdateTaskStatus();
  
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [draggedTask, setDraggedTask] = useState<Task | null>(null);
  const [dragOverStatus, setDragOverStatus] = useState<TaskStatus | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);

  // Load agent ID from localStorage after hydration
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedAgentId = localStorage.getItem('agent_id') || '';
      if (storedAgentId && !storedAgentId.includes(':')) {
        setSelectedAgentId(storedAgentId);
      }
    }
  }, []);

  // Save selected agent ID to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined' && selectedAgentId) {
      localStorage.setItem('agent_id', selectedAgentId);
    }
  }, [selectedAgentId]);

  // Apply filters to tasks
  const filteredTasks = tasks.filter(task => {
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

  const handleTaskClick = useCallback((task: Task) => {
    setSelectedTask(task);
    setIsTaskModalOpen(true);
  }, []);

  const handleDragStart = (e: React.DragEvent, task: Task) => {
    setDraggedTask(task);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, status: TaskStatus) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverStatus(status);
  };

  const handleDragLeave = () => {
    setDragOverStatus(null);
  };

  const handleDrop = async (e: React.DragEvent, newStatus: TaskStatus) => {
    e.preventDefault();
    setDragOverStatus(null);

    if (!draggedTask || !selectedAgentId) {
      alert('Please select an agent to move tasks. Use the dropdown above to select an agent.');
      return;
    }

    if (draggedTask.status === newStatus) {
      return; // No change needed
    }

    try {
      await updateTaskStatus.mutateAsync({
        taskId: draggedTask.id,
        status: newStatus,
        agentId: selectedAgentId
      });
      refetch(); // Refresh the task list
    } catch (error) {
      console.error('Failed to update task status:', error);
      alert('Failed to update task status');
    }
  };

  if (isLoading) {
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

      {/* Task Board */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {TASK_STATUSES.map((statusConfig) => (
          <TaskColumn
            key={statusConfig.key}
            status={statusConfig.key}
            label={statusConfig.label}
            color={statusConfig.color}
            tasks={filteredTasks}
            onTaskClick={handleTaskClick}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            isDragOver={dragOverStatus === statusConfig.key}
          />
        ))}
      </div>

      <TaskDetailModal
        task={selectedTask}
        isOpen={isTaskModalOpen}
        onClose={() => {
          setIsTaskModalOpen(false);
          setSelectedTask(null);
        }}
      />
    </div>
  );
}