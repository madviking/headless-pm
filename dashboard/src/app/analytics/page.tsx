'use client';

import { useMemo } from 'react';
import { PageLayout } from '@/components/layout/page-layout';
import { useTasks, useAgents, useEpics, useDocuments } from '@/lib/hooks/useApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { StatsWidget } from '@/components/ui/stats-widget';
import { 
  BarChart3, 
  TrendingUp, 
  Clock, 
  Target,
  Users,
  Activity,
  CheckCircle2,
  AlertCircle,
  Calendar,
  PieChart
} from 'lucide-react';
import { TaskStatus, AgentRole } from '@/lib/types';
import { format, subDays, isAfter } from 'date-fns';

export default function AnalyticsPage() {
  const { data: tasks, isLoading: tasksLoading } = useTasks();
  const { data: agents, isLoading: agentsLoading } = useAgents();
  const { data: epics, isLoading: epicsLoading } = useEpics();
  const { data: documents, isLoading: documentsLoading } = useDocuments();

  // Calculate analytics metrics
  const analytics = useMemo(() => {
    if (!tasks || !agents || !epics || !documents) return null;

    const now = new Date();
    const weekAgo = subDays(now, 7);
    const monthAgo = subDays(now, 30);

    // Task status distribution
    const tasksByStatus = tasks.reduce((acc, task) => {
      acc[task.status] = (acc[task.status] || 0) + 1;
      return acc;
    }, {} as Record<TaskStatus, number>);

    // Tasks by complexity
    const tasksByComplexity = tasks.reduce((acc, task) => {
      acc[task.complexity] = (acc[task.complexity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    // Tasks by role
    const tasksByRole = tasks.reduce((acc, task) => {
      if (task.assigned_role) {
        acc[task.assigned_role] = (acc[task.assigned_role] || 0) + 1;
      }
      return acc;
    }, {} as Record<AgentRole, number>);

    // Weekly activity
    const weeklyTasks = tasks.filter(task => 
      task.created_at && isAfter(new Date(task.created_at), weekAgo)
    );
    const weeklyDocs = documents.filter(doc => 
      isAfter(new Date(doc.created_at), weekAgo)
    );

    // Completion rate
    const completedTasks = tasks.filter(t => t.status === TaskStatus.Committed).length;
    const completionRate = tasks.length > 0 ? (completedTasks / tasks.length) * 100 : 0;

    // Average tasks per agent
    const activeAgents = agents.filter(a => {
      if (!a.last_seen) return false;
      const lastSeenTime = new Date(a.last_seen).getTime();
      const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
      return lastSeenTime > fiveMinutesAgo;
    });

    const avgTasksPerAgent = activeAgents.length > 0 ? tasks.length / activeAgents.length : 0;

    // Epic progress
    const epicProgress = epics.map(epic => {
      const epicTasks = tasks.filter(t => t.epic_id === epic.id);
      const completed = epicTasks.filter(t => t.status === TaskStatus.Committed).length;
      const progress = epicTasks.length > 0 ? (completed / epicTasks.length) * 100 : 0;
      return { ...epic, progress, totalTasks: epicTasks.length, completedTasks: completed };
    });

    // Team velocity (tasks completed per week)
    const velocity = weeklyTasks.filter(t => t.status === TaskStatus.Committed).length;

    return {
      tasksByStatus,
      tasksByComplexity,
      tasksByRole,
      weeklyActivity: {
        tasks: weeklyTasks.length,
        documents: weeklyDocs.length
      },
      completionRate,
      avgTasksPerAgent,
      epicProgress,
      velocity,
      totalTasks: tasks.length,
      totalAgents: agents.length,
      activeAgents: activeAgents.length
    };
  }, [tasks, agents, epics, documents]);

  if (tasksLoading || agentsLoading || epicsLoading || documentsLoading) {
    return (
      <PageLayout>
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold">Analytics & Metrics</h1>
            <p className="text-muted-foreground mt-1">Loading analytics data...</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        </div>
      </PageLayout>
    );
  }

  if (!analytics) {
    return (
      <PageLayout>
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold">Analytics & Metrics</h1>
            <p className="text-muted-foreground mt-1">No data available</p>
          </div>
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Analytics & Metrics</h1>
          <p className="text-muted-foreground mt-1">
            Team performance and project insights
          </p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsWidget
            title="Completion Rate"
            value={`${analytics.completionRate.toFixed(1)}%`}
            description={`${analytics.totalTasks} total tasks`}
            icon={<Target className="h-4 w-4" />}
            trend={{ value: 8, isPositive: true }}
          />
          <StatsWidget
            title="Team Velocity"
            value={analytics.velocity}
            description="Tasks completed this week"
            icon={<TrendingUp className="h-4 w-4" />}
            trend={{ value: 15, isPositive: true }}
          />
          <StatsWidget
            title="Avg Tasks/Agent"
            value={analytics.avgTasksPerAgent.toFixed(1)}
            description={`${analytics.activeAgents} active agents`}
            icon={<Users className="h-4 w-4" />}
          />
          <StatsWidget
            title="Weekly Activity"
            value={analytics.weeklyActivity.tasks + analytics.weeklyActivity.documents}
            description={`${analytics.weeklyActivity.tasks} tasks, ${analytics.weeklyActivity.documents} docs`}
            icon={<Activity className="h-4 w-4" />}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Task Status Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                Task Status Distribution
              </CardTitle>
              <CardDescription>Current status of all tasks</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(analytics.tasksByStatus).map(([status, count]) => {
                  const percentage = (count / analytics.totalTasks) * 100;
                  const getStatusColor = (status: string) => {
                    switch (status) {
                      case TaskStatus.Committed: return 'bg-green-500';
                      case TaskStatus.UnderWork: return 'bg-blue-500';
                      case TaskStatus.DevDone: return 'bg-purple-500';
                      case TaskStatus.QADone: return 'bg-orange-500';
                      case TaskStatus.Created: return 'bg-gray-500';
                      default: return 'bg-gray-500';
                    }
                  };
                  
                  return (
                    <div key={status} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium">{status.replace('_', ' ')}</span>
                        <span className="text-muted-foreground">{count} ({percentage.toFixed(1)}%)</span>
                      </div>
                      <Progress value={percentage} className="h-2" />
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Tasks by Role */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Tasks by Role
              </CardTitle>
              <CardDescription>Task assignment across team roles</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(analytics.tasksByRole).map(([role, count]) => {
                  const percentage = (count / analytics.totalTasks) * 100;
                  
                  return (
                    <div key={role} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium">{role.replace('_', ' ')}</span>
                        <span className="text-muted-foreground">{count} ({percentage.toFixed(1)}%)</span>
                      </div>
                      <Progress value={percentage} className="h-2" />
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Task Complexity */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Task Complexity
              </CardTitle>
              <CardDescription>Distribution by complexity level</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(analytics.tasksByComplexity).map(([complexity, count]) => {
                  const percentage = (count / analytics.totalTasks) * 100;
                  const getComplexityColor = (complexity: string) => {
                    switch (complexity) {
                      case 'minor': return 'text-green-600';
                      case 'major': return 'text-red-600';
                      default: return 'text-gray-600';
                    }
                  };
                  
                  return (
                    <div key={complexity} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className={`font-medium ${getComplexityColor(complexity)}`}>
                          {complexity}
                        </span>
                        <span className="text-muted-foreground">{count} ({percentage.toFixed(1)}%)</span>
                      </div>
                      <Progress value={percentage} className="h-2" />
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Epic Progress */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5" />
                Epic Progress
              </CardTitle>
              <CardDescription>Completion status of major initiatives</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px]">
                <div className="space-y-4">
                  {analytics.epicProgress.map((epic) => (
                    <div key={epic.id} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium truncate">{epic.name}</span>
                        <span className="text-muted-foreground">
                          {epic.completedTasks}/{epic.totalTasks}
                        </span>
                      </div>
                      <Progress value={epic.progress} className="h-2" />
                      <p className="text-xs text-muted-foreground">
                        {epic.progress.toFixed(1)}% complete
                      </p>
                    </div>
                  ))}
                  {analytics.epicProgress.length === 0 && (
                    <div className="text-center py-4">
                      <CheckCircle2 className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                      <p className="text-sm text-muted-foreground">No epics found</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Activity Timeline */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Recent Activity Summary
            </CardTitle>
            <CardDescription>
              Activity summary for the past 7 days
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-3 p-4 border rounded-lg">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Activity className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-medium">New Tasks</p>
                  <p className="text-2xl font-bold">{analytics.weeklyActivity.tasks}</p>
                  <p className="text-xs text-muted-foreground">This week</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 p-4 border rounded-lg">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-medium">Completed</p>
                  <p className="text-2xl font-bold">{analytics.velocity}</p>
                  <p className="text-xs text-muted-foreground">This week</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 p-4 border rounded-lg">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Users className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm font-medium">Team Docs</p>
                  <p className="text-2xl font-bold">{analytics.weeklyActivity.documents}</p>
                  <p className="text-xs text-muted-foreground">This week</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}