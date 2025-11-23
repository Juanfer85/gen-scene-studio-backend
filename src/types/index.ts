export type Quality = "draft" | "upscale";

export interface RenderItemIn {
  id: string;
  prompt: string;
  negative: string;
  seed: number;
  quality: Quality;
}

export interface RenderBatchIn {
  job_id: string;
  model: string;
  aspectRatio: string;
  enableTranslation?: boolean;
  planos: RenderItemIn[];
}

export interface RenderItemOut {
  id: string;
  quality: Quality;
  hash: string;
  url?: string;
  status: "queued" | "running" | "done" | "error";
}

export interface JobStatusOut {
  job_id: string;
  state: "idle" | "queued" | "running" | "done" | "error";
  progress: number;
  outputs: RenderItemOut[];
}

export interface ComposeImage {
  url: string;
  duration: number;
  kenburns: string;
  text?: string;
  pos?: string;
}

export interface ComposeIn {
  job_id: string;
  images: ComposeImage[];
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

export interface TTSIn {
  job_id: string;
  text: string;
  voice?: string;
  wpm?: number;
}

export interface TTSOut {
  audio_url: string;
  duration_s: number;
}

export interface ComposeResult {
  job_id: string;
  ready: boolean;
  reason?: string;
  video_url?: string;
  size_bytes?: number;
}

export interface RenderBatchResponse {
  job_id: string;
  accepted: number;
  deduped: number;
}

export interface ComposeResponse {
  job_id: string;
  accepted: boolean;
}