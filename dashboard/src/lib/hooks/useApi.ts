import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import { HeadlessPMClient } from '@/lib/api/client';
import { 
  AgentRole, SkillLevel, TaskStatus, DocumentType,
  Epic, Feature, Task, Agent, Document, Service, Mention
} from '@/lib/types';

// Create a singleton instance of the API client to prevent re-initialization
let apiClientInstance: HeadlessPMClient | null = null;

const getApiClient = () => {
  if (!apiClientInstance) {
    apiClientInstance = new HeadlessPMClient(
      process.env.NEXT_PUBLIC_API_URL,
      process.env.NEXT_PUBLIC_API_KEY
    );
  }
  return apiClientInstance;
};

const apiClient = getApiClient();

// Epic hooks
export const useEpics = () => {
  return useQuery({
    queryKey: ['epics'],
    queryFn: () => apiClient.getEpics(),
    refetchInterval: 30000, // Refetch every 30 seconds
    refetchOnWindowFocus: false // Prevent refetch on window focus
  });
};

export const useCreateEpic = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string; pmId?: string }) => 
      apiClient.createEpic(data.name, data.description, data.pmId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epics'] });
    }
  });
};

// Feature hooks
export const useFeatures = (epicId?: number) => {
  return useQuery({
    queryKey: ['features', epicId],
    queryFn: () => apiClient.getFeatures(epicId),
    enabled: epicId !== undefined
  });
};

// Task hooks
export const useTasks = () => {
  return useQuery({
    queryKey: ['tasks'],
    queryFn: () => apiClient.getTasks(),
    refetchInterval: 10000, // Refetch every 10 seconds
    refetchOnWindowFocus: false // Prevent refetch on window focus
  });
};

export const useTasksByFeature = (featureId: number) => {
  return useQuery({
    queryKey: ['tasks', 'feature', featureId],
    queryFn: () => apiClient.getTasksByFeature(featureId),
    enabled: !!featureId
  });
};

export const useUpdateTaskStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, status, agentId }: { taskId: number; status: TaskStatus; agentId: string }) =>
      apiClient.updateTaskStatus(taskId, status, agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    }
  });
};

// Agent hooks
export const useAgents = () => {
  return useQuery({
    queryKey: ['agents'],
    queryFn: () => apiClient.getAgents(),
    refetchInterval: 30000, // Refetch every 30 seconds (reduced from 5 seconds)
    refetchOnWindowFocus: false,
    staleTime: 10000, // Consider data fresh for 10 seconds
    retry: 1
  });
};

// Document hooks
export const useDocuments = (authorId?: string, type?: DocumentType) => {
  return useQuery({
    queryKey: ['documents', authorId, type],
    queryFn: () => apiClient.getDocuments(authorId, type),
    refetchInterval: 15000,
    refetchOnWindowFocus: false // Prevent refetch on window focus
  });
};

export const useCreateDocument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { type: DocumentType; title: string; content: string; author_id: string }) =>
      apiClient.createDocument(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['mentions'] });
    }
  });
};

// Mention hooks
export const useMentions = (agentId?: string, unreadOnly = false) => {
  console.log('useMentions called with agentId:', agentId);
  return useQuery({
    queryKey: ['mentions', agentId, unreadOnly],
    queryFn: () => apiClient.getMentions(agentId, unreadOnly),
    enabled: true, // Always enabled since API can handle no agent_id
    refetchInterval: 10000,
    refetchOnWindowFocus: false // Prevent refetch on window focus
  });
};

export const useMentionsByRole = (role?: string, unreadOnly = false) => {
  console.log('useMentionsByRole called with role:', role);
  return useQuery({
    queryKey: ['mentions', 'by-role', role, unreadOnly],
    queryFn: () => apiClient.getMentionsByRole(role, unreadOnly),
    enabled: true, // Always enabled since API can handle no role
    refetchInterval: 10000,
    refetchOnWindowFocus: false // Prevent refetch on window focus
  });
};

// Service hooks
export const useServices = () => {
  return useQuery({
    queryKey: ['services'],
    queryFn: () => apiClient.getServices(),
    refetchInterval: 5000, // Frequent refresh for health monitoring
    refetchOnWindowFocus: false // Prevent refetch on window focus
  });
};

// Context hook
export const useProjectContext = () => {
  return useQuery({
    queryKey: ['context'],
    queryFn: () => apiClient.getContext(),
    staleTime: Infinity // Context rarely changes
  });
};

// Changes hook for real-time updates
export const useChanges = (since: number, agentId?: string) => {
  return useQuery({
    queryKey: ['changes', since, agentId],
    queryFn: () => apiClient.getChanges(since, agentId),
    refetchInterval: 3000, // Poll every 3 seconds
    enabled: !!since,
    refetchOnWindowFocus: false // Prevent refetch on window focus
  });
};

// Generic useApi hook for flexible API calls
export const useApi = <T>(
  queryKey: string | readonly unknown[],
  queryFn: (client: HeadlessPMClient) => Promise<T>,
  options?: {
    refetchInterval?: number;
    enabled?: boolean;
    staleTime?: number;
  }
) => {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: Array.isArray(queryKey) ? queryKey : [queryKey],
    queryFn: () => queryFn(apiClient),
    refetchInterval: options?.refetchInterval || false, // Use provided interval or disable
    refetchOnWindowFocus: false,
    enabled: options?.enabled !== false,
    staleTime: options?.staleTime || 30000, // 30 seconds default stale time
    retry: 1,
    retryDelay: 2000
  });

  return {
    data: data as T, // Don't force empty array, let components handle undefined
    isLoading,
    error,
    refetch,
    mutate: refetch
  };
};