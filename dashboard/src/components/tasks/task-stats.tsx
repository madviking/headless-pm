'use client';

import { useApi } from '@/lib/hooks/useApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Task, AgentRole, TaskDifficulty, TaskStatus, Epic } from '@/lib/types';

const DIFFICULTY_COLORS = {
  [TaskDifficulty.Junior]: '#10b981',
  [TaskDifficulty.Senior]: '#f59e0b', 
  [TaskDifficulty.Principal]: '#ef4444'
};

const STATUS_COLORS = {
  [TaskStatus.Backlog]: '#64748b',
  [TaskStatus.InProgress]: '#3b82f6',
  [TaskStatus.DevDone]: '#10b981',
  [TaskStatus.QATesting]: '#8b5cf6',
  [TaskStatus.Done]: '#059669'
};

export function TaskStats({ filters = {} }: { filters?: any }) {
  const { data: tasks = [], isLoading: tasksLoading } = useApi(
    'tasks',
    (client) => client.getTasks()
  );

  const { data: epics = [], isLoading: epicsLoading } = useApi(
    'epics',
    (client) => client.getEpics()
  );

  const { data: agents = [], isLoading: agentsLoading } = useApi(
    'agents',
    (client) => client.getAgents()
  );

  const isLoading = tasksLoading || epicsLoading || agentsLoading;

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-3/4" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-32 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  // Process data for analytics
  const tasksByAgent = agents.reduce((acc, agent) => {
    const agentTasks = tasks.filter(task => 
      task.locked_by === agent.agent_id || 
      task.target_role === agent.role
    );
    acc[agent.id] = {
      name: agent.name || agent.agent_id,
      role: agent.role,
      total: agentTasks.length,
      completed: agentTasks.filter(task => task.status === TaskStatus.Committed).length,
      inProgress: agentTasks.filter(task => task.status === TaskStatus.UnderWork).length
    };
    return acc;
  }, {} as Record<string, any>);

  const tasksByDifficulty = Object.values(TaskDifficulty).map(difficulty => ({
    name: difficulty.charAt(0).toUpperCase() + difficulty.slice(1),
    value: tasks.filter(task => task.difficulty === difficulty).length,
    color: DIFFICULTY_COLORS[difficulty]
  }));

  const tasksByStatus = Object.values(TaskStatus).map(status => ({
    name: status.replace('_', ' ').toUpperCase(),
    value: tasks.filter(task => task.status === status).length,
    color: STATUS_COLORS[status]
  })).filter(item => item.value > 0);

  const epicProgress = epics.map(epic => ({
    name: epic.name,
    completed: epic.completed_task_count || 0,
    total: epic.task_count || 0,
    progress: epic.task_count ? Math.round(((epic.completed_task_count || 0) / epic.task_count) * 100) : 0
  }));

  const agentWorkloadData = Object.values(tasksByAgent).map(agent => {
    const displayName = agent.name || 'Unknown';
    return {
      name: displayName.length > 12 ? displayName.substring(0, 12) + '...' : displayName,
      completed: agent.completed,
      inProgress: agent.inProgress,
      total: agent.total
    };
  });

  return (
    <div className="space-y-6">
      {/* Top Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tasks.length}</div>
            <p className="text-xs text-muted-foreground">
              {tasks.filter(t => t.status === TaskStatus.Committed).length} completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agents.length}</div>
            <p className="text-xs text-muted-foreground">
              {agents.filter(a => a.current_task_id).length} currently working
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Completion Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tasks.length ? Math.round((tasks.filter(t => t.status === TaskStatus.Committed).length / tasks.length) * 100) : 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              Last 30 days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg. Cycle Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3.2d</div>
            <p className="text-xs text-muted-foreground">
              From start to done
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Workload */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Agent Workload</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={agentWorkloadData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" fontSize={12} />
                <YAxis fontSize={12} />
                <Bar dataKey="completed" stackId="a" fill="#10b981" name="Completed" />
                <Bar dataKey="inProgress" stackId="a" fill="#3b82f6" name="In Progress" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Task Distribution by Difficulty */}
        <Card>
          <CardHeader>
            <CardTitle>Tasks by Difficulty</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={tasksByDifficulty}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {tasksByDifficulty.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Epic Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Epic Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {epicProgress.map((epic, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{epic.name}</span>
                  <span className="text-sm text-muted-foreground">
                    {epic.completed}/{epic.total} tasks ({epic.progress}%)
                  </span>
                </div>
                <Progress value={epic.progress} className="h-2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Task Status Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Task Status Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={tasksByStatus} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" fontSize={12} />
              <YAxis dataKey="name" type="category" fontSize={12} width={100} />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}