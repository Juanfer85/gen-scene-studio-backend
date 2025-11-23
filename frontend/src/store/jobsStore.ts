import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import {
  JobStatus,
  JobNotification,
  JobMonitorConfig,
  JobsState,
  JobState as JobStatusEnum,
  STORAGE_KEYS
} from '@/types/job';
import { apiService } from '@/services/api';

interface JobsStore extends JobsState {
  // Actions
  addJob: (job: JobStatus) => void;
  updateJob: (jobId: string, updates: Partial<JobStatus>) => void;
  removeJob: (jobId: string) => void;
  moveJobToCompleted: (jobId: string) => void;

  // Notifications
  addNotification: (notification: Omit<JobNotification, 'id' | 'timestamp'>) => void;
  markNotificationRead: (notificationId: string) => void;
  clearNotifications: () => void;

  // Configuration
  updateConfig: (config: Partial<JobMonitorConfig>) => void;

  // Bulk operations
  refreshJobs: () => Promise<void>;
  cleanupOldJobs: () => void;

  // Persistence helpers
  loadFromStorage: () => void;
  saveToStorage: () => void;
}

const defaultConfig: JobMonitorConfig = {
  pollingInterval: parseInt(import.meta.env.VITE_DEFAULT_POLLING_INTERVAL || '3000'),
  maxRetries: 3,
  retryDelay: 1000,
  enableNotifications: true,
  persistToLocalStorage: true,
  maxActiveJobs: parseInt(import.meta.env.VITE_MAX_ACTIVE_JOBS || '10'),
  cleanupAfterHours: 24,
};

export const useJobsStore = create<JobsStore>()(
  persist(
    (set, get) => ({
      // Initial state
      activeJobs: [],
      completedJobs: [],
      notifications: [],
      config: defaultConfig,
      isConnected: false,
      lastUpdate: 0,

      // Job management
      addJob: (job) => {
        set((state) => {
          // Check if job already exists
          const existingIndex = state.activeJobs.findIndex(j => j.job_id === job.job_id);

          if (existingIndex >= 0) {
            // Update existing job
            const updatedJobs = [...state.activeJobs];
            updatedJobs[existingIndex] = { ...updatedJobs[existingIndex], ...job };
            return { activeJobs: updatedJobs };
          } else {
            // Add new job
            return {
              activeJobs: [...state.activeJobs, job],
              lastUpdate: Date.now()
            };
          }
        });
      },

      updateJob: (jobId, updates) => {
        set((state) => {
          const updatedJobs = state.activeJobs.map(job =>
            job.job_id === jobId
              ? { ...job, ...updates, updated_at: new Date().toISOString() }
              : job
          );
          return { activeJobs: updatedJobs, lastUpdate: Date.now() };
        });
      },

      removeJob: (jobId) => {
        set((state) => ({
          activeJobs: state.activeJobs.filter(job => job.job_id !== jobId),
          completedJobs: state.completedJobs.filter(job => job.job_id !== jobId),
        }));
      },

      moveJobToCompleted: (jobId) => {
        set((state) => {
          const jobToMove = state.activeJobs.find(job => job.job_id === jobId);
          if (!jobToMove) return state;

          return {
            activeJobs: state.activeJobs.filter(job => job.job_id !== jobId),
            completedJobs: [jobToMove, ...state.completedJobs],
          };
        });
      },

      // Notifications
      addNotification: (notification) => {
        const newNotification: JobNotification = {
          ...notification,
          id: crypto.randomUUID(),
          timestamp: Date.now(),
          read: false,
        };

        set((state) => ({
          notifications: [newNotification, ...state.notifications].slice(0, 50), // Keep last 50
        }));

        // Auto-show notification if enabled
        const state = get();
        if (state.config.enableNotifications && typeof window !== 'undefined') {
          // Trigger toast notification here if using sonner
          console.info('Notification:', newNotification.title, newNotification.message);
        }
      },

      markNotificationRead: (notificationId) => {
        set((state) => ({
          notifications: state.notifications.map(n =>
            n.id === notificationId ? { ...n, read: true } : n
          ),
        }));
      },

      clearNotifications: () => {
        set({ notifications: [] });
      },

      // Configuration
      updateConfig: (configUpdates) => {
        set((state) => ({
          config: { ...state.config, ...configUpdates },
        }));
      },

      // Bulk operations
      refreshJobs: async () => {
        const state = get();
        const activeJobIds = state.activeJobs.map(job => job.job_id);

        if (activeJobIds.length === 0) return;

        try {
          const updatedJobs = await apiService.getMultipleJobStatus(activeJobIds);

          set((currentState) => {
            const updatedActiveJobs = updatedJobs.map(updatedJob => {
              const previousJob = currentState.activeJobs.find(j => j.job_id === updatedJob.job_id);

              // Detect state changes for notifications
              if (previousJob && previousJob.state !== updatedJob.state) {
                const { addNotification } = get();

                if (updatedJob.state === 'done') {
                  addNotification({
                    type: 'success',
                    title: 'Job Completed',
                    message: `Job ${updatedJob.job_id} completed successfully`,
                    jobId: updatedJob.job_id,
                  });
                } else if (updatedJob.state === 'error') {
                  addNotification({
                    type: 'error',
                    title: 'Job Failed',
                    message: `Job ${updatedJob.job_id} failed: ${updatedJob.error_message || 'Unknown error'}`,
                    jobId: updatedJob.job_id,
                  });
                }
              }

              return updatedJob;
            });

            return {
              activeJobs: updatedActiveJobs,
              isConnected: true,
              lastUpdate: Date.now(),
            };
          });

          // Move completed jobs to completed list
          const currentState = get();
          const completedJobs = currentState.activeJobs.filter(job =>
            !apiService.isJobActive(job.state)
          );

          completedJobs.forEach(job => {
            get().moveJobToCompleted(job.job_id);
          });

        } catch (error) {
          console.error('Failed to refresh jobs:', error);
          set({ isConnected: false });
        }
      },

      cleanupOldJobs: () => {
        const state = get();
        const cutoffTime = Date.now() - (state.config.cleanupAfterHours! * 60 * 60 * 1000);

        set((currentState) => ({
          completedJobs: currentState.completedJobs.filter(job => {
            const jobTime = new Date(job.updated_at || job.created_at || '').getTime();
            return jobTime > cutoffTime;
          }),
        }));
      },

      // Persistence helpers
      loadFromStorage: () => {
        if (typeof window === 'undefined') return;

        try {
          const storedJobs = localStorage.getItem(STORAGE_KEYS.JOBS);
          const storedNotifications = localStorage.getItem(STORAGE_KEYS.NOTIFICATIONS);
          const storedConfig = localStorage.getItem(STORAGE_KEYS.CONFIG);

          if (storedJobs) {
            const jobs = JSON.parse(storedJobs);
            set({ activeJobs: jobs.active || [], completedJobs: jobs.completed || [] });
          }

          if (storedNotifications) {
            set({ notifications: JSON.parse(storedNotifications) });
          }

          if (storedConfig) {
            set({ config: { ...defaultConfig, ...JSON.parse(storedConfig) } });
          }
        } catch (error) {
          console.error('Failed to load from storage:', error);
        }
      },

      saveToStorage: () => {
        if (typeof window === 'undefined') return;

        const state = get();
        if (state.config.persistToLocalStorage) {
          try {
            localStorage.setItem(STORAGE_KEYS.JOBS, JSON.stringify({
              active: state.activeJobs,
              completed: state.completedJobs,
            }));
            localStorage.setItem(STORAGE_KEYS.NOTIFICATIONS, JSON.stringify(state.notifications));
            localStorage.setItem(STORAGE_KEYS.CONFIG, JSON.stringify(state.config));
          } catch (error) {
            console.error('Failed to save to storage:', error);
          }
        }
      },
    }),
    {
      name: 'lovable-jobs-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        activeJobs: state.activeJobs,
        completedJobs: state.completedJobs,
        notifications: state.notifications,
        config: state.config,
      }),
    }
  )
);