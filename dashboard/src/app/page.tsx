'use client';

import { PageLayout } from '@/components/layout/page-layout';
import { StatsWidget } from '@/components/ui/stats-widget';
import { EpicProgressCard } from '@/components/epics/epic-progress-card';
import { useEpics, useTasks, useAgents, useServices } from '@/lib/hooks/useApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Briefcase, 
  Users, 
  CheckCircle2, 
  Clock,
  Activity,
  TrendingUp,
  AlertCircle,
  Server
} from 'lucide-react';
import { TaskStatus } from '@/lib/types';

export default function Home() {
  const { data: epics, isLoading: epicsLoading } = useEpics();
  const { data: tasks, isLoading: tasksLoading } = useTasks();
  const { data: agents, isLoading: agentsLoading } = useAgents();
  const { data: services, isLoading: servicesLoading } = useServices();

  // Calculate stats
  const totalTasks = tasks?.length || 0;
  const completedTasks = tasks?.filter(t => t.status === TaskStatus.Committed).length || 0;
  const inProgressTasks = tasks?.filter(t => 
    [TaskStatus.UnderWork, TaskStatus.DevDone, TaskStatus.QADone].includes(t.status)
  ).length || 0;
  const blockedTasks = 0; // No blocked status in new enum
  
  const activeAgents = agents?.filter(a => {
    if (!a.last_seen) return false;
    const lastSeenTime = new Date(a.last_seen).getTime();
    const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
    return lastSeenTime > fiveMinutesAgo;
  }).length || 0;

  const activeServices = services?.filter(s => s.status === 'active').length || 0;

  // Recent activity
  const recentTasks = tasks?.slice(-5).reverse() || [];

  return (
    <PageLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Project Overview</h1>
          <p className="text-muted-foreground mt-1">
            Real-time dashboard for Headless PM
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsWidget
            title="Total Tasks"
            value={totalTasks}
            description={`${inProgressTasks} in progress`}
            icon={<Briefcase className="h-4 w-4" />}
          />
          <StatsWidget
            title="Completed"
            value={completedTasks}
            description={`${totalTasks > 0 ? ((completedTasks / totalTasks) * 100).toFixed(0) : 0}% completion rate`}
            icon={<CheckCircle2 className="h-4 w-4 text-green-600" />}
            trend={{ value: 12, isPositive: true }}
          />
          <StatsWidget
            title="Active Agents"
            value={`${activeAgents}/${agents?.length || 0}`}
            description="Online in last 5 minutes"
            icon={<Users className="h-4 w-4" />}
          />
          <StatsWidget
            title="Services"
            value={`${activeServices}/${services?.length || 0}`}
            description="Running services"
            icon={<Server className="h-4 w-4" />}
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Epics Section - 2 columns wide */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Active Epics</h2>
              <Badge variant="secondary">{epics?.length || 0} total</Badge>
            </div>
            
            {epicsLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[1, 2, 3, 4].map(i => (
                  <Skeleton key={i} className="h-48" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {epics?.map(epic => (
                  <EpicProgressCard key={epic.id} epic={epic} />
                ))}
                {(!epics || epics.length === 0) && (
                  <Card className="col-span-2">
                    <CardContent className="flex flex-col items-center justify-center py-8">
                      <Briefcase className="h-12 w-12 text-muted-foreground mb-2" />
                      <p className="text-muted-foreground">No epics created yet</p>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </div>

          {/* Activity Feed - 1 column wide */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Recent Activity</h2>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </div>
            
            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Latest task updates</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-4">
                    {recentTasks.map((task) => (
                      <div key={task.id} className="flex items-start gap-3 pb-3 border-b last:border-0">
                        <div className="flex-1 space-y-1">
                          <p className="text-sm font-medium leading-none">
                            {task.title}
                          </p>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Badge variant="outline" className="text-xs">
                              {task.status.replace('_', ' ')}
                            </Badge>
                            {task.assigned_agent_id && (
                              <span>• {task.assigned_agent_id}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                    {recentTasks.length === 0 && (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        No recent activity
                      </p>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Alerts Section */}
            {blockedTasks > 0 && (
              <Card className="border-destructive">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-destructive" />
                    Blocked Tasks
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    {blockedTasks} task{blockedTasks !== 1 ? 's' : ''} currently blocked
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </PageLayout>
  );
}