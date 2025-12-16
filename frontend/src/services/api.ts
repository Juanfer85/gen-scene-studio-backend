import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  ApiJobStatusResponse,
  JobStatus,
  RenderBatchPayload,
  ComposePayload,
  TTSPayload,
  JobState
} from '@/types/job';

// Environment variables validation
const validateEnvironment = () => {
  const required = ['NEXT_PUBLIC_API_URL', 'NEXT_PUBLIC_API_KEY'];
  const missing = required.filter(key => !process.env[key]);

  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }
};

class ApiService {
  private client: AxiosInstance;
  private readonly baseURL: string;
  private readonly apiKey: string;
  private readonly timeout: number;

  constructor() {
    // Validate environment variables
    validateEnvironment();

    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    this.apiKey = process.env.NEXT_PUBLIC_API_KEY || '';
    this.timeout = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000');

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey,
      },
    });

    // Request interceptor for debugging and logging
    this.client.interceptors.request.use((config) => {
      if (process.env.NODE_ENV === 'development') {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, {
          data: config.data,
          params: config.params,
        });
      }
      return config;
    });

    // Response interceptor for error handling and debugging
    this.client.interceptors.response.use(
      (response) => {
        if (process.env.NODE_ENV === 'development') {
          console.log(`API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
            status: response.status,
            data: response.data,
          });
        }
        return response;
      },
      (error) => {
        console.error('API Error:', error);
        throw this.handleError(error);
      }
    );
  }

  private handleError(error: any): Error {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const message = error.response.data?.detail || error.message;

      switch (status) {
        case 401:
          return new Error('Unauthorized: Invalid API key');
        case 404:
          return new Error('Job not found');
        case 429:
          return new Error('Rate limit exceeded');
        case 500:
          return new Error('Server error');
        default:
          return new Error(`API Error (${status}): ${message}`);
      }
    } else if (error.request) {
      // Network error
      return new Error('Network error: Unable to connect to server');
    } else {
      // Other error
      return new Error(error.message || 'Unknown error occurred');
    }
  }

  // Job status endpoints
  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response: AxiosResponse<ApiJobStatusResponse> = await this.client.get(
      `/api/status?job_id=${jobId}`
    );

    return {
      ...response.data,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  }

  async getMultipleJobStatus(jobIds: string[]): Promise<JobStatus[]> {
    const promises = jobIds.map(id => this.getJobStatus(id));
    return Promise.allSettled(promises).then(results =>
      results
        .filter((result): result is PromiseFulfilledResult<JobStatus> =>
          result.status === 'fulfilled'
        )
        .map(result => result.value)
    );
  }

  // Job creation endpoints
  async createRenderBatch(payload: RenderBatchPayload): Promise<{ job_id: string; accepted: number; deduped: number }> {
    const response = await this.client.post('/api/render-batch', payload);
    return response.data;
  }

  async createComposeJob(payload: ComposePayload): Promise<{ job_id: string; accepted: boolean }> {
    const response = await this.client.post('/api/compose', payload);
    return response.data;
  }

  async createTTSJob(payload: TTSPayload): Promise<{ audio_url: string; duration_s: number }> {
    const response = await this.client.post('/api/tts', payload);
    return response.data;
  }

  // Compose result endpoint
  async getComposeResult(jobId: string): Promise<{
    job_id: string;
    ready: boolean;
    video_url?: string;
    size_bytes?: number;
    reason?: string;
  }> {
    const response = await this.client.get(`/api/compose-result?job_id=${jobId}`);
    return response.data;
  }

  // Quick Create endpoint
  async quickCreateFullUniverse(payload: any): Promise<any> {
    console.log("DEBUG QuickCreateFullUniverse URL:", this.baseURL, `${this.baseURL}/api/quick-create-full-universe`);
    const response = await this.client.post('/api/quick-create-full-universe', payload);
    return response.data;
  }

  // Jobs Hub endpoint
  async getJobsHub(): Promise<{ jobs: any[]; total: number }> {
    const response = await this.client.get('/api/jobs-hub');
    return response.data;
  }

  // ============================================================================
  // VIDEO MODELS ENDPOINTS
  // ============================================================================

  /**
   * Obtener todos los modelos de video disponibles
   */
  async getVideoModels(): Promise<{
    models: Array<{
      id: string;
      name: string;
      tier: 'premium' | 'high' | 'economic';
      credits_5s: number;
      max_duration: number;
      features: string[];
      description: string;
      recommended_for: string[];
    }>;
    total: number;
    default_model: string;
  }> {
    const response = await this.client.get('/api/video-models');
    return response.data;
  }

  /**
   * Obtener el mapeo de estilos a modelos
   */
  async getStyleModelMapping(): Promise<{
    mapping: Record<string, string>;
    available_styles: string[];
    note: string;
  }> {
    const response = await this.client.get('/api/style-model-mapping');
    return response.data;
  }

  /**
   * Obtener el modelo recomendado para un estilo específico
   */
  async getRecommendedModel(styleKey: string): Promise<{
    style_key: string;
    recommended_model: string;
    model_info: {
      id: string;
      name: string;
      tier: string;
      credits_5s: number;
      max_duration: number;
      features: string[];
      description: string;
    };
    can_override: boolean;
    available_models: string[];
  }> {
    const response = await this.client.get(`/api/recommended-model/${styleKey}`);
    return response.data;
  }

  /**
   * Quick Create con soporte para selección de modelo
   * @param payload Datos del job incluyendo video_model opcional
   */
  async quickCreateWithModel(payload: {
    idea_text: string;
    duration: string;
    style_key: string;
    auto_create_universe?: boolean;
    video_model?: string | null;  // null = auto-select based on style
    video_duration?: number;
    video_quality?: '720p' | '1080p';
    aspect_ratio?: '16:9' | '9:16' | '1:1';
  }): Promise<{
    job_id: string;
    episode_id?: string;
    series_id?: string;
    character_id?: string;
    status: 'queued' | 'processing' | 'error';
    estimated_time_sec?: number;
    message: string;
  }> {
    // Si video_model es null, no lo enviamos para que el backend auto-seleccione
    const cleanPayload = { ...payload };
    if (cleanPayload.video_model === null) {
      delete cleanPayload.video_model;
    }

    const response = await this.client.post('/api/quick-create-full-universe', cleanPayload);
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{
    status: string;
    ffmpeg: boolean;
    ffprobe: boolean;
    db: boolean;
    rate_limiter: string;
  }> {
    const response = await this.client.get('/health');
    return response.data;
  }

  // Utility method to check if job is still active
  isJobActive(state: JobState): boolean {
    return ['queued', 'running'].includes(state);
  }

  // Batch status check with caching
  async getBatchStatusWithCache(
    jobIds: string[],
    cacheKey: string,
    cacheDuration: number = 2000 // 2 seconds default cache
  ): Promise<JobStatus[]> {
    const cached = this.getFromCache(cacheKey);
    if (cached && Date.now() - cached.timestamp < cacheDuration) {
      return cached.data;
    }

    const data = await this.getMultipleJobStatus(jobIds);
    this.setCache(cacheKey, data);

    return data;
  }

  // Simple cache implementation
  private cache = new Map<string, { data: any; timestamp: number }>();

  private getFromCache(key: string): { data: any; timestamp: number } | null {
    return this.cache.get(key) || null;
  }

  private setCache(key: string, data: any): void {
    this.cache.set(key, { data, timestamp: Date.now() });

    // Cleanup old cache entries periodically
    if (this.cache.size > 100) {
      this.cleanupCache();
    }
  }

  private cleanupCache(): void {
    const now = Date.now();
    const maxAge = 5 * 60 * 1000; // 5 minutes

    for (const [key, value] of this.cache.entries()) {
      if (now - value.timestamp > maxAge) {
        this.cache.delete(key);
      }
    }
  }
}

// Create singleton instance
export const apiService = new ApiService();

// Export types for external use
export type { ApiService };
export default apiService;