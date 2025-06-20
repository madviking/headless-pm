'use client';

import { useApi } from '@/lib/hooks/useApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Task, AgentRole } from '@/lib/types';
import { format, addHours, startOfDay } from 'date-fns';

const ROLE_COLORS = {
  [AgentRole.FrontendDev]: 'bg-blue-500',
  [AgentRole.BackendDev]: 'bg-green-500',
  [AgentRole.QA]: 'bg-purple-500',
  [AgentRole.Architect]: 'bg-orange-500',
  [AgentRole.PM]: 'bg-red-500'
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

  // Generate some mock timeline data for demonstration (in hours)
  const now = new Date();
  const startHour = addHours(now, Math.floor(Math.random() * 4)); // Start within next 4 hours
  const duration = Math.floor(Math.random() * 8) + 1; // 1-8 hours duration
  const endHour = addHours(startHour, duration);
  const isActive = Math.random() > 0.5;
  const isCompleted = Math.random() > 0.3;

  return (
    <div className="grid grid-cols-12 gap-2 py-2 border-b last:border-b-0 items-center">
      <div className="col-span-4 flex items-center gap-2">
        <span className="text-sm">{getTaskIcon(task.title)}</span>
        <span className="text-sm font-medium truncate">{task.title}</span>
      </div>
      
      <div className="col-span-2 flex items-center gap-2">
        {task.target_role && (
          <Badge variant="outline" className="text-xs">
            {task.target_role.replace('_', ' ')}
          </Badge>
        )}
      </div>

      <div className="col-span-6 grid grid-cols-12 gap-1">
        {hours.map((hour, index) => {
          const isInRange = hour >= startHour && hour <= endHour;
          const hourClass = isInRange
            ? isCompleted
              ? 'bg-green-500'
              : isActive
                ? 'bg-blue-500'
                : 'bg-yellow-500'
            : 'bg-gray-100';

          return (
            <div
              key={index}
              className={`h-6 rounded-sm ${hourClass} flex items-center justify-center`}
              title={format(hour, 'HH:mm')}
            >
              {isInRange && (
                <div className="w-full h-2 bg-current opacity-80 rounded-sm" />
              )}
            </div>
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

  // Generate 12 hours starting from current hour
  const currentHour = startOfDay(new Date());
  const hours = Array.from({ length: 12 }, (_, i) => addHours(currentHour, i));

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
        <CardTitle>Task Timeline (Gantt View)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Header */}
          <div className="grid grid-cols-12 gap-2 pb-2 border-b font-medium text-sm">
            <div className="col-span-4">Task Name</div>
            <div className="col-span-2">Assignee</div>
            <div className="col-span-6 grid grid-cols-12 gap-1 text-center">
              {hours.map((hour, index) => (
                <div key={index} className="text-xs">
                  {format(hour, 'HH:mm')}
                </div>
              ))}
            </div>
          </div>

          {/* Task rows */}
          <div className="max-h-[400px] overflow-y-auto">
            {tasks.slice(0, 10).map((task) => (
              <TimelineRow key={task.id} task={task} hours={hours} />
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center gap-6 pt-4 border-t text-sm">
            <span className="font-medium">Legend:</span>
            <div className="flex items-center gap-2">
              <div className="w-4 h-2 bg-yellow-500 rounded-sm" />
              <span>Scheduled</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-2 bg-blue-500 rounded-sm" />
              <span>In Progress</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-2 bg-green-500 rounded-sm" />
              <span>Completed</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-2 bg-red-500 rounded-sm" />
              <span>Delayed</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}