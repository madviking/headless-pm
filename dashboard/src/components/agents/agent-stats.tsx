'use client';

import { useApi } from '@/lib/hooks/useApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Users, Activity, Clock, TrendingUp, Zap, BrainCircuit } from 'lucide-react';
import { Agent, ConnectionType, SkillLevel } from '@/lib/types';

export function AgentStats() {
  const { data: agents, isLoading } = useApi(
    'agents',
    (client) => client.getAgents(),
    { staleTime: 10000, refetchInterval: 30000 }
  );

  const agentsList = agents || [];

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16 mb-2" />
              <Skeleton className="h-3 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const onlineAgents = agentsList.filter(agent => 
    agent.last_seen && 
    new Date().getTime() - new Date(agent.last_seen).getTime() < 5 * 60 * 1000 // 5 minutes
  );

  const workingAgents = agentsList.filter(agent => agent.current_task_id);

  const mcpAgents = agentsList.filter(agent => agent.connection_type === ConnectionType.MCP);

  const skillDistribution = {
    [SkillLevel.Junior]: agentsList.filter(a => (a.level || a.skill_level) === SkillLevel.Junior).length,
    [SkillLevel.Senior]: agentsList.filter(a => (a.level || a.skill_level) === SkillLevel.Senior).length,
    [SkillLevel.Principal]: agentsList.filter(a => (a.level || a.skill_level) === SkillLevel.Principal).length,
  };

  const averagePerformance = Math.floor(Math.random() * 20) + 80; // Mock data
  const totalTasksToday = Math.floor(Math.random() * 50) + 20; // Mock data

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
          <Users className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{agentsList.length}</div>
          <p className="text-xs text-muted-foreground">
            {onlineAgents.length} currently online
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Workers</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{workingAgents.length}</div>
          <p className="text-xs text-muted-foreground">
            {workingAgents.length > 0 ? 
              `${Math.round((workingAgents.length / agentsList.length) * 100)}% utilization` :
              'No active tasks'
            }
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Tasks Completed</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalTasksToday}</div>
          <p className="text-xs text-muted-foreground">
            +12% from yesterday
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Performance</CardTitle>
          <Zap className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{averagePerformance}%</div>
          <p className="text-xs text-muted-foreground">
            Team performance score
          </p>
        </CardContent>
      </Card>

      <Card className="md:col-span-2 lg:col-span-4">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Team Composition</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="space-y-2">
              <div className="text-sm font-medium">By Skill Level</div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Junior:</span>
                  <span className="font-semibold">{skillDistribution[SkillLevel.Junior]}</span>
                </div>
                <div className="flex justify-between">
                  <span>Senior:</span>
                  <span className="font-semibold">{skillDistribution[SkillLevel.Senior]}</span>
                </div>
                <div className="flex justify-between">
                  <span>Principal:</span>
                  <span className="font-semibold">{skillDistribution[SkillLevel.Principal]}</span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-sm font-medium">Connection Types</div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="flex items-center gap-1">
                    <BrainCircuit className="h-3 w-3" />
                    MCP:
                  </span>
                  <span className="font-semibold">{mcpAgents.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    Client:
                  </span>
                  <span className="font-semibold">{agentsList.length - mcpAgents.length}</span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-sm font-medium">Status Overview</div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-green-600">Online:</span>
                  <span className="font-semibold">{onlineAgents.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Offline:</span>
                  <span className="font-semibold">{agentsList.length - onlineAgents.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-blue-600">Working:</span>
                  <span className="font-semibold">{workingAgents.length}</span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-sm font-medium">Quick Actions</div>
              <div className="space-y-1">
                <button className="text-xs text-blue-600 hover:underline block">
                  View All Agents
                </button>
                <button className="text-xs text-blue-600 hover:underline block">
                  Register New Agent
                </button>
                <button className="text-xs text-blue-600 hover:underline block">
                  Performance Report
                </button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}