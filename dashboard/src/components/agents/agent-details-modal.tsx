'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  User, Clock, CheckCircle, MessageSquare, Star, Zap, 
  Activity, Calendar, TrendingUp, Award, Code, Target,
  GitBranch, FileText, Users, BrainCircuit
} from 'lucide-react';
import { Agent, AgentRole, SkillLevel, ConnectionType } from '@/lib/types';
import { format, formatDistanceToNow } from 'date-fns';

interface AgentDetailsModalProps {
  agent: Agent | null;
  isOpen: boolean;
  onClose: () => void;
}

export function AgentDetailsModal({ agent, isOpen, onClose }: AgentDetailsModalProps) {
  if (!agent) return null;

  const skillLevel = agent.level || agent.skill_level || SkillLevel.Junior;
  const isOnline = agent.last_seen && 
    new Date().getTime() - new Date(agent.last_seen).getTime() < 5 * 60 * 1000;

  // Mock data for demonstration - in real app this would come from API
  const mockStats = {
    tasksCompleted: Math.floor(Math.random() * 50) + 10,
    tasksInProgress: Math.floor(Math.random() * 5) + 1,
    totalContributions: Math.floor(Math.random() * 200) + 50,
    avgCompletionTime: `${Math.floor(Math.random() * 8) + 2}h`,
    qualityScore: Math.floor(Math.random() * 20) + 80,
    collaborationScore: Math.floor(Math.random() * 30) + 70,
    codeReviews: Math.floor(Math.random() * 20) + 5,
    mentoringSessions: Math.floor(Math.random() * 10),
    specialties: getSpecialtiesByRole(agent.role),
    recentTraining: 'Advanced React Patterns, TypeScript Best Practices',
    joinedDate: '2024-11-15',
    totalWorkTime: `${Math.floor(Math.random() * 200) + 100}h`,
    weeklyHours: `${Math.floor(Math.random() * 20) + 25}h`,
    recentProjects: [
      'User Authentication System',
      'Payment Gateway Integration', 
      'Mobile App Redesign'
    ]
  };

  function getSpecialtiesByRole(role: AgentRole): string[] {
    switch (role) {
      case AgentRole.FrontendDev:
        return ['React', 'TypeScript', 'UI/UX', 'Responsive Design'];
      case AgentRole.BackendDev:
        return ['Node.js', 'Python', 'Database Design', 'API Development'];
      case AgentRole.QA:
        return ['Test Automation', 'Performance Testing', 'Bug Analysis'];
      case AgentRole.Architect:
        return ['System Design', 'Microservices', 'Cloud Architecture'];
      case AgentRole.PM:
        return ['Agile', 'Stakeholder Management', 'Risk Assessment'];
      default:
        return ['Software Development'];
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold">
              {agent.name ? agent.name.charAt(0).toUpperCase() : agent.agent_id.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="text-2xl font-bold">{agent.name || agent.agent_id}</h2>
              <div className="flex items-center gap-2 text-muted-foreground">
                <Badge variant={isOnline ? "default" : "secondary"}>
                  {isOnline ? "ONLINE" : "OFFLINE"}
                </Badge>
                <Badge variant="outline">
                  {skillLevel.toUpperCase()} {agent.role.replace('_', ' ').toUpperCase()}
                </Badge>
                <Badge variant="outline" className="flex items-center gap-1">
                  {agent.connection_type === ConnectionType.MCP ? 
                    <BrainCircuit className="h-3 w-3" /> : 
                    <Users className="h-3 w-3" />
                  }
                  {agent.connection_type.toUpperCase()}
                </Badge>
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
                  <CardTitle className="text-sm">Tasks Completed</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">{mockStats.tasksCompleted}</div>
                  <p className="text-xs text-muted-foreground">+{Math.floor(Math.random() * 5) + 1} this week</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Active Tasks</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-600">{mockStats.tasksInProgress}</div>
                  <p className="text-xs text-muted-foreground">Currently working on</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Quality Score</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-purple-600">{mockStats.qualityScore}%</div>
                  <p className="text-xs text-muted-foreground">Above team average</p>
                </CardContent>
              </Card>
            </div>

            {agent.current_task_id && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-4 w-4" />
                    Current Task
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Task #{agent.current_task_id}</span>
                      <Badge variant="outline">In Progress</Badge>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>Progress</span>
                        <span>{Math.floor(Math.random() * 60) + 30}%</span>
                      </div>
                      <Progress value={Math.floor(Math.random() * 60) + 30} />
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Working for: {Math.floor(Math.random() * 8) + 1}h {Math.floor(Math.random() * 60)}m
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

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
                    <span className="text-muted-foreground">Joined:</span>
                    <div className="font-medium">{format(new Date(mockStats.joinedDate), 'MMM d, yyyy')}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Total Work Time:</span>
                    <div className="font-medium">{mockStats.totalWorkTime}</div>
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
                    <span className="text-muted-foreground">Weekly Hours:</span>
                    <div className="font-medium">{mockStats.weeklyHours}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="performance" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    Performance Metrics
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Quality Score</span>
                      <span className="font-medium">{mockStats.qualityScore}%</span>
                    </div>
                    <Progress value={mockStats.qualityScore} />
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Collaboration</span>
                      <span className="font-medium">{mockStats.collaborationScore}%</span>
                    </div>
                    <Progress value={mockStats.collaborationScore} />
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Delivery Speed</span>
                      <span className="font-medium">92%</span>
                    </div>
                    <Progress value={92} />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Award className="h-4 w-4" />
                    Achievements
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-2 p-2 bg-green-50 rounded">
                    <Star className="h-4 w-4 text-yellow-500" />
                    <span className="text-sm">Top Performer (This Month)</span>
                  </div>
                  <div className="flex items-center gap-2 p-2 bg-blue-50 rounded">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="text-sm">Zero Bug Rate (2 weeks)</span>
                  </div>
                  <div className="flex items-center gap-2 p-2 bg-purple-50 rounded">
                    <Users className="h-4 w-4 text-purple-500" />
                    <span className="text-sm">Team Collaborator</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Recent Projects</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {mockStats.recentProjects.map((project, index) => (
                    <div key={index} className="flex items-center gap-2 p-2 border rounded">
                      <GitBranch className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">{project}</span>
                      <Badge variant="outline" className="ml-auto">Completed</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="activity" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Code Reviews</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{mockStats.codeReviews}</div>
                  <p className="text-xs text-muted-foreground">This month</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Contributions</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{mockStats.totalContributions}</div>
                  <p className="text-xs text-muted-foreground">Total commits</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Avg. Completion</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{mockStats.avgCompletionTime}</div>
                  <p className="text-xs text-muted-foreground">Per task</p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  Recent Activity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex items-center gap-2 p-2 border-l-2 border-green-500">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Completed task "Login API Validation"</span>
                    <span className="text-muted-foreground ml-auto">2 hours ago</span>
                  </div>
                  <div className="flex items-center gap-2 p-2 border-l-2 border-blue-500">
                    <MessageSquare className="h-4 w-4 text-blue-500" />
                    <span>Commented on "Password Reset Flow"</span>
                    <span className="text-muted-foreground ml-auto">4 hours ago</span>
                  </div>
                  <div className="flex items-center gap-2 p-2 border-l-2 border-purple-500">
                    <FileText className="h-4 w-4 text-purple-500" />
                    <span>Created document "API Security Guidelines"</span>
                    <span className="text-muted-foreground ml-auto">1 day ago</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="skills" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  Technical Specialties
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {mockStats.specialties.map((specialty, index) => (
                    <Badge key={index} variant="secondary">{specialty}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent Training</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{mockStats.recentTraining}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Mentoring & Leadership</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Mentoring Sessions</span>
                  <span className="font-medium">{mockStats.mentoringSessions}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Knowledge Sharing</span>
                  <Badge variant="outline">Active</Badge>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={onClose}>Close</Button>
          <Button variant="outline">Send Message</Button>
          <Button variant="outline">Assign Task</Button>
          <Button>View Full Profile</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}