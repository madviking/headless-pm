'use client';

import { useState } from 'react';
import { PageLayout } from '@/components/layout/page-layout';
import { AgentGrid } from '@/components/agents/agent-grid';
import { AgentStats } from '@/components/agents/agent-stats';
import { AgentActivityFeed } from '@/components/agents/agent-activity-feed-real';
import { AgentFilters, AgentFilters as AgentFiltersType } from '@/components/agents/agent-filters';

export default function AgentsPage() {
  const [filters, setFilters] = useState<AgentFiltersType>({
    search: '',
    role: 'all',
    skillLevel: 'all',
    connectionType: 'all',
    status: 'all'
  });

  return (
    <PageLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Agent Activity</h1>
        </div>

        <AgentStats />
        
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <AgentFilters onFiltersChange={setFilters} />
          </div>
          <div className="lg:col-span-2">
            <AgentGrid filters={filters} />
          </div>
          <div className="lg:col-span-1">
            <AgentActivityFeed />
          </div>
        </div>
      </div>
    </PageLayout>
  );
}