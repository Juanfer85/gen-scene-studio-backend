import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  RenderBatchIn,
  JobStatusOut,
  ComposeIn,
  ComposeResult,
  TTSIn,
  TTSOut,
  RenderBatchResponse,
  ComposeResponse
} from '@/types';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || '',
      },
      timeout: 60000, // 60 seconds timeout
    });

    // Request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error: AxiosError) => {
        const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred';
        console.error(`API Error: ${error.config?.method?.toUpperCase()} ${error.config?.url}`, errorMessage);
        return Promise.reject(new Error(errorMessage));
      }
    );
  }

  // Text-to-Speech API
  async generateSpeech(payload: TTSIn): Promise<TTSOut> {
    const response = await this.client.post<TTSOut>('/api/tts', payload);
    return response.data;
  }

  // Video Composition API
  async composeVideo(payload: ComposeIn): Promise<ComposeResponse> {
    const response = await this.client.post<ComposeResponse>('/api/compose', payload);
    return response.data;
  }

  // Get composition result
  async getComposeResult(jobId: string): Promise<ComposeResult> {
    const response = await this.client.get<ComposeResult>(`/api/compose-result?job_id=${jobId}`);
    return response.data;
  }

  // Batch render images
  async renderBatch(payload: RenderBatchIn): Promise<RenderBatchResponse> {
    const response = await this.client.post<RenderBatchResponse>('/api/render-batch', payload);
    return response.data;
  }

  // Get job status
  async getJobStatus(jobId: string): Promise<JobStatusOut> {
    const response = await this.client.get<JobStatusOut>(`/api/status?job_id=${jobId}`);
    return response.data;
  }

  // Helper method for polling job status
  async pollJobStatus(
    jobId: string,
    onUpdate: (status: JobStatusOut) => void,
    interval: number = 2000,
    timeout: number = 300000 // 5 minutes
  ): Promise<JobStatusOut> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();

      const poll = async () => {
        try {
          const status = await this.getJobStatus(jobId);
          onUpdate(status);

          // Check if job is complete
          if (status.state === 'done') {
            resolve(status);
            return;
          }

          // Check if job has error
          if (status.state === 'error') {
            reject(new Error(`Job ${jobId} failed with error state`));
            return;
          }

          // Check timeout
          if (Date.now() - startTime > timeout) {
            reject(new Error(`Job ${jobId} polling timeout after ${timeout}ms`));
            return;
          }

          // Continue polling
          setTimeout(poll, interval);
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }

  // Helper method for polling composition result
  async pollComposeResult(
    jobId: string,
    onUpdate: (result: ComposeResult) => void,
    interval: number = 2000,
    timeout: number = 300000
  ): Promise<ComposeResult> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();

      const poll = async () => {
        try {
          const result = await this.getComposeResult(jobId);
          onUpdate(result);

          if (result.ready) {
            resolve(result);
            return;
          }

          if (Date.now() - startTime > timeout) {
            reject(new Error(`Compose job ${jobId} polling timeout after ${timeout}ms`));
            return;
          }

          setTimeout(poll, interval);
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }

  // Generate file download URL
  getFileUrl(jobId: string, filename: string): string {
    return `${this.client.defaults.baseURL}/files/${jobId}/${filename}`;
  }
}

export const apiClient = new ApiClient();
export default apiClient;