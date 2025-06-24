'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Task, TaskStatus } from '@/lib/types';
import { useTasks, useUpdateTaskStatus, useAgents } from '@/lib/hooks/useApi';

const TASK_STATUSES = [
  { key: TaskStatus.Created, label: 'CREATED', color: 'bg-slate-100 text-slate-700' },
  { key: TaskStatus.UnderWork, label: 'UNDER WORK', color: 'bg-blue-100 text-blue-700' },
  { key: TaskStatus.DevDone, label: 'DEV DONE', color: 'bg-green-100 text-green-700' },
  { key: TaskStatus.QADone, label: 'QA DONE', color: 'bg-purple-100 text-purple-700' },
  { key: TaskStatus.DocumentationDone, label: 'DOCS DONE', color: 'bg-orange-100 text-orange-700' },
  { key: TaskStatus.Committed, label: 'COMMITTED', color: 'bg-emerald-100 text-emerald-700' }
];

export function SimpleTaskBoard() {
  const { data: tasks = [], isLoading, refetch } = useTasks();
  const { data: agents = [] } = useAgents();
  const updateTaskStatus = useUpdateTaskStatus();
  
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [draggedTask, setDraggedTask] = useState<Task | null>(null);
  const [dragOverStatus, setDragOverStatus] = useState<TaskStatus | null>(null);

  // Load agent ID from localStorage
  useEffect(() => {
    const storedId = localStorage.getItem('agent_id');
    if (storedId) setSelectedAgentId(storedId);
  }, []);

  // Save agent ID to localStorage
  useEffect(() => {
    if (selectedAgentId) {
      localStorage.setItem('agent_id', selectedAgentId);
    }
  }, [selectedAgentId]);

  const handleDragStart = (e: React.DragEvent, task: Task) => {
    setDraggedTask(task);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, status: TaskStatus) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverStatus(status);
  };

  const handleDragLeave = () => {
    setDragOverStatus(null);
  };

  const handleDrop = async (e: React.DragEvent, newStatus: TaskStatus) => {
    e.preventDefault();
    setDragOverStatus(null);

    if (!draggedTask || !selectedAgentId) {
      alert('Please select an agent to move tasks');
      return;
    }

    if (draggedTask.status === newStatus) {
      return; // No change needed
    }

    try {
      await updateTaskStatus.mutateAsync({
        taskId: draggedTask.id,
        status: newStatus,
        agentId: selectedAgentId
      });
      refetch(); // Refresh the task list
    } catch (error) {
      console.error('Failed to update task status:', error);
      alert('Failed to update task status');
    }
  };

  const getTasksByStatus = (status: TaskStatus) => 
    tasks.filter(task => task.status === status);

  if (isLoading) {
    return <div>Loading tasks...</div>;
  }

  return (
    <div className="space-y-4">
      {/* Agent Selector */}
      <div className="flex items-center gap-2 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <span className="text-sm font-medium">Acting as Agent:</span>
        <select 
          value={selectedAgentId} 
          onChange={(e) => setSelectedAgentId(e.target.value)}
          className="px-3 py-1 border rounded-md text-sm"
        >
          <option value="">Select an agent...</option>
          {agents?.map(agent => (
            <option key={agent.id} value={agent.agent_id}>
              {agent.name || agent.agent_id} ({agent.role})
            </option>
          ))}
        </select>
        {!selectedAgentId && (
          <span className="text-xs text-amber-600">⚠️ Select an agent to move tasks</span>
        )}
      </div>

      {/* Task Board */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {TASK_STATUSES.map(({ key: status, label, color }) => (
          <div key={status} className="flex-1 min-w-[250px]">
            <Card 
              className={`h-full ${dragOverStatus === status ? 'ring-2 ring-blue-400 bg-blue-50/20' : ''}`}
              onDragOver={(e) => handleDragOver(e, status)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, status)}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">
                  <span className={`px-2 py-1 rounded-md ${color}`}>
                    {label} ({getTasksByStatus(status).length})
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 min-h-[400px]">
                  {getTasksByStatus(status).map(task => (
                    <Card
                      key={task.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, task)}
                      className="cursor-move hover:shadow-md transition-shadow"
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium">#{task.id}</span>
                          <Badge variant="outline" className="text-xs">
                            {task.difficulty}
                          </Badge>
                        </div>
                        <h4 className="font-medium text-sm">{task.title}</h4>
                        {task.assigned_agent_id && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Assigned: {task.assigned_agent_id}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        ))}
      </div>
    </div>
  );
}