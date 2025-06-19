'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Activity, 
  Clock, 
  CheckCircle, 
  AlertTriangle, 
  MessageSquare, 
  GitBranch,
  Users,
  Pause,
  RefreshCw,
  FileText,
  User
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useApi } from '@/lib/hooks/useApi';
import { Changes } from '@/lib/types';

interface ActivityEvent {
  id: string;
  type: 'task' | 'document' | 'agent' | 'mention' | 'service';
  title: string;
  description: string;
  agent?: string;
  timestamp: Date;
  priority: 'high' | 'medium' | 'low';
  metadata?: Record<string, any>;
}

function getEventIcon(type: ActivityEvent['type']) {
  switch (type) {
    case 'task':
      return <GitBranch className="h-4 w-4" />;
    case 'document':
      return <FileText className="h-4 w-4" />;
    case 'agent':
      return <Users className="h-4 w-4" />;
    case 'mention':
      return <MessageSquare className="h-4 w-4" />;
    case 'service':
      return <AlertTriangle className="h-4 w-4" />;
    default:
      return <Activity className="h-4 w-4" />;
  }
}

function getPriorityColor(priority: ActivityEvent['priority']) {
  switch (priority) {
    case 'high':
      return 'text-red-600 bg-red-50 border-red-200';
    case 'medium':
      return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'low':
      return 'text-green-600 bg-green-50 border-green-200';
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
}

function ActivityEventCard({ event }: { event: ActivityEvent }) {
  const iconColorClass = getPriorityColor(event.priority);

  return (
    <div className={`border rounded-lg p-3 space-y-2 ${iconColorClass}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          {getEventIcon(event.type)}
          <span className="text-xs font-medium">
            {formatDistanceToNow(event.timestamp, { addSuffix: true })}
          </span>
        </div>
        <Badge variant="outline" className="text-xs">
          {event.priority.toUpperCase()}
        </Badge>
      </div>
      
      <div>
        <h4 className="text-sm font-medium">{event.title}</h4>
        <p className="text-xs text-muted-foreground mt-1">{event.description}</p>
        {event.agent && (
          <p className="text-xs text-muted-foreground mt-1">
            <User className="h-3 w-3 inline mr-1" />
            {event.agent}
          </p>
        )}
      </div>
    </div>
  );
}

export function AgentActivityFeed() {
  const [isLive, setIsLive] = useState(false);
  const [lastTimestamp, setLastTimestamp] = useState(Date.now() - 60 * 60 * 1000); // 1 hour ago
  const [events, setEvents] = useState<ActivityEvent[]>([]);

  // Fetch recent changes
  const { data: changes, refetch } = useApi(
    ['changes', lastTimestamp],
    (client) => client.getChanges(lastTimestamp),
    { 
      enabled: true, 
      refetchInterval: isLive ? 5000 : false,
      refetchOnWindowFocus: false
    }
  );

  // Convert changes to activity events
  useEffect(() => {
    if (!changes) return;

    const newEvents: ActivityEvent[] = [];

    // Process new tasks
    changes.new_tasks?.forEach(task => {
      newEvents.push({
        id: `task-${task.id}`,
        type: 'task',
        title: `New task created: ${task.title}`,
        description: `${task.difficulty} ${task.complexity} task for ${task.assigned_role || 'unassigned'}`,
        timestamp: new Date(task.created_at),
        priority: task.complexity === 'major' ? 'high' : 'medium'
      });
    });

    // Process updated tasks
    changes.updated_tasks?.forEach(task => {
      newEvents.push({
        id: `task-update-${task.id}-${task.updated_at}`,
        type: 'task',
        title: `Task #${task.id} status changed to ${task.status}`,
        description: task.title,
        agent: task.assigned_agent_id,
        timestamp: new Date(task.updated_at || task.created_at),
        priority: task.status === 'blocked' ? 'high' : 'low'
      });
    });

    // Process new documents
    changes.new_documents?.forEach(doc => {
      newEvents.push({
        id: `doc-${doc.id}`,
        type: 'document',
        title: `New ${doc.type}: ${doc.title}`,
        description: doc.content.substring(0, 100) + (doc.content.length > 100 ? '...' : ''),
        agent: doc.author_id,
        timestamp: new Date(doc.created_at),
        priority: doc.type === 'issue' ? 'high' : 'medium'
      });
    });

    // Process mentions
    changes.mentions?.forEach(mention => {
      newEvents.push({
        id: `mention-${mention.id}`,
        type: 'mention',
        title: `@${mention.mentioned_agent_id} mentioned`,
        description: `In ${mention.source_type} #${mention.source_id}`,
        timestamp: new Date(mention.created_at),
        priority: 'medium'
      });
    });

    // Process registered agents
    changes.registered_agents?.forEach(agent => {
      newEvents.push({
        id: `agent-${agent.id}-${agent.created_at}`,
        type: 'agent',
        title: `${agent.name || agent.id} joined`,
        description: `${agent.role} (${agent.skill_level || agent.level}) via ${agent.connection_type}`,
        timestamp: new Date(agent.created_at),
        priority: 'low'
      });
    });

    // Update events list (most recent first)
    if (newEvents.length > 0) {
      setEvents(prev => [...newEvents, ...prev].slice(0, 50)); // Keep last 50 events
      if (changes.timestamp) {
        setLastTimestamp(changes.timestamp);
      }
    }
  }, [changes]);

  const handleRefresh = () => {
    refetch();
  };

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Live Activity Feed</CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsLive(!isLive)}
              className={isLive ? 'bg-green-50 text-green-700' : ''}
            >
              {isLive ? <Pause className="h-3 w-3" /> : <RefreshCw className="h-3 w-3" />}
            </Button>
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="h-3 w-3" />
            </Button>
          </div>
        </div>
        
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          {isLive ? (
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span>LIVE • Updates every 5 seconds</span>
            </div>
          ) : (
            <span>Feed paused</span>
          )}
          <span>{events.length} events</span>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="space-y-3">
            {events.length > 0 ? (
              events.map((event) => (
                <ActivityEventCard key={event.id} event={event} />
              ))
            ) : (
              <div className="text-center py-8">
                <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No recent activity</p>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="mt-2"
                  onClick={handleRefresh}
                >
                  Refresh
                </Button>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}