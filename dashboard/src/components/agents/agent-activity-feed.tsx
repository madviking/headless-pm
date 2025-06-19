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
  Settings,
  RefreshCw
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface ActivityEvent {
  id: string;
  type: 'task_moved' | 'task_started' | 'task_completed' | 'agent_joined' | 'agent_offline' | 'comment_added' | 'service_alert';
  title: string;
  description: string;
  agent?: string;
  timestamp: Date;
  priority: 'high' | 'medium' | 'low';
  metadata?: Record<string, any>;
}

// Mock activity events - in a real app, this would come from an API
const generateMockEvents = (): ActivityEvent[] => {
  const events: ActivityEvent[] = [
    {
      id: '1',
      type: 'task_moved',
      title: 'Task #789 moved to QA_DONE',
      description: 'Fixed validation issues, ready for deployment',
      agent: 'qa_senior_001',
      timestamp: new Date(Date.now() - 1000 * 30), // 30 seconds ago
      priority: 'medium',
      metadata: { taskId: 789, fromStatus: 'DEV_DONE', toStatus: 'QA_DONE' }
    },
    {
      id: '2',
      type: 'comment_added',
      title: 'New document: "API Security Guidelines"',
      description: '@backend_dev_001 @backend_dev_002 mentioned',
      agent: 'architect_001',
      timestamp: new Date(Date.now() - 1000 * 60 * 2), // 2 minutes ago
      priority: 'high',
      metadata: { documentType: 'Documentation', securityReview: true }
    },
    {
      id: '3',
      type: 'task_completed',
      title: 'Epic "User Authentication" reached 85% completion',
      description: 'Milestone achieved • On track for Dec 20 deadline',
      timestamp: new Date(Date.now() - 1000 * 60 * 3), // 3 minutes ago
      priority: 'medium',
      metadata: { epicName: 'User Authentication', completion: 85 }
    },
    {
      id: '4',
      type: 'service_alert',
      title: 'Service alert: email-service response time > 1s',
      description: 'Current: 1.2s average • Target: <500ms',
      agent: 'backend_dev_003',
      timestamp: new Date(Date.now() - 1000 * 60 * 5), // 5 minutes ago
      priority: 'high',
      metadata: { service: 'email-service', responseTime: 1.2, target: 0.5 }
    },
    {
      id: '5',
      type: 'task_started',
      title: 'Agent frontend_dev_001 started working on task #801',
      description: 'Task locked • "Navigation Redesign"',
      agent: 'frontend_dev_001',
      timestamp: new Date(Date.now() - 1000 * 60 * 8), // 8 minutes ago
      priority: 'low',
      metadata: { taskId: 801, taskName: 'Navigation Redesign', complexity: 'Major' }
    },
    {
      id: '6',
      type: 'task_completed',
      title: 'QA testing completed for task #756',
      description: 'All tests passed, ready for production',
      agent: 'qa_senior_001',
      timestamp: new Date(Date.now() - 1000 * 60 * 12), // 12 minutes ago
      priority: 'medium',
      metadata: { taskId: 756, component: 'User Profile Component' }
    },
    {
      id: '7',
      type: 'agent_offline',
      title: 'Service monitoring-agent went offline',
      description: 'Impact: Health monitoring unavailable',
      timestamp: new Date(Date.now() - 1000 * 60 * 15), // 15 minutes ago
      priority: 'high',
      metadata: { service: 'monitoring-agent', impact: 'Health monitoring unavailable' }
    }
  ];

  return events;
};

const getEventIcon = (type: ActivityEvent['type']) => {
  switch (type) {
    case 'task_moved':
      return <GitBranch className="h-4 w-4" />;
    case 'task_started':
      return <Clock className="h-4 w-4" />;
    case 'task_completed':
      return <CheckCircle className="h-4 w-4" />;
    case 'agent_joined':
      return <Users className="h-4 w-4" />;
    case 'agent_offline':
      return <AlertTriangle className="h-4 w-4" />;
    case 'comment_added':
      return <MessageSquare className="h-4 w-4" />;
    case 'service_alert':
      return <AlertTriangle className="h-4 w-4" />;
    default:
      return <Activity className="h-4 w-4" />;
  }
};

const getPriorityColor = (priority: ActivityEvent['priority']) => {
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
};

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
            👤 {event.agent}
          </p>
        )}
      </div>
    </div>
  );
}

export function AgentActivityFeed() {
  // Use static initial events to prevent infinite re-renders
  const [events] = useState<ActivityEvent[]>(() => generateMockEvents());
  const [isLive, setIsLive] = useState(false); // Start with live updates disabled
  const [eventsPerMinute] = useState(15); // Mock statistic

  // Removed the problematic useEffect that was causing infinite loops
  // Real-time updates can be added later with proper dependency management

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
            <Button variant="outline" size="sm">
              <Settings className="h-3 w-3" />
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
          <span>📊 {eventsPerMinute} events/minute</span>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="space-y-3">
            {events.map((event) => (
              <ActivityEventCard key={event.id} event={event} />
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}