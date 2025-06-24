'use client';

import { useState } from 'react';
import { Task, TaskStatus, TaskDifficulty, TaskComplexity } from '@/lib/types';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { 
  User, 
  Clock, 
  GitBranch, 
  Flag, 
  Calendar, 
  FileText,
  MessageSquare,
  ExternalLink
} from 'lucide-react';
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';

interface TaskDetailModalProps {
  task: Task | null;
  isOpen: boolean;
  onClose: () => void;
}

const ROLE_COLORS = {
  frontend_dev: 'bg-blue-500 text-white',
  backend_dev: 'bg-green-500 text-white',
  qa: 'bg-purple-500 text-white',
  architect: 'bg-orange-500 text-white',
  pm: 'bg-red-500 text-white'
};

const DIFFICULTY_COLORS = {
  [TaskDifficulty.Junior]: 'bg-green-500 text-white',
  [TaskDifficulty.Senior]: 'bg-yellow-500 text-white',
  [TaskDifficulty.Principal]: 'bg-red-500 text-white'
};

const COMPLEXITY_COLORS = {
  [TaskComplexity.Minor]: 'bg-blue-500 text-white',
  [TaskComplexity.Major]: 'bg-orange-500 text-white'
};

const STATUS_COLORS = {
  [TaskStatus.Created]: 'bg-slate-100 text-slate-700',
  [TaskStatus.UnderWork]: 'bg-blue-100 text-blue-700',
  [TaskStatus.DevDone]: 'bg-green-100 text-green-700',
  [TaskStatus.QADone]: 'bg-purple-100 text-purple-700',
  [TaskStatus.DocumentationDone]: 'bg-orange-100 text-orange-700',
  [TaskStatus.Committed]: 'bg-emerald-100 text-emerald-700'
};

export function TaskDetailModal({ task, isOpen, onClose }: TaskDetailModalProps) {
  if (!task) return null;

  const getTaskIcon = (title: string) => {
    const lower = title.toLowerCase();
    if (lower.includes('navigation') || lower.includes('ui')) return '🎨';
    if (lower.includes('login') || lower.includes('auth')) return '🔐';
    if (lower.includes('profile') || lower.includes('user')) return '👤';
    if (lower.includes('payment') || lower.includes('webhook')) return '💳';
    if (lower.includes('shopping') || lower.includes('cart')) return '🛒';
    if (lower.includes('database') || lower.includes('migration')) return '🗄️';
    if (lower.includes('search') || lower.includes('filter')) return '🔍';
    if (lower.includes('analytics') || lower.includes('dashboard')) return '📊';
    if (lower.includes('email') || lower.includes('template')) return '📧';
    if (lower.includes('error') || lower.includes('handling')) return '🔧';
    if (lower.includes('mobile') || lower.includes('responsive')) return '📱';
    if (lower.includes('test') || lower.includes('unit')) return '🧪';
    if (lower.includes('homepage') || lower.includes('home')) return '🏠';
    return '📋';
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <span className="text-2xl">{getTaskIcon(task.title)}</span>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span>Task #{task.id}</span>
                <Badge className={STATUS_COLORS[task.status]}>
                  {task.status.replace('_', ' ')}
                </Badge>
              </div>
            </div>
          </DialogTitle>
          <div className="text-xl font-semibold text-foreground mt-2">{task.title}</div>
        </DialogHeader>

        <div className="space-y-6">
          {/* Metadata Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Task Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {task.target_role && (
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Role:</span>
                    <Badge className={`text-xs ${ROLE_COLORS[task.target_role] || 'bg-gray-500 text-white'}`}>
                      {task.target_role.replace('_', ' ')}
                    </Badge>
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <Flag className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Difficulty:</span>
                  <Badge className={`text-xs ${DIFFICULTY_COLORS[task.difficulty]}`}>
                    {task.difficulty.toUpperCase()}
                  </Badge>
                </div>

                <div className="flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Complexity:</span>
                  <Badge className={`text-xs ${COMPLEXITY_COLORS[task.complexity]}`}>
                    {task.complexity.toUpperCase()}
                  </Badge>
                </div>

                {task.assigned_agent_id && (
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Assigned:</span>
                    <Badge variant="outline" className="text-xs">
                      {task.assigned_agent_id}
                    </Badge>
                  </div>
                )}

                {task.locked_by && (
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Locked by:</span>
                    <Badge variant="outline" className="text-xs">
                      {task.locked_by}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Timeline</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {task.created_at && (
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Created:</span>
                    <span className="text-sm">
                      {format(new Date(task.created_at), 'MMM dd, yyyy HH:mm')}
                    </span>
                  </div>
                )}

                {task.updated_at && (
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Updated:</span>
                    <span className="text-sm">
                      {format(new Date(task.updated_at), 'MMM dd, yyyy HH:mm')}
                    </span>
                  </div>
                )}

                {task.started_at && (
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Started:</span>
                    <span className="text-sm">
                      {format(new Date(task.started_at), 'MMM dd, yyyy HH:mm')}
                    </span>
                  </div>
                )}

                {task.completed_at && (
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Completed:</span>
                    <span className="text-sm">
                      {format(new Date(task.completed_at), 'MMM dd, yyyy HH:mm')}
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Description Section */}
          {task.description && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Description
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{task.description}</ReactMarkdown>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Git Information */}
          {(task.git_branch || task.pr_url) && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <GitBranch className="h-4 w-4" />
                  Git Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {task.git_branch && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Branch:</span>
                    <Badge variant="outline" className="font-mono text-xs">
                      {task.git_branch}
                    </Badge>
                  </div>
                )}

                {task.pr_url && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Pull Request:</span>
                    <Button variant="link" size="sm" className="p-0 h-auto" asChild>
                      <a href={task.pr_url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-3 w-3 mr-1" />
                        View PR
                      </a>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Comments Section - Placeholder for future implementation */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                Comments
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Comments feature coming soon</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-end pt-4">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}