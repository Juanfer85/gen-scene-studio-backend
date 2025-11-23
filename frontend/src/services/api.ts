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
  const required = ['VITE_API_URL', 'VITE_API_KEY'];
  const missing = required.filter(key => !import.meta.env[key]);

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

    this.baseURL = import.meta.env.VITE_API_URL;
    this.apiKey = import.meta.env.VITE_API_KEY;
    this.timeout = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');

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
      if (import.meta.env.VITE_DEBUG === 'true') {
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
        if (import.meta.env.VITE_DEBUG === 'true') {
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