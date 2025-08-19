/**
 * Frontend Service Types
 * Multi-Channel AI Coaching Platform
 */

// Program Builder Types
export interface ProgramStep {
  id: string;
  step_id: string;
  program_id: string;
  step_type: StepType;
  step_name: string;
  position: {
    x: number;
    y: number;
  };
  trigger_config: TriggerConfig;
  action_config: ActionConfig;
}

export enum StepType {
  MESSAGE = "MESSAGE",
  TASK = "TASK", 
  SURVEY = "SURVEY",
  WAIT = "WAIT",
  CONDITION = "CONDITION",
  TRIGGER = "TRIGGER",
}

export interface TriggerConfig {
  trigger_type: TriggerType;
  schedule?: string;
  condition_expression?: string;
  delay_minutes?: number;
}

export enum TriggerType {
  IMMEDIATE = "IMMEDIATE",
  TIME_BASED = "TIME_BASED",
  CONDITION_BASED = "CONDITION_BASED",
  USER_ACTION = "USER_ACTION",
  DELAYED = "DELAYED",
}

export interface ActionConfig {
  action_type: ActionType;
  use_knowledge_context?: boolean;
  use_personality?: boolean;
  context_query?: string;
  message_template?: string;
  task_description?: string;
  survey_questions?: string[];
  wait_duration_minutes?: number;
}

export enum ActionType {
  SEND_MESSAGE = "SEND_MESSAGE",
  ASSIGN_TASK = "ASSIGN_TASK",
  SEND_SURVEY = "SEND_SURVEY",
  WAIT = "WAIT",
  TRIGGER_WEBHOOK = "TRIGGER_WEBHOOK",
}

// Authentication Types
export interface User {
  id: string;
  email: string;
  full_name: string;
  company_name?: string;
  is_active: boolean;
  subscription_tier: string;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  company_name?: string;
}

// Program Types
export interface Program {
  id: string;
  title: string;
  description: string;
  version: string;
  status: ProgramStatus;
  creator_id: string;
  enable_personality: boolean;
  enable_analytics: boolean;
  created_at: string;
  updated_at: string;
}

export enum ProgramStatus {
  DRAFT = "DRAFT",
  ACTIVE = "ACTIVE", 
  PAUSED = "PAUSED",
  ARCHIVED = "ARCHIVED",
}

// React Flow Node Types
export interface NodeData {
  step: ProgramStep;
  label: string;
  stepType: StepType;
  isEditing?: boolean;
}

export interface EdgeData {
  sourceStepId: string;
  targetStepId: string;
  condition?: string;
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Canvas Store Types
export interface CanvasStore {
  nodes: any[];
  edges: any[];
  selectedNode: string | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  addNode: (node: any) => void;
  updateNode: (id: string, updates: any) => void;
  deleteNode: (id: string) => void;
  addEdge: (edge: any) => void;
  deleteEdge: (id: string) => void;
  selectNode: (id: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearCanvas: () => void;
}

// Environment Configuration
export interface EnvConfig {
  AUTH_SERVICE_URL: string;
  CREATOR_HUB_SERVICE_URL: string;
  AI_ENGINE_SERVICE_URL: string;
  CHANNEL_SERVICE_URL: string;
  DEVELOPMENT_MODE: boolean;
}