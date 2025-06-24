'use client';

import { useState, useEffect } from 'react';
import { TaskBoard } from './task-board';
import { SimpleTaskBoard } from './task-board-simple';
import { TaskFilters } from './task-filters';
import { Button } from '@/components/ui/button';
import { Info } from 'lucide-react';

export function TaskBoardWrapper({ filters = {} }: { filters?: TaskFilters }) {
  const [useSimpleDnd, setUseSimpleDnd] = useState(false);
  const [hasError, setHasError] = useState(false);

  // Check if @dnd-kit is working properly
  useEffect(() => {
    // Check for React 19 compatibility issues
    const reactVersion = parseInt(require('react').version.split('.')[0]);
    if (reactVersion >= 19) {
      console.warn('React 19 detected - may have compatibility issues with @dnd-kit');
    }
  }, []);

  if (hasError || useSimpleDnd) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between bg-amber-50 border border-amber-200 rounded-lg p-3">
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-amber-600" />
            <span className="text-sm text-amber-700">
              Using native HTML5 drag and drop due to compatibility issues
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setUseSimpleDnd(false);
              setHasError(false);
            }}
          >
            Try @dnd-kit again
          </Button>
        </div>
        <SimpleTaskBoard filters={filters} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-end">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setUseSimpleDnd(true)}
          className="text-xs text-muted-foreground"
        >
          Switch to simple drag & drop
        </Button>
      </div>
      <div
        onError={() => {
          console.error('Error in TaskBoard component, switching to simple implementation');
          setHasError(true);
        }}
      >
        <TaskBoard filters={filters} />
      </div>
    </div>
  );
}