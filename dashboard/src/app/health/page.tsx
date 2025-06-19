'use client';

import { useState, useMemo } from 'react';
import { PageLayout } from '@/components/layout/page-layout';
import { useServices, useAgents } from '@/lib/hooks/useApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { StatsWidget } from '@/components/ui/stats-widget';
import { 
  Server, 
  Activity, 
  AlertCircle, 
  CheckCircle2,
  Clock,
  Users,
  Wifi,
  Database,
  Globe,
  Zap,
  RefreshCw,
  Link
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function HealthPage() {
  const { data: services, isLoading: servicesLoading, refetch: refetchServices } = useServices();
  const { data: agents, isLoading: agentsLoading, refetch: refetchAgents } = useAgents();

  // Calculate health metrics
  const healthMetrics = useMemo(() => {
    if (!services || !agents) return null;

    const now = Date.now();
    const fiveMinutesAgo = now - 5 * 60 * 1000;
    const oneHourAgo = now - 60 * 60 * 1000;

    // Service health
    const activeServices = services.filter(s => s.status === 'active');
    const inactiveServices = services.filter(s => s.status === 'inactive');
    const servicesWithPing = services.filter(s => s.ping_url);

    // Agent health
    const onlineAgents = agents.filter(a => {
      if (!a.last_seen) return false;
      const lastSeenTime = new Date(a.last_seen).getTime();
      return lastSeenTime > fiveMinutesAgo;
    });

    const recentlyActiveAgents = agents.filter(a => {
      if (!a.last_seen) return false;
      const lastSeenTime = new Date(a.last_seen).getTime();
      return lastSeenTime > oneHourAgo && lastSeenTime <= fiveMinutesAgo;
    });

    const offlineAgents = agents.filter(a => {
      if (!a.last_seen) return true;
      const lastSeenTime = new Date(a.last_seen).getTime();
      return lastSeenTime <= oneHourAgo;
    });

    // Overall system health score
    const totalServices = services.length;
    const totalAgents = agents.length;
    const healthyServices = activeServices.length;
    const healthyAgents = onlineAgents.length;
    
    const serviceHealthScore = totalServices > 0 ? (healthyServices / totalServices) * 100 : 100;
    const agentHealthScore = totalAgents > 0 ? (healthyAgents / totalAgents) * 100 : 100;
    const overallHealthScore = (serviceHealthScore + agentHealthScore) / 2;

    return {
      services: {
        total: totalServices,
        active: activeServices.length,
        inactive: inactiveServices.length,
        withPing: servicesWithPing.length,
        healthScore: serviceHealthScore
      },
      agents: {
        total: totalAgents,
        online: onlineAgents.length,
        recentlyActive: recentlyActiveAgents.length,
        offline: offlineAgents.length,
        healthScore: agentHealthScore
      },
      overallHealthScore,
      servicesData: services,
      agentsData: agents,
      onlineAgents,
      recentlyActiveAgents,
      offlineAgents
    };
  }, [services, agents]);

  const getServiceStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getAgentStatusColor = (agent: any) => {
    if (!agent.last_seen) return 'bg-gray-100 text-gray-800';
    
    const lastSeenTime = new Date(agent.last_seen).getTime();
    const now = Date.now();
    const fiveMinutesAgo = now - 5 * 60 * 1000;
    const oneHourAgo = now - 60 * 60 * 1000;

    if (lastSeenTime > fiveMinutesAgo) return 'bg-green-100 text-green-800';
    if (lastSeenTime > oneHourAgo) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getAgentStatus = (agent: any) => {
    if (!agent.last_seen) return 'Never seen';
    
    const lastSeenTime = new Date(agent.last_seen).getTime();
    const now = Date.now();
    const fiveMinutesAgo = now - 5 * 60 * 1000;
    const oneHourAgo = now - 60 * 60 * 1000;

    if (lastSeenTime > fiveMinutesAgo) return 'Online';
    if (lastSeenTime > oneHourAgo) return 'Recently Active';
    return 'Offline';
  };

  const handleRefresh = () => {
    refetchServices();
    refetchAgents();
  };

  if (servicesLoading || agentsLoading) {
    return (
      <PageLayout>
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold">System Health</h1>
            <p className="text-muted-foreground mt-1">Loading system status...</p>
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

  if (!healthMetrics) {
    return (
      <PageLayout>
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold">System Health</h1>
            <p className="text-muted-foreground mt-1">No health data available</p>
          </div>
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold">System Health</h1>
            <p className="text-muted-foreground mt-1">
              Service registry and agent monitoring
            </p>
          </div>
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-3 py-2 text-sm border rounded-md hover:bg-gray-50"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>

        {/* System Health Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsWidget
            title="Overall Health"
            value={`${healthMetrics.overallHealthScore.toFixed(0)}%`}
            description="System status"
            icon={<Activity className="h-4 w-4" />}
            trend={{ 
              value: healthMetrics.overallHealthScore > 80 ? 5 : -10, 
              isPositive: healthMetrics.overallHealthScore > 80 
            }}
          />
          <StatsWidget
            title="Services"
            value={`${healthMetrics.services.active}/${healthMetrics.services.total}`}
            description="Active services"
            icon={<Server className="h-4 w-4" />}
          />
          <StatsWidget
            title="Agents"
            value={`${healthMetrics.agents.online}/${healthMetrics.agents.total}`}
            description="Online agents"
            icon={<Users className="h-4 w-4" />}
          />
          <StatsWidget
            title="Connectivity"
            value={`${healthMetrics.services.withPing}/${healthMetrics.services.total}`}
            description="Services with ping"
            icon={<Wifi className="h-4 w-4" />}
          />
        </div>

        {/* Detailed Health Info */}
        <Tabs defaultValue="services" className="space-y-4">
          <TabsList>
            <TabsTrigger value="services">Services</TabsTrigger>
            <TabsTrigger value="agents">Agents</TabsTrigger>
            <TabsTrigger value="system">System Overview</TabsTrigger>
          </TabsList>

          <TabsContent value="services" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Server className="h-5 w-5" />
                  Service Registry
                </CardTitle>
                <CardDescription>
                  Registered services and their health status
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[500px]">
                  <div className="space-y-4">
                    {healthMetrics.servicesData.length > 0 ? (
                      healthMetrics.servicesData.map((service) => (
                        <Card key={service.id} className="p-4">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 space-y-2">
                              <div className="flex items-center gap-2">
                                <h3 className="font-medium">{service.name}</h3>
                                <Badge className={getServiceStatusColor(service.status)}>
                                  {service.status}
                                </Badge>
                                {service.ping_url && (
                                  <Badge variant="outline" className="text-xs">
                                    <Link className="h-3 w-3 mr-1" />
                                    Pingable
                                  </Badge>
                                )}
                              </div>
                              <div className="text-sm text-muted-foreground space-y-1">
                                <p><span className="font-medium">Type:</span> {service.type}</p>
                                <p><span className="font-medium">Endpoint:</span> {service.endpoint_url}</p>
                                {service.ping_url && (
                                  <p><span className="font-medium">Ping URL:</span> {service.ping_url}</p>
                                )}
                                <p><span className="font-medium">Last heartbeat:</span> {
                                  service.last_heartbeat 
                                    ? formatDistanceToNow(new Date(service.last_heartbeat), { addSuffix: true })
                                    : 'Never'
                                }</p>
                              </div>
                              {service.metadata && Object.keys(service.metadata).length > 0 && (
                                <div className="text-xs">
                                  <span className="font-medium">Metadata:</span>
                                  <pre className="mt-1 p-2 bg-gray-50 rounded text-xs">
                                    {JSON.stringify(service.metadata, null, 2)}
                                  </pre>
                                </div>
                              )}
                            </div>
                            <div className="flex items-center">
                              {service.status === 'active' ? (
                                <CheckCircle2 className="h-5 w-5 text-green-600" />
                              ) : (
                                <AlertCircle className="h-5 w-5 text-red-600" />
                              )}
                            </div>
                          </div>
                        </Card>
                      ))
                    ) : (
                      <div className="text-center py-8">
                        <Server className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                        <p className="text-muted-foreground">No services registered</p>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="agents" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Online Agents */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-green-600">
                    <CheckCircle2 className="h-5 w-5" />
                    Online ({healthMetrics.agents.online})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-2">
                      {healthMetrics.onlineAgents.map(agent => (
                        <div key={agent.id} className="p-3 border rounded-lg">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium text-sm">{agent.name || agent.id}</p>
                              <p className="text-xs text-muted-foreground">{agent.role}</p>
                              <p className="text-xs text-muted-foreground">
                                {agent.last_seen && formatDistanceToNow(new Date(agent.last_seen), { addSuffix: true })}
                              </p>
                            </div>
                            <Badge className="bg-green-100 text-green-800 text-xs">Online</Badge>
                          </div>
                        </div>
                      ))}
                      {healthMetrics.agents.online === 0 && (
                        <p className="text-sm text-muted-foreground text-center py-4">No online agents</p>
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>

              {/* Recently Active Agents */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-yellow-600">
                    <Clock className="h-5 w-5" />
                    Recently Active ({healthMetrics.agents.recentlyActive})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-2">
                      {healthMetrics.recentlyActiveAgents.map(agent => (
                        <div key={agent.id} className="p-3 border rounded-lg">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium text-sm">{agent.name || agent.id}</p>
                              <p className="text-xs text-muted-foreground">{agent.role}</p>
                              <p className="text-xs text-muted-foreground">
                                {agent.last_seen && formatDistanceToNow(new Date(agent.last_seen), { addSuffix: true })}
                              </p>
                            </div>
                            <Badge className="bg-yellow-100 text-yellow-800 text-xs">Away</Badge>
                          </div>
                        </div>
                      ))}
                      {healthMetrics.agents.recentlyActive === 0 && (
                        <p className="text-sm text-muted-foreground text-center py-4">No recently active agents</p>
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>

              {/* Offline Agents */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-red-600">
                    <AlertCircle className="h-5 w-5" />
                    Offline ({healthMetrics.agents.offline})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-2">
                      {healthMetrics.offlineAgents.map(agent => (
                        <div key={agent.id} className="p-3 border rounded-lg">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium text-sm">{agent.name || agent.id}</p>
                              <p className="text-xs text-muted-foreground">{agent.role}</p>
                              <p className="text-xs text-muted-foreground">
                                {agent.last_seen 
                                  ? formatDistanceToNow(new Date(agent.last_seen), { addSuffix: true })
                                  : 'Never seen'
                                }
                              </p>
                            </div>
                            <Badge className="bg-red-100 text-red-800 text-xs">Offline</Badge>
                          </div>
                        </div>
                      ))}
                      {healthMetrics.agents.offline === 0 && (
                        <p className="text-sm text-muted-foreground text-center py-4">No offline agents</p>
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="system" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Health Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5" />
                    Health Summary
                  </CardTitle>
                  <CardDescription>Overall system health metrics</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-2">
                      <Server className="h-4 w-4 text-blue-600" />
                      <span className="text-sm font-medium">Service Health</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold">{healthMetrics.services.healthScore.toFixed(0)}%</span>
                      {healthMetrics.services.healthScore > 80 ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-red-600" />
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-purple-600" />
                      <span className="text-sm font-medium">Agent Health</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold">{healthMetrics.agents.healthScore.toFixed(0)}%</span>
                      {healthMetrics.agents.healthScore > 80 ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-red-600" />
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-2">
                      <Zap className="h-4 w-4 text-green-600" />
                      <span className="text-sm font-medium">Overall Health</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold">{healthMetrics.overallHealthScore.toFixed(0)}%</span>
                      {healthMetrics.overallHealthScore > 80 ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-red-600" />
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* System Info */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    System Information
                  </CardTitle>
                  <CardDescription>Current system status and configuration</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">API Endpoint</span>
                      <span className="font-mono text-xs">{process.env.NEXT_PUBLIC_API_URL || 'http://localhost:6969'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Total Services</span>
                      <span>{healthMetrics.services.total}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Total Agents</span>
                      <span>{healthMetrics.agents.total}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Last Updated</span>
                      <span>{new Date().toLocaleTimeString()}</span>
                    </div>
                  </div>
                  
                  <div className="pt-3 border-t">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Globe className="h-4 w-4" />
                      <span>Auto-refresh every 5 seconds</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </PageLayout>
  );
}