'use client';

import { useApi } from '@/lib/hooks/useApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Task, AgentRole, TaskStatus } from '@/lib/types';
import { format, addHours, startOfDay, differenceInHours, isWithinInterval } from 'date-fns';

const ROLE_COLORS = {
  [AgentRole.FrontendDev]: 'bg-blue-500',
  [AgentRole.BackendDev]: 'bg-green-500',
  [AgentRole.QA]: 'bg-purple-500',
  [AgentRole.Architect]: 'bg-orange-500',
  [AgentRole.PM]: 'bg-red-500'
};

const STATUS_COLORS = {
  [TaskStatus.Created]: 'bg-slate-300',
  [TaskStatus.UnderWork]: 'bg-blue-500',
  [TaskStatus.DevDone]: 'bg-yellow-500',
  [TaskStatus.QADone]: 'bg-purple-500',
  [TaskStatus.DocumentationDone]: 'bg-orange-500',
  [TaskStatus.Committed]: 'bg-green-500',
  [TaskStatus.Evaluation]: 'bg-indigo-500',
  [TaskStatus.Approved]: 'bg-cyan-500'
};

// Special colors for timeline phases
const TIMELINE_COLORS = {
  created: 'bg-slate-300'
};

function TimelineRow({ task, hours }: { task: Task; hours: Date[] }) {
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

  // Parse task timestamps
  const taskCreatedTime = task.created_at ? new Date(task.created_at) : new Date();
  const taskUpdatedTime = task.updated_at ? new Date(task.updated_at) : taskCreatedTime;
  
  // Determine what phase the task was in for each hour slot
  const getTaskPhaseForHour = (hour: Date) => {
    // Task wasn't created yet
    if (hour < taskCreatedTime) {
      return null;
    }
    
    // If task was just created and never updated, show as created
    if (taskCreatedTime.getTime() === taskUpdatedTime.getTime()) {
      return 'created';
    }
    
    // Show created phase from creation until update
    if (hour >= taskCreatedTime && hour < taskUpdatedTime) {
      return 'created';
    }
    
    // Show final status at the updated time point
    if (hour >= taskUpdatedTime) {
      return 'final_status';
    }
    
    return null;
  };
  
  const getPhaseColor = (phase: string | null) => {
    switch (phase) {
      case 'created': return TIMELINE_COLORS.created;
      case 'final_status': return STATUS_COLORS[task.status] || 'bg-gray-400';
      default: return 'bg-gray-100';
    }
  };

  return (
    <div className="grid grid-cols-12 gap-2 py-2 border-b last:border-b-0 items-center">
      <div className="col-span-4 flex items-center gap-2">
        <span className="text-sm">{getTaskIcon(task.title)}</span>
        <span className="text-sm font-medium truncate">{task.title}</span>
      </div>
      
      <div className="col-span-2 flex flex-col gap-1">
        {task.target_role && (
          <Badge variant="outline" className="text-xs">
            {task.target_role.replace('_', ' ')}
          </Badge>
        )}
        <Badge variant="secondary" className="text-xs">
          {task.status.replace('_', ' ')}
        </Badge>
      </div>

      <div className="col-span-6 grid grid-cols-12 gap-1">
        {hours.map((hour, index) => {
          const phase = getTaskPhaseForHour(hour);
          const hourClass = getPhaseColor(phase);
          const hasActivity = phase !== null;

          const getPhaseLabel = (phase: string | null) => {
            switch (phase) {
              case 'created': return 'Created';
              case 'final_status': return task.status.replace('_', ' ');
              default: return '';
            }
          };

          return (
            <div
              key={index}
              className={`h-6 rounded-sm ${hourClass} ${hasActivity ? 'border border-gray-300' : 'border border-gray-200'}`}
              title={`${format(hour, 'HH:mm')} - ${getPhaseLabel(phase)}`}
            />
          );
        })}
      </div>
    </div>
  );
}

export function TaskTimeline({ filters = {} }: { filters?: any }) {
  const { data: tasks = [], isLoading, error } = useApi(
    'tasks',
    (client) => client.getTasks()
  );

  // Generate 12 hours starting from 12 hours ago (better for task tracking)
  const now = new Date();
  const startTime = addHours(now, -12);
  const hours = Array.from({ length: 12 }, (_, i) => addHours(startTime, i));

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Task Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Task Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Failed to load tasks. Please try again later.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Task Timeline (Past 12 Hours)</CardTitle>
        <p className="text-sm text-muted-foreground">
          Shows task lifecycle: creation time → status change at updated_at
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Header */}
          <div className="grid grid-cols-12 gap-2 pb-2 border-b font-medium text-sm">
            <div className="col-span-4">Task Name</div>
            <div className="col-span-2">Role & Status</div>
            <div className="col-span-6 grid grid-cols-12 gap-1 text-center">
              {hours.map((hour, index) => (
                <div key={index} className="text-xs" title={format(hour, 'MMM dd, HH:mm')}>
                  {format(hour, 'HH:mm')}
                </div>
              ))}
            </div>
          </div>

          {/* Task rows */}
          <div className="max-h-[600px] overflow-y-auto">
            {tasks.map((task) => (
              <TimelineRow key={task.id} task={task} hours={hours} />
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 pt-4 border-t text-sm flex-wrap">
            <span className="font-medium">Timeline Legend:</span>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-slate-300 rounded-sm border border-gray-300" />
              <span>Created</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-yellow-500 rounded-sm border border-gray-300" />
              <span>Dev Done</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-purple-500 rounded-sm border border-gray-300" />
              <span>QA Done</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-orange-500 rounded-sm border border-gray-300" />
              <span>Docs Done</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded-sm border border-gray-300" />
              <span>Committed</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}