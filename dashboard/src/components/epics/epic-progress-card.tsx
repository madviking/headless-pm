import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Epic, TaskStatus } from '@/lib/types';
import { Users, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

interface EpicProgressCardProps {
  epic: Epic;
}

export function EpicProgressCard({ epic }: EpicProgressCardProps) {
  const totalTasks = epic.task_count || 0;
  const completedTasks = epic.completed_task_count || 0;
  const inProgressTasks = epic.in_progress_task_count || 0;
  const progressPercentage = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

  const getStatusColor = (percentage: number) => {
    if (percentage === 100) return 'text-green-600';
    if (percentage > 75) return 'text-blue-600';
    if (percentage > 50) return 'text-yellow-600';
    return 'text-gray-600';
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{epic.name}</CardTitle>
            <CardDescription className="mt-1">
              {epic.description || 'No description provided'}
            </CardDescription>
          </div>
          <Badge variant="secondary" className="ml-2">
            Epic #{epic.id}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Progress</span>
            <span className={`font-medium ${getStatusColor(progressPercentage)}`}>
              {progressPercentage.toFixed(0)}%
            </span>
          </div>
          <Progress value={progressPercentage} className="h-2" />
        </div>

        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="space-y-1">
            <div className="flex items-center justify-center text-muted-foreground">
              <Clock className="h-4 w-4 mr-1" />
            </div>
            <div className="text-2xl font-bold">{totalTasks}</div>
            <div className="text-xs text-muted-foreground">Total</div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-center text-yellow-600">
              <AlertCircle className="h-4 w-4 mr-1" />
            </div>
            <div className="text-2xl font-bold">{inProgressTasks}</div>
            <div className="text-xs text-muted-foreground">In Progress</div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-center text-green-600">
              <CheckCircle2 className="h-4 w-4 mr-1" />
            </div>
            <div className="text-2xl font-bold">{completedTasks}</div>
            <div className="text-xs text-muted-foreground">Completed</div>
          </div>
        </div>

        {epic.features && epic.features.length > 0 && (
          <div className="pt-2 border-t">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground flex items-center">
                <Users className="h-3 w-3 mr-1" />
                {epic.features.length} Features
              </span>
              {epic.pm_id && (
                <div className="flex items-center gap-1">
                  <span className="text-xs text-muted-foreground">PM:</span>
                  <Avatar className="h-5 w-5">
                    <AvatarFallback className="text-xs">
                      {epic.pm_id.slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}