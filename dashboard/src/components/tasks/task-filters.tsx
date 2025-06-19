'use client';

import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { Search, X } from 'lucide-react';
import { AgentRole, TaskStatus, TaskDifficulty, TaskComplexity } from '@/lib/types';

interface TaskFiltersProps {
  onFiltersChange?: (filters: TaskFilters) => void;
}

export interface TaskFilters {
  epic?: string;
  role?: AgentRole;
  difficulty?: TaskDifficulty;
  status?: TaskStatus;
  complexity?: TaskComplexity;
  assignee?: string;
  branch?: string;
  search?: string;
}

export function TaskFilters({ onFiltersChange }: TaskFiltersProps) {
  const [filters, setFilters] = useState<TaskFilters>({});

  const updateFilters = useCallback((key: keyof TaskFilters, value: string | undefined) => {
    setFilters(prev => {
      const newFilters = { ...prev };
      if (value && value !== 'all') {
        newFilters[key] = value as any;
      } else {
        delete newFilters[key];
      }
      onFiltersChange?.(newFilters);
      return newFilters;
    });
  }, [onFiltersChange]);

  const clearFilters = useCallback(() => {
    setFilters({});
    onFiltersChange?.({});
  }, [onFiltersChange]);

  const hasActiveFilters = Object.keys(filters).length > 0;

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Label htmlFor="epic-filter" className="text-sm font-medium">
              Epic:
            </Label>
            <Select value={filters.epic || 'all'} onValueChange={(value) => updateFilters('epic', value)}>
              <SelectTrigger id="epic-filter" className="w-[140px]">
                <SelectValue placeholder="All Epics" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Epics</SelectItem>
                <SelectItem value="authentication">Authentication</SelectItem>
                <SelectItem value="payment">Payment System</SelectItem>
                <SelectItem value="admin">Admin Panel</SelectItem>
                <SelectItem value="reporting">Reporting</SelectItem>
                <SelectItem value="mobile">Mobile App</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Label htmlFor="role-filter" className="text-sm font-medium">
              Role:
            </Label>
            <Select value={filters.role || 'all'} onValueChange={(value) => updateFilters('role', value)}>
              <SelectTrigger id="role-filter" className="w-[140px]">
                <SelectValue placeholder="All Roles" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value={AgentRole.FrontendDev}>Frontend Dev</SelectItem>
                <SelectItem value={AgentRole.BackendDev}>Backend Dev</SelectItem>
                <SelectItem value={AgentRole.QA}>QA</SelectItem>
                <SelectItem value={AgentRole.Architect}>Architect</SelectItem>
                <SelectItem value={AgentRole.PM}>PM</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Label htmlFor="difficulty-filter" className="text-sm font-medium">
              Difficulty:
            </Label>
            <Select value={filters.difficulty || 'all'} onValueChange={(value) => updateFilters('difficulty', value)}>
              <SelectTrigger id="difficulty-filter" className="w-[140px]">
                <SelectValue placeholder="All Levels" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value={TaskDifficulty.Junior}>Junior</SelectItem>
                <SelectItem value={TaskDifficulty.Senior}>Senior</SelectItem>
                <SelectItem value={TaskDifficulty.Principal}>Principal</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Label htmlFor="status-filter" className="text-sm font-medium">
              Status:
            </Label>
            <Select value={filters.status || 'all'} onValueChange={(value) => updateFilters('status', value)}>
              <SelectTrigger id="status-filter" className="w-[140px]">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value={TaskStatus.Created}>Created</SelectItem>
                <SelectItem value={TaskStatus.UnderWork}>Under Work</SelectItem>
                <SelectItem value={TaskStatus.DevDone}>Dev Done</SelectItem>
                <SelectItem value={TaskStatus.QADone}>QA Done</SelectItem>
                <SelectItem value={TaskStatus.DocumentationDone}>Documentation Done</SelectItem>
                <SelectItem value={TaskStatus.Committed}>Committed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Label htmlFor="complexity-filter" className="text-sm font-medium">
              Complexity:
            </Label>
            <Select value={filters.complexity || 'all'} onValueChange={(value) => updateFilters('complexity', value)}>
              <SelectTrigger id="complexity-filter" className="w-[140px]">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value={TaskComplexity.Minor}>Minor</SelectItem>
                <SelectItem value={TaskComplexity.Major}>Major</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Label htmlFor="assignee-filter" className="text-sm font-medium">
              Assignee:
            </Label>
            <Select value={filters.assignee || 'all'} onValueChange={(value) => updateFilters('assignee', value)}>
              <SelectTrigger id="assignee-filter" className="w-[140px]">
                <SelectValue placeholder="All Agents" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Agents</SelectItem>
                <SelectItem value="frontend_dev_001">Frontend Dev 001</SelectItem>
                <SelectItem value="backend_dev_002">Backend Dev 002</SelectItem>
                <SelectItem value="qa_senior_001">QA Senior 001</SelectItem>
                <SelectItem value="architect_001">Architect 001</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2 flex-1 min-w-[200px]">
            <Label htmlFor="search-filter" className="text-sm font-medium">
              Search:
            </Label>
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="search-filter"
                placeholder="Search tasks..."
                value={filters.search || ''}
                onChange={(e) => updateFilters('search', e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {hasActiveFilters && (
            <Button
              variant="outline"
              size="sm"
              onClick={clearFilters}
              className="flex items-center gap-2"
            >
              <X className="h-4 w-4" />
              Clear Filters
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}