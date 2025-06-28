import axios, { AxiosInstance } from 'axios';
import { 
  Agent, Epic, Feature, Task, TaskComment, Document, 
  Mention, Service, ProjectContext, Changes,
  TaskStatus, AgentRole, SkillLevel, DocumentType
} from '@/lib/types';

export class HeadlessPMClient {
  private client: AxiosInstance;

  constructor(baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:6969', apiKey?: string) {
    const apiKeyToUse = apiKey || process.env.NEXT_PUBLIC_API_KEY;
    this.client = axios.create({
      baseURL: `${baseURL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
        ...(apiKeyToUse && { 'X-API-Key': apiKeyToUse })
      }
    });
  }

  // Agent endpoints
  async registerAgent(agentId: string, role: AgentRole, skillLevel: SkillLevel, name?: string) {
    const { data } = await this.client.post<Agent>('/register', {
      agent_id: agentId,
      role,
      skill_level: skillLevel,
      name
    });
    return data;
  }

  async getAgents() {
    const { data } = await this.client.get<Agent[]>('/agents');
    return data;
  }

  async deleteAgent(agentId: string) {
    await this.client.delete(`/agents/${agentId}`);
  }

  // Epic endpoints
  async getEpics() {
    const { data } = await this.client.get<Epic[]>('/epics');
    return data;
  }

  async createEpic(name: string, description?: string, pmId?: string) {
    const { data } = await this.client.post<Epic>('/epics', {
      name,
      description,
      pm_id: pmId
    });
    return data;
  }

  async deleteEpic(id: number) {
    await this.client.delete(`/epics/${id}`);
  }

  // Feature endpoints
  async getFeatures(epicId?: number) {
    const url = epicId ? `/features/${epicId}` : '/features';
    const { data } = await this.client.get<Feature[]>(url);
    return data;
  }

  async createFeature(epicId: number, name: string, description?: string) {
    const { data } = await this.client.post<Feature>('/features', {
      epic_id: epicId,
      name,
      description
    });
    return data;
  }

  // Task endpoints
  async getTasks() {
    const { data } = await this.client.get<Task[]>('/tasks');
    return data;
  }

  async getTasksByFeature(featureId: number) {
    const { data } = await this.client.get<Task[]>(`/tasks/feature/${featureId}`);
    return data;
  }

  async createTask(task: {
    feature_id: number;
    title: string;
    description?: string;
    assigned_role?: AgentRole;
    difficulty: string;
    complexity: string;
  }) {
    const { data } = await this.client.post<Task>('/tasks/create', task);
    return data;
  }

  async updateTaskStatus(taskId: number, status: TaskStatus, agentId: string) {
    console.log('UpdateTaskStatus called with:', { taskId, status, agentId });
    console.log('Status type:', typeof status);
    console.log('Status value:', JSON.stringify(status));
    
    const url = `/tasks/${taskId}/status?agent_id=${encodeURIComponent(agentId)}`;
    const payload = { status };
    
    console.log('Request URL:', url);
    console.log('Request payload:', JSON.stringify(payload));
    console.log('Full API URL:', `${this.client.defaults.baseURL}${url}`);
    
    try {
      const { data } = await this.client.put<Task>(url, payload);
      console.log('UpdateTaskStatus success:', data);
      return data;
    } catch (error) {
      console.error('UpdateTaskStatus error:', error);
      if (error.response) {
        console.error('Error response data:', error.response.data);
        console.error('Error response status:', error.response.status);
        console.error('Error response headers:', error.response.headers);
      }
      throw error;
    }
  }

  async addTaskComment(taskId: number, agentId: string, content: string) {
    const { data } = await this.client.post<TaskComment>(`/tasks/${taskId}/comment`, {
      agent_id: agentId,
      content
    });
    return data;
  }

  // Document endpoints
  async getDocuments(authorId?: string, type?: DocumentType) {
    const params = new URLSearchParams();
    if (authorId) params.append('author_id', authorId);
    if (type) params.append('type', type);
    
    const { data } = await this.client.get<Document[]>(`/documents?${params.toString()}`);
    return data;
  }

  async getDocument(documentId: number) {
    const { data } = await this.client.get<Document>(`/documents/${documentId}`);
    return data;
  }

  async createDocument(document: {
    type: DocumentType;
    title: string;
    content: string;
    author_id: string;
  }) {
    const { data } = await this.client.post<Document>('/documents', document);
    return data;
  }

  // Mention endpoints
  async getMentions(agentId?: string, unreadOnly = false) {
    const params = new URLSearchParams();
    if (agentId) {
      params.append('agent_id', agentId);
    }
    // Always explicitly set unread_only parameter
    params.append('unread_only', unreadOnly ? 'true' : 'false');
    
    console.log('Fetching mentions with params:', params.toString());
    const { data } = await this.client.get<Mention[]>(`/mentions?${params.toString()}`);
    console.log('Mentions response:', data);
    return data;
  }

  async getMentionsByRole(role?: string, unreadOnly = false) {
    const params = new URLSearchParams();
    if (role) {
      params.append('role', role);
    }
    params.append('unread_only', unreadOnly ? 'true' : 'false');
    
    console.log('Fetching mentions by role with params:', params.toString());
    const { data } = await this.client.get<Mention[]>(`/mentions/by-role?${params.toString()}`);
    console.log('Mentions by role response:', data);
    return data;
  }

  async markMentionRead(mentionId: number) {
    await this.client.put(`/mentions/${mentionId}/read`);
  }

  // Service endpoints
  async getServices() {
    const { data } = await this.client.get<Service[]>('/services');
    return data;
  }

  async registerService(service: {
    name: string;
    type: string;
    endpoint_url: string;
    ping_url?: string;
    metadata?: Record<string, any>;
  }) {
    const { data } = await this.client.post<Service>('/services/register', service);
    return data;
  }

  async sendHeartbeat(serviceName: string) {
    await this.client.post(`/services/${serviceName}/heartbeat`);
  }

  // Context and changes
  async getContext() {
    const { data } = await this.client.get<ProjectContext>('/context');
    return data;
  }

  async getChanges(since: number, agentId?: string) {
    const params = new URLSearchParams();
    params.append('since', since.toString());
    if (agentId) params.append('agent_id', agentId);
    
    const { data } = await this.client.get<Changes>(`/changes?${params.toString()}`);
    return data;
  }

  async getChangelog(hours = 24) {
    const { data } = await this.client.get(`/changelog?hours=${hours}`);
    return data;
  }
}