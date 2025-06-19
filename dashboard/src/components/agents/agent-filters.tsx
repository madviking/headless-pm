'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Search, Filter, X, Users, Wifi, WifiOff } from 'lucide-react';
import { AgentRole, SkillLevel, ConnectionType } from '@/lib/types';

interface AgentFiltersProps {
  onFiltersChange: (filters: AgentFilters) => void;
}

export interface AgentFilters {
  search: string;
  role: AgentRole | 'all';
  skillLevel: SkillLevel | 'all';
  connectionType: ConnectionType | 'all';
  status: 'all' | 'online' | 'offline' | 'working';
}

export function AgentFilters({ onFiltersChange }: AgentFiltersProps) {
  const [filters, setFilters] = useState<AgentFilters>({
    search: '',
    role: 'all',
    skillLevel: 'all',
    connectionType: 'all',
    status: 'all'
  });

  const updateFilter = (key: keyof AgentFilters, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const clearFilters = () => {
    const clearedFilters: AgentFilters = {
      search: '',
      role: 'all',
      skillLevel: 'all',
      connectionType: 'all',
      status: 'all'
    };
    setFilters(clearedFilters);
    onFiltersChange(clearedFilters);
  };

  const hasActiveFilters = filters.search !== '' || 
    filters.role !== 'all' || 
    filters.skillLevel !== 'all' || 
    filters.connectionType !== 'all' || 
    filters.status !== 'all';

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Filter className="h-4 w-4" />
          Filter Agents
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="h-3 w-3 mr-1" />
              Clear
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="Search agents by name or ID..."
            value={filters.search}
            onChange={(e) => updateFilter('search', e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Quick Status Filters */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Status</label>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={filters.status === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => updateFilter('status', 'all')}
              className="flex items-center gap-1"
            >
              <Users className="h-3 w-3" />
              All
            </Button>
            <Button
              variant={filters.status === 'online' ? 'default' : 'outline'}
              size="sm"
              onClick={() => updateFilter('status', 'online')}
              className="flex items-center gap-1"
            >
              <Wifi className="h-3 w-3" />
              Online
            </Button>
            <Button
              variant={filters.status === 'offline' ? 'default' : 'outline'}
              size="sm"
              onClick={() => updateFilter('status', 'offline')}
              className="flex items-center gap-1"
            >
              <WifiOff className="h-3 w-3" />
              Offline
            </Button>
            <Button
              variant={filters.status === 'working' ? 'default' : 'outline'}
              size="sm"
              onClick={() => updateFilter('status', 'working')}
              className="flex items-center gap-1"
            >
              Working
            </Button>
          </div>
        </div>

        {/* Dropdown Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Role</label>
            <Select value={filters.role} onValueChange={(value) => updateFilter('role', value)}>
              <SelectTrigger>
                <SelectValue placeholder="All roles" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value={AgentRole.FrontendDev}>Frontend Developer</SelectItem>
                <SelectItem value={AgentRole.BackendDev}>Backend Developer</SelectItem>
                <SelectItem value={AgentRole.QA}>QA Engineer</SelectItem>
                <SelectItem value={AgentRole.Architect}>Architect</SelectItem>
                <SelectItem value={AgentRole.PM}>Project Manager</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Skill Level</label>
            <Select value={filters.skillLevel} onValueChange={(value) => updateFilter('skillLevel', value)}>
              <SelectTrigger>
                <SelectValue placeholder="All levels" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value={SkillLevel.Junior}>Junior</SelectItem>
                <SelectItem value={SkillLevel.Senior}>Senior</SelectItem>
                <SelectItem value={SkillLevel.Principal}>Principal</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Connection</label>
            <Select value={filters.connectionType} onValueChange={(value) => updateFilter('connectionType', value)}>
              <SelectTrigger>
                <SelectValue placeholder="All connections" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Connections</SelectItem>
                <SelectItem value={ConnectionType.Client}>Client</SelectItem>
                <SelectItem value={ConnectionType.MCP}>MCP</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Active Filters Display */}
        {hasActiveFilters && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Active Filters:</label>
            <div className="flex flex-wrap gap-2">
              {filters.search && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  Search: "{filters.search}"
                  <X 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => updateFilter('search', '')}
                  />
                </Badge>
              )}
              {filters.role !== 'all' && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  Role: {filters.role.replace('_', ' ')}
                  <X 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => updateFilter('role', 'all')}
                  />
                </Badge>
              )}
              {filters.skillLevel !== 'all' && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  Level: {filters.skillLevel}
                  <X 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => updateFilter('skillLevel', 'all')}
                  />
                </Badge>
              )}
              {filters.connectionType !== 'all' && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  Connection: {filters.connectionType}
                  <X 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => updateFilter('connectionType', 'all')}
                  />
                </Badge>
              )}
              {filters.status !== 'all' && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  Status: {filters.status}
                  <X 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => updateFilter('status', 'all')}
                  />
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}