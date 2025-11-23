export type Quality = 'draft' | 'upscale';
export type JobState = 'idle' | 'queued' | 'running' | 'done' | 'error';
export type JobType = 'render_batch' | 'compose' | 'tts';

export interface RenderItem {
  id: string;
  prompt: string;
  negative: string;
  seed: number;
  quality: Quality;
  hash?: string;
  url?: string | null;
  status: 'queued' | 'running' | 'done' | 'error';
}

export interface JobStatus {
  job_id: string;
  state: JobState;
  progress: number;
  outputs: RenderItem[];
  type?: JobType;
  created_at?: string;
  updated_at?: string;
  error_message?: string;
  metadata?: Record<string, any>;
}

export interface JobMonitorConfig {
  pollingInterval?: number;
  maxRetries?: number;
  retryDelay?: number;
  enableNotifications?: boolean;
  persistToLocalStorage?: boolean;
  maxActiveJobs?: number;
  cleanupAfterHours?: number;
}

export interface JobNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  jobId?: string;
  timestamp: number;
  read: boolean;
}

export interface JobsState {
  activeJobs: JobStatus[];
  completedJobs: JobStatus[];
  notifications: JobNotification[];
  config: JobMonitorConfig;
  isConnected: boolean;
  lastUpdate: number;
}

// Storage keys for localStorage
export const STORAGE_KEYS = {
  JOBS: 'lovable_jobs',
  NOTIFICATIONS: 'lovable_notifications',
  CONFIG: 'lovable_job_config',
} as const;

// API Response types
export interface ApiJobStatusResponse {
  job_id: string;
  state: JobState;
  progress: number;
  outputs: RenderItem[];
}

export interface RenderBatchPayload {
  job_id: string;
  model: string;
  aspectRatio: string;
  enableTranslation?: boolean;
  planos: Array<{
    id: string;
    prompt: string;
    negative: string;
    seed: number;
    quality: Quality;
  }>;
}

export interface ComposePayload {
  job_id: string;
  images: Array<{
    url: string;
    duration: number;
    kenburns: string;
    text: string;
    pos: string;
  }>;
  audio: string;
  srt: string;
  out: string;
  fade_in_ms?: number;
  fade_out_ms?: number;
  loudnorm?: boolean;
  logo_path?: string;
  logo_scale?: number;
  lut_path?: string;
  margin?: number;
}

export interface TTSPayload {
  job_id: string;
  text: string;
  voice?: string;
  wpm?: number;
}