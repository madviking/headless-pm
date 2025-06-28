// API Types based on Headless PM models

export enum AgentRole {
  FrontendDev = "frontend_dev",
  BackendDev = "backend_dev",
  QA = "qa", 
  Architect = "architect",
  PM = "pm"
}

export enum SkillLevel {
  Junior = "junior",
  Senior = "senior",
  Principal = "principal"
}

export enum ConnectionType {
  Client = "client",
  MCP = "mcp"
}

export enum TaskStatus {
  Created = "created",
  UnderWork = "under_work",
  DevDone = "dev_done",
  QADone = "qa_done",
  DocumentationDone = "documentation_done",
  Committed = "committed",
  // Legacy statuses (deprecated)
  Evaluation = "evaluation",
  Approved = "approved"
}

export enum TaskDifficulty {
  Junior = "junior",
  Senior = "senior",
  Principal = "principal"
}

export enum TaskComplexity {
  Minor = "minor",
  Major = "major"
}

export enum DocumentType {
  Comment = "comment",
  Update = "update",
  Question = "question",
  Announcement = "announcement",
  Decision = "decision",
  Report = "report"
}

export interface Agent {
  id: number;
  agent_id: string;
  role: AgentRole;
  level: SkillLevel; // API uses 'level' not 'skill_level'
  skill_level?: SkillLevel; // Keep for backward compatibility
  name?: string;
  connection_type: ConnectionType;
  created_at?: string;
  last_seen?: string;
  current_task_id?: number;
}

export interface Epic {
  id: number;
  name: string;
  description?: string;
  pm_id?: string;
  created_at: string;
  updated_at?: string;
  task_count?: number;
  completed_task_count?: number;
  in_progress_task_count?: number;
  features?: Feature[];
}

export interface Feature {
  id: number;
  epic_id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  task_count?: number;
  completed_task_count?: number;
  in_progress_task_count?: number;
  tasks?: Task[];
}

export interface Task {
  id: number;
  feature_id: number;
  title: string;
  description?: string;
  target_role: AgentRole;           // Fixed: was assigned_role
  locked_by?: string;               // Fixed: was assigned_agent_id
  difficulty: TaskDifficulty;
  complexity: TaskComplexity;
  status: TaskStatus;
  branch: string;                   // Fixed: was branch_name
  created_by: string;               // Added: missing field
  locked_at?: string;               // Added: missing field
  notes?: string;                   // Added: missing field
  created_at: string;
  updated_at?: string;
  task_type?: string;               // Added: missing field
  poll_interval?: number;           // Added: missing field
  assigned_agent?: Agent;           // Keep for UI convenience
  comments?: TaskComment[];
}

export interface TaskComment {
  id: number;
  task_id: number;
  agent_id: string;
  content: string;
  created_at: string;
  agent?: Agent;
}

export interface Document {
  id: number;
  doc_type: DocumentType;
  title: string;
  content: string;
  author_id: string;
  created_at: string;
  updated_at: string;
  expires_at?: string;
  meta_data?: any;
  mentions: string[]; // Array of mentioned agent IDs
  author?: Agent;
}

export interface Mention {
  id: number;
  document_id?: number;
  task_id?: number;
  task_comment_id?: number;
  mentioned_agent_id: string;
  created_by: string;
  is_read: boolean;
  created_at: string;
  document_title?: string;
  task_title?: string;
  document?: Document;
  task_comment?: TaskComment;
  mentioned_agent?: Agent;
  mentioned_by_agent?: Agent;
}

export interface Service {
  name: string;
  type: string;
  endpoint_url: string;
  ping_url?: string;
  status: "active" | "inactive";
  metadata?: Record<string, any>;
  last_heartbeat?: string;
  created_at: string;
}

export interface ProjectContext {
  project_name: string;
  project_description: string;
  git_repo: string;
  main_branch: string;
  services_dir: string;
  current_sprint?: string;
  tech_stack?: string[];
}

export interface Changes {
  timestamp: number;
  tasks: Task[];
  documents: Document[];
  mentions: Mention[];
  services: Service[];
}