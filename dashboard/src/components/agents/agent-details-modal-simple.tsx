'use client';

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  User, 
  Clock, 
  Target, 
  Calendar,
  Wifi,
  WifiOff,
  BrainCircuit,
  Users
} from 'lucide-react';
import { Agent, AgentRole, SkillLevel, ConnectionType } from '@/lib/types';
import { formatDistanceToNow } from 'date-fns';
import { useApi } from '@/lib/hooks/useApi';

interface AgentDetailsModalProps {
  agent: Agent | null;
  isOpen: boolean;
  onClose: () => void;
}

const ROLE_COLORS = {
  [AgentRole.FrontendDev]: 'bg-blue-500 text-white',
  [AgentRole.BackendDev]: 'bg-green-500 text-white',
  [AgentRole.QA]: 'bg-purple-500 text-white',
  [AgentRole.Architect]: 'bg-orange-500 text-white',
  [AgentRole.PM]: 'bg-red-500 text-white'
};

const SKILL_COLORS = {
  [SkillLevel.Junior]: 'bg-green-100 text-green-700',
  [SkillLevel.Senior]: 'bg-yellow-100 text-yellow-700',
  [SkillLevel.Principal]: 'bg-red-100 text-red-700'
};

const CONNECTION_COLORS = {
  [ConnectionType.Client]: 'bg-blue-100 text-blue-700',
  [ConnectionType.MCP]: 'bg-purple-100 text-purple-700'
};

export function AgentDetailsModal({ agent, isOpen, onClose }: AgentDetailsModalProps) {
  if (!agent) return null;

  // Fetch agent's recent activity
  const { data: documents } = useApi(
    ['documents', agent.id],
    (client) => client.getDocuments(agent.id),
    { enabled: isOpen }
  );

  const { data: tasks } = useApi(
    'tasks',
    (client) => client.getTasks(),
    { enabled: isOpen }
  );

  const agentTasks = tasks?.filter(task => 
    task.assigned_agent_id === agent.id || 
    task.assigned_role === agent.role
  ) || [];

  const isOnline = agent.last_seen && 
    new Date().getTime() - new Date(agent.last_seen).getTime() < 5 * 60 * 1000;

  const skillLevel = agent.level || agent.skill_level || SkillLevel.Junior;
  const roleDisplayName = agent.role.replace('_', ' ').split(' ').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${ROLE_COLORS[agent.role]}`}>
              {agent.name ? agent.name.charAt(0).toUpperCase() : agent.id.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="text-2xl font-bold">{agent.name || agent.id}</h2>
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <Badge className={SKILL_COLORS[skillLevel]}>
                  {skillLevel.toUpperCase()} {roleDisplayName}
                </Badge>
                <Badge className={CONNECTION_COLORS[agent.connection_type]}>
                  {agent.connection_type === ConnectionType.MCP ? 
                    <BrainCircuit className="h-3 w-3 mr-1" /> : 
                    <Users className="h-3 w-3 mr-1" />
                  }
                  {agent.connection_type.toUpperCase()}
                </Badge>
                {isOnline ? (
                  <div className="flex items-center gap-1 text-green-600">
                    <Wifi className="h-3 w-3" />
                    <span>ONLINE</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-gray-600">
                    <WifiOff className="h-3 w-3" />
                    <span>OFFLINE</span>
                  </div>
                )}
              </div>
            </div>
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="overview" className="mt-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="activity">Activity</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Total Tasks</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{agentTasks.length}</div>
                  <p className="text-xs text-muted-foreground">
                    {agentTasks.filter(t => t.status === TaskStatus.Committed).length} completed
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Current Task</CardTitle>
                </CardHeader>
                <CardContent>
                  {agent.current_task_id ? (
                    <>
                      <div className="text-2xl font-bold">#{agent.current_task_id}</div>
                      <p className="text-xs text-muted-foreground">In progress</p>
                    </>
                  ) : (
                    <>
                      <div className="text-2xl font-bold">-</div>
                      <p className="text-xs text-muted-foreground">Available</p>
                    </>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Documents</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{documents?.length || 0}</div>
                  <p className="text-xs text-muted-foreground">Created</p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Agent Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Agent ID:</span>
                    <div className="font-medium">{agent.id}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Role:</span>
                    <div className="font-medium">{roleDisplayName}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Skill Level:</span>
                    <div className="font-medium">{skillLevel}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Connection:</span>
                    <div className="font-medium">{agent.connection_type}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Last Seen:</span>
                    <div className="font-medium">
                      {agent.last_seen ? 
                        formatDistanceToNow(new Date(agent.last_seen), { addSuffix: true }) :
                        'Never'
                      }
                    </div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Created:</span>
                    <div className="font-medium">
                      {formatDistanceToNow(new Date(agent.created_at), { addSuffix: true })}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="activity" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Recent Tasks</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {agentTasks.slice(0, 10).map(task => (
                    <div key={task.id} className="flex items-center justify-between p-2 border rounded">
                      <div>
                        <p className="font-medium text-sm">#{task.id} - {task.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {task.status.replace('_', ' ')} • {task.difficulty} • {task.complexity}
                        </p>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {task.status}
                      </Badge>
                    </div>
                  ))}
                  {agentTasks.length === 0 && (
                    <p className="text-sm text-muted-foreground text-center py-4">
                      No tasks assigned yet
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {documents && documents.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Recent Documents</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {documents.slice(0, 5).map(doc => (
                      <div key={doc.id} className="p-2 border rounded">
                        <p className="font-medium text-sm">{doc.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {doc.type} • {formatDistanceToNow(new Date(doc.created_at), { addSuffix: true })}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}