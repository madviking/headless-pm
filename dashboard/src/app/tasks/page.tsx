'use client';

import { useState } from 'react';
import { PageLayout } from '@/components/layout/page-layout';
import { TaskBoard } from '@/components/tasks/task-board-merged';
import { TaskFilters, type TaskFilters as TaskFiltersType } from '@/components/tasks/task-filters';
import { TaskStats } from '@/components/tasks/task-stats';
import { TaskTimeline } from '@/components/tasks/task-timeline';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LayoutGrid, Calendar, BarChart3 } from 'lucide-react';

export default function TasksPage() {
  const [view, setView] = useState<'board' | 'timeline' | 'analytics'>('board');
  const [filters, setFilters] = useState<TaskFiltersType>({});

  return (
    <PageLayout fullWidth={view === 'board'}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Task Management</h1>
          <Tabs
            value={view}
            onValueChange={(value) => {
              if (value === 'board' || value === 'timeline' || value === 'analytics') {
                setView(value);
              }
            }}
            className="w-auto"
          >
            <TabsList>
              <TabsTrigger value="board" className="flex items-center gap-2">
                <LayoutGrid className="h-4 w-4" />
                Board
              </TabsTrigger>
              <TabsTrigger value="timeline" className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Timeline
              </TabsTrigger>
              <TabsTrigger value="analytics" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Analytics
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <TaskFilters onFiltersChange={setFilters} />
        
        <div className="min-h-[600px]">
          {view === 'board' && <TaskBoard filters={filters} />}
          {view === 'timeline' && <TaskTimeline filters={filters} />}
          {view === 'analytics' && <TaskStats filters={filters} />}
        </div>
      </div>
    </PageLayout>
  );
}
