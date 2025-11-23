import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Plus,
  Play,
  Zap,
  Image,
  Video,
  Music,
  Trash2,
  Loader2,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useJobsStore } from '@/store/jobsStore';
import { useJobMonitor } from '@/hooks/useJobMonitor';
import { generateJobId } from '@/utils/helpers';
import { JobStatus, JobType, RenderItem } from '@/types/job';

interface DemoJobConfig {
  type: JobType;
  name: string;
  description: string;
  icon: React.ElementType;
  baseProgress: number;
  itemCount: number;
  duration: number; // in seconds
}

const demoJobConfigs: DemoJobConfig[] = [
  {
    type: 'render_batch',
    name: 'Render Batch',
    description: 'Generate multiple images from text prompts',
    icon: Image,
    baseProgress: 0,
    itemCount: 10,
    duration: 30,
  },
  {
    type: 'compose',
    name: 'Video Compose',
    description: 'Compose multiple images into a video',
    icon: Video,
    baseProgress: 0,
    itemCount: 1,
    duration: 45,
  },
  {
    type: 'tts',
    name: 'Text to Speech',
    description: 'Convert text to audio using TTS',
    icon: Music,
    baseProgress: 0,
    itemCount: 1,
    duration: 15,
  },
];

const DemoJobsCreator: React.FC = () => {
  const { addJob, addNotification } = useJobsStore();
  const { addJob: monitorAddJob } = useJobMonitor();
  const [isCreating, setIsCreating] = useState<Record<string, boolean>>({});

  const createDemoJob = async (config: DemoJobConfig) => {
    setIsCreating(prev => ({ ...prev, [config.type]: true }));

    try {
      const jobId = generateJobId();

      // Create initial job with queued status
      const job: JobStatus = {
        job_id: jobId,
        state: 'queued',
        progress: 0,
        type: config.type,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {
          demo: true,
          duration: config.duration,
          itemCount: config.itemCount,
        },
      };

      // Add outputs for render_batch jobs
      if (config.type === 'render_batch') {
        const outputs: RenderItem[] = Array.from({ length: config.itemCount }, (_, i) => ({
          id: `item_${i + 1}`,
          prompt: `Demo prompt ${i + 1}: A beautiful landscape with mountains and lakes`,
          negative: 'blurry, low quality, distorted',
          seed: Math.floor(Math.random() * 1000000),
          quality: Math.random() > 0.5 ? 'draft' : 'upscale',
          status: 'queued',
          hash: `hash_${i + 1}`,
        }));
        job.outputs = outputs;
      }

      addJob(job);
      monitorAddJob(job);

      addNotification({
        type: 'info',
        title: 'Demo Job Created',
        message: `${config.name} job ${jobId} has been created and will start processing.`,
        jobId,
      });

      // Simulate job progression
      await simulateJobProgress(jobId, config);

    } catch (error) {
      console.error('Failed to create demo job:', error);
      addNotification({
        type: 'error',
        title: 'Failed to Create Job',
        message: `Could not create ${config.name} job. Please try again.`,
      });
    } finally {
      setIsCreating(prev => ({ ...prev, [config.type]: false }));
    }
  };

  const simulateJobProgress = async (jobId: string, config: DemoJobConfig) => {
    const steps = config.itemCount;
    const stepDuration = (config.duration * 1000) / steps; // Convert to milliseconds

    // Move to running
    await new Promise(resolve => setTimeout(resolve, 1000));
    updateJobStatus(jobId, 'running', 0);

    // Simulate progress
    for (let i = 1; i <= steps; i++) {
      await new Promise(resolve => setTimeout(resolve, stepDuration));
      const progress = Math.round((i / steps) * 100);

      // Update outputs for render_batch jobs
      if (config.type === 'render_batch') {
        updateJobOutputs(jobId, i - 1);
      }

      updateJobStatus(jobId, 'running', progress);
    }

    // Move to done
    await new Promise(resolve => setTimeout(resolve, 500));
    updateJobStatus(jobId, 'done', 100);

    addNotification({
      type: 'success',
      title: 'Demo Job Completed',
      message: `${config.name} job ${jobId} has completed successfully.`,
      jobId,
    });
  };

  const updateJobStatus = (jobId: string, state: JobState, progress: number) => {
    const { updateJob } = useJobsStore.getState();
    updateJob(jobId, {
      state,
      progress,
      updated_at: new Date().toISOString(),
    });
  };

  const updateJobOutputs = (jobId: string, itemIndex: number) => {
    const { activeJobs } = useJobsStore.getState();
    const job = activeJobs.find(j => j.job_id === jobId);
    if (job?.outputs) {
      const updatedOutputs = [...job.outputs];
      updatedOutputs[itemIndex] = {
        ...updatedOutputs[itemIndex],
        status: 'done',
        url: `https://picsum.photos/512/512?random=${itemIndex}`,
      };

      const { updateJob } = useJobsStore.getState();
      updateJob(jobId, {
        outputs: updatedOutputs,
        updated_at: new Date().toISOString(),
      });
    }
  };

  const createRandomError = () => {
    const randomConfig = demoJobConfigs[Math.floor(Math.random() * demoJobConfigs.length)];
    const jobId = generateJobId();

    const job: JobStatus = {
      job_id: jobId,
      state: 'error',
      progress: Math.floor(Math.random() * 50),
      type: randomConfig.type,
      created_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
      updated_at: new Date().toISOString(),
      error_message: 'This is a simulated error for demonstration purposes.',
      metadata: {
        demo: true,
        simulatedError: true,
      },
    };

    addJob(job);
    addNotification({
      type: 'error',
      title: 'Demo Error Created',
      message: `A sample error job has been created for testing error handling.`,
      jobId,
    });
  };

  const clearAllJobs = () => {
    const { activeJobs, completedJobs, removeJob } = useJobsStore.getState();
    [...activeJobs, ...completedJobs].forEach(job => {
      removeJob(job.job_id);
    });

    addNotification({
      type: 'info',
      title: 'Jobs Cleared',
      message: 'All demo jobs have been removed.',
    });
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Demo Jobs Creator</h2>
        <p className="text-gray-600 mb-6">
          Create sample jobs to test the monitoring system. These are simulated jobs that will progress through different states.
        </p>

        {/* Job creation buttons */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {demoJobConfigs.map((config) => {
            const Icon = config.icon;
            const isLoading = isCreating[config.type];

            return (
              <motion.button
                key={config.type}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => createDemoJob(config)}
                disabled={isLoading}
                className={clsx(
                  "relative p-4 border-2 border-dashed rounded-xl transition-all duration-200",
                  isLoading
                    ? "border-blue-300 bg-blue-50 cursor-not-allowed"
                    : "border-gray-300 hover:border-blue-400 hover:bg-blue-50"
                )}
              >
                <div className="flex flex-col items-center gap-3">
                  <Icon className={clsx(
                    "w-8 h-8",
                    isLoading ? "text-blue-500 animate-pulse" : "text-gray-500"
                  )} />
                  <div className="text-center">
                    <h3 className="font-medium text-gray-900">{config.name}</h3>
                    <p className="text-xs text-gray-500 mt-1">{config.description}</p>
                  </div>
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                  ) : (
                    <Plus className="w-4 h-4 text-gray-400" />
                  )}
                </div>

                {isLoading && (
                  <div className="absolute inset-0 bg-white bg-opacity-75 rounded-xl flex items-center justify-center">
                    <div className="text-center">
                      <Loader2 className="w-6 h-6 text-blue-500 animate-spin mx-auto mb-2" />
                      <p className="text-sm text-blue-600 font-medium">Creating...</p>
                    </div>
                  </div>
                )}
              </motion.button>
            );
          })}
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-3">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={createRandomError}
            className="flex items-center gap-2 px-4 py-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition-colors"
          >
            <Zap className="w-4 h-4" />
            Create Error Job
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={clearAllJobs}
            className="flex items-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Clear All Jobs
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => {
              // Create multiple jobs at once
              demoJobConfigs.forEach((config, index) => {
                setTimeout(() => createDemoJob(config), index * 500);
              });
            }}
            className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
          >
            <Play className="w-4 h-4" />
            Create All Jobs
          </motion.button>
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h3 className="font-medium text-blue-900 mb-2">How to use the demo</h3>
        <ol className="text-sm text-blue-800 space-y-1">
          <li>1. Click on any job type above to create a sample job</li>
          <li>2. Watch the jobs progress through different states in the Job Panel</li>
          <li>3. Switch to the "Live Monitor" tab to see real-time updates</li>
          <li>4. Try creating error jobs to test error handling</li>
          <li>5. Use the Configuration tab to customize polling and notification settings</li>
        </ol>
      </div>
    </div>
  );
};

export default DemoJobsCreator;