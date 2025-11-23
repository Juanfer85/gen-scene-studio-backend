import { useEffect, useRef, useCallback, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { JobStatus, JobState, JobMonitorConfig } from '@/types/job';
import { useJobsStore } from '@/store/jobsStore';
import { apiService } from '@/services/api';

interface UseJobMonitorOptions {
  autoStart?: boolean;
  jobId?: string;
  jobIds?: string[];
  config?: Partial<JobMonitorConfig>;
  onJobComplete?: (job: JobStatus) => void;
  onJobError?: (job: JobStatus) => void;
  onStatusChange?: (job: JobStatus, previousState: JobState) => void;
}

interface UseJobMonitorReturn {
  jobs: JobStatus[];
  isLoading: boolean;
  isConnected: boolean;
  error: string | null;
  lastUpdate: number;

  // Actions
  startMonitoring: () => void;
  stopMonitoring: () => void;
  addJob: (job: JobStatus) => void;
  removeJob: (jobId: string) => void;
  retryJob: (jobId: string) => void;

  // Status
  activeJobsCount: number;
  completedJobsCount: number;
  averageProgress: number;
}

export function useJobMonitor({
  autoStart = true,
  jobId,
  jobIds,
  config,
  onJobComplete,
  onJobError,
  onStatusChange,
}: UseJobMonitorOptions = {}): UseJobMonitorReturn {
  const {
    activeJobs,
    completedJobs,
    notifications,
    config: globalConfig,
    isConnected: storeConnected,
    lastUpdate: storeLastUpdate,
    addJob: storeAddJob,
    updateJob: storeUpdateJob,
    removeJob: storeRemoveJob,
    moveJobToCompleted,
    refreshJobs: storeRefreshJobs,
    addNotification,
    updateConfig,
  } = useJobsStore();

  const [isMonitoring, setIsMonitoring] = useState(autoStart);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);
  const previousStatesRef = useRef<Map<string, JobState>>(new Map());
  const queryClient = useQueryClient();

  // Merge global config with local config
  const finalConfig: JobMonitorConfig = {
    ...globalConfig,
    ...config,
  };

  // Get job IDs to monitor
  const monitoredJobIds = useCallback(() => {
    const ids: string[] = [];
    if (jobId) ids.push(jobId);
    if (jobIds) ids.push(...jobIds);
    return ids;
  }, [jobId, jobIds]);

  // Query for job status
  const {
    data: fetchedJobs,
    isLoading,
    refetch,
    error: queryError,
  } = useQuery({
    queryKey: ['jobs', 'status', ...monitoredJobIds()],
    queryFn: async () => {
      const ids = monitoredJobIds();
      if (ids.length === 0) return [];

      try {
        const jobs = await apiService.getMultipleJobStatus(ids);
        setIsConnected(true);
        setError(null);
        retryCountRef.current = 0;
        return jobs;
      } catch (err) {
        setIsConnected(false);
        setError(err instanceof Error ? err.message : 'Failed to fetch jobs');
        throw err;
      }
    },
    enabled: isMonitoring && monitoredJobIds().length > 0,
    refetchInterval: isMonitoring ? finalConfig.pollingInterval : false,
    retry: finalConfig.maxRetries,
    retryDelay: finalConfig.retryDelay,
    staleTime: 1000, // Consider data stale after 1 second
  });

  // Store jobs in zustand store
  useEffect(() => {
    if (fetchedJobs) {
      fetchedJobs.forEach(job => {
        const previousState = previousStatesRef.current.get(job.job_id);

        // Check for state changes
        if (previousState && previousState !== job.state) {
          // Handle state change
          if (onStatusChange) {
            onStatusChange(job, previousState);
          }

          // Handle completion
          if (job.state === 'done' && previousState !== 'done') {
            if (onJobComplete) onJobComplete(job);

            if (finalConfig.enableNotifications) {
              addNotification({
                type: 'success',
                title: 'Job Completed',
                message: `Job ${job.job_id} completed successfully`,
                jobId: job.job_id,
              });
            }
          }

          // Handle errors
          if (job.state === 'error' && previousState !== 'error') {
            if (onJobError) onJobError(job);

            if (finalConfig.enableNotifications) {
              addNotification({
                type: 'error',
                title: 'Job Failed',
                message: `Job ${job.job_id} failed: ${job.error_message || 'Unknown error'}`,
                jobId: job.job_id,
              });
            }
          }
        }

        // Update previous state
        previousStatesRef.current.set(job.job_id, job.state);

        // Update job in store
        storeUpdateJob(job.job_id, job);

        // Move to completed if no longer active
        if (!apiService.isJobActive(job.state)) {
          moveJobToCompleted(job.job_id);
        }
      });
    }
  }, [fetchedJobs, onStatusChange, onJobComplete, onJobError, finalConfig.enableNotifications]);

  // Polling logic for active jobs
  useEffect(() => {
    if (!isMonitoring || finalConfig.pollingInterval! <= 0) {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      return;
    }

    pollingRef.current = setInterval(async () => {
      try {
        await storeRefreshJobs();
        setIsConnected(true);
        setError(null);
        retryCountRef.current = 0;
      } catch (err) {
        retryCountRef.current++;
        setIsConnected(false);
        setError(err instanceof Error ? err.message : 'Connection error');

        // Stop polling after max retries
        if (retryCountRef.current >= finalConfig.maxRetries!) {
          stopMonitoring();
        }
      }
    }, finalConfig.pollingInterval);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [isMonitoring, finalConfig.pollingInterval, finalConfig.maxRetries, storeRefreshJobs]);

  // Start monitoring
  const startMonitoring = useCallback(() => {
    setIsMonitoring(true);
    retryCountRef.current = 0;
  }, []);

  // Stop monitoring
  const stopMonitoring = useCallback(() => {
    setIsMonitoring(false);
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  // Add new job to monitor
  const addJob = useCallback((job: JobStatus) => {
    storeAddJob(job);
    previousStatesRef.current.set(job.job_id, job.state);

    // Refetch if not currently monitoring
    if (!isMonitoring) {
      refetch();
    }
  }, [storeAddJob, isMonitoring, refetch]);

  // Remove job from monitoring
  const removeJob = useCallback((jobId: string) => {
    storeRemoveJob(jobId);
    previousStatesRef.current.delete(jobId);

    // Invalidate query to remove from cache
    queryClient.invalidateQueries({ queryKey: ['jobs', 'status', jobId] });
  }, [storeRemoveJob, queryClient]);

  // Retry job (placeholder - would need backend support)
  const retryJob = useCallback((jobId: string) => {
    addNotification({
      type: 'info',
      title: 'Retry Job',
      message: `Retrying job ${jobId}...`,
      jobId,
    });

    // This would need to be implemented based on backend capabilities
    console.info(`Retrying job ${jobId}`);
  }, [addNotification]);

  // Calculate metrics
  const allJobs = [...activeJobs, ...completedJobs];
  const activeJobsCount = activeJobs.length;
  const completedJobsCount = completedJobs.length;

  const averageProgress = activeJobs.length > 0
    ? activeJobs.reduce((sum, job) => sum + job.progress, 0) / activeJobs.length
    : 0;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  return {
    jobs: allJobs,
    isLoading: isLoading || !isConnected,
    isConnected: isConnected && storeConnected,
    error: error || (queryError instanceof Error ? queryError.message : null),
    lastUpdate: storeLastUpdate,

    // Actions
    startMonitoring,
    stopMonitoring,
    addJob,
    removeJob,
    retryJob,

    // Status
    activeJobsCount,
    completedJobsCount,
    averageProgress,
  };
}