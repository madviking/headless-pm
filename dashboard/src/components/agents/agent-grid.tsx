'use client';

import { useState, useMemo } from 'react';
import { useApi } from '@/lib/hooks/useApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { AgentDetailsModal } from './agent-details-modal-simple';
import { AgentFilters } from './agent-filters';
import { 
  User, 
  Clock, 
  CheckCircle, 
  MessageSquare, 
  Star, 
  Zap, 
  Eye,
  WifiOff,
  Wifi,
  BrainCircuit,
  Users
} from 'lucide-react';
import { Agent, AgentRole, SkillLevel, ConnectionType } from '@/lib/types';
import { format, formatDistanceToNow } from 'date-fns';

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

interface AgentCardProps {
  agent: Agent;
  onViewDetails: (agent: Agent) => void;
}

function AgentCard({ agent, onViewDetails }: AgentCardProps) {
  const isOnline = agent.last_seen && 
    new Date().getTime() - new Date(agent.last_seen).getTime() < 5 * 60 * 1000; // 5 minutes

  const skillLevel = agent.level || agent.skill_level || SkillLevel.Junior;
  const roleDisplayName = agent.role.replace('_', ' ').split(' ').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${ROLE_COLORS[agent.role]}`}>
              {agent.name ? agent.name.charAt(0).toUpperCase() : agent.agent_id.charAt(0).toUpperCase()}
            </div>
            <div>
              <h3 className="font-semibold">{agent.name || agent.agent_id}</h3>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
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
          </div>
          <Button variant="outline" size="sm" onClick={() => onViewDetails(agent)}>
            <Eye className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <Badge className={SKILL_COLORS[skillLevel]}>
            <Zap className="h-3 w-3 mr-1" />
            {skillLevel.toUpperCase()} {roleDisplayName.toUpperCase()}
          </Badge>
          <Badge className={CONNECTION_COLORS[agent.connection_type]}>
            {agent.connection_type === ConnectionType.MCP ? 
              <BrainCircuit className="h-3 w-3 mr-1" /> : 
              <Users className="h-3 w-3 mr-1" />
            }
            {agent.connection_type.toUpperCase()}
          </Badge>
        </div>

        {agent.last_seen && (
          <div className="text-sm text-muted-foreground">
            <Clock className="h-3 w-3 inline mr-1" />
            Last seen: {formatDistanceToNow(new Date(agent.last_seen), { addSuffix: true })}
          </div>
        )}

        {agent.current_task_id && (
          <div className="space-y-2">
            <div className="text-sm font-medium">Current Task: #{agent.current_task_id}</div>
          </div>
        )}

        <div className="pt-2">
          <Button variant="outline" size="sm" className="w-full" onClick={() => onViewDetails(agent)}>
            View Details
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

interface AgentGridProps {
  filters?: AgentFilters;
}

export function AgentGrid({ filters }: AgentGridProps) {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: agents, isLoading, error } = useApi(
    'agents',
    (client) => client.getAgents(),
    { staleTime: 10000, refetchInterval: 30000 }
  );

  const agentsList = agents || [];

  // Filter agents based on provided filters
  const filteredAgents = useMemo(() => {
    if (!filters) return agentsList;

    return agentsList.filter(agent => {
      const skillLevel = agent.level || agent.skill_level || SkillLevel.Junior;
      const isOnline = agent.last_seen && 
        new Date().getTime() - new Date(agent.last_seen).getTime() < 5 * 60 * 1000;
      
      // Search filter
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase();
        const agentName = (agent.name || agent.agent_id).toLowerCase();
        if (!agentName.includes(searchTerm)) return false;
      }

      // Role filter
      if (filters.role !== 'all' && agent.role !== filters.role) return false;

      // Skill level filter
      if (filters.skillLevel !== 'all' && skillLevel !== filters.skillLevel) return false;

      // Connection type filter
      if (filters.connectionType !== 'all' && agent.connection_type !== filters.connectionType) return false;

      // Status filter
      if (filters.status !== 'all') {
        switch (filters.status) {
          case 'online':
            if (!isOnline) return false;
            break;
          case 'offline':
            if (isOnline) return false;
            break;
          case 'working':
            if (!agent.current_task_id) return false;
            break;
        }
      }

      return true;
    });
  }, [agentsList, filters]);

  const handleViewDetails = (agent: Agent) => {
    setSelectedAgent(agent);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedAgent(null);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Agent Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-80 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">Failed to load agents. Please try again later.</p>
      </div>
    );
  }

  const onlineAgents = filteredAgents.filter(agent => 
    agent.last_seen && 
    new Date().getTime() - new Date(agent.last_seen).getTime() < 5 * 60 * 1000
  );

  const workingAgents = filteredAgents.filter(agent => agent.current_task_id);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">
          Agent Status
          {filters && (
            <span className="text-base font-normal text-muted-foreground ml-2">
              ({filteredAgents.length} {filteredAgents.length === 1 ? 'agent' : 'agents'})
            </span>
          )}
        </h2>
        <div className="text-sm text-muted-foreground">
          {onlineAgents.length} online • {workingAgents.length} working
        </div>
      </div>
      
      {filteredAgents.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-muted-foreground">
            {agentsList.length === 0 ? 'No agents registered yet.' : 'No agents match the current filters.'}
          </p>
          {agentsList.length === 0 && <Button className="mt-4">Register New Agent</Button>}
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredAgents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} onViewDetails={handleViewDetails} />
          ))}
        </div>
      )}

      <AgentDetailsModal 
        agent={selectedAgent}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  );
}