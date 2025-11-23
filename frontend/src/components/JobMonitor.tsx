import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  Pause,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  AlertCircle,
  Loader2,
  TrendingUp,
} from 'lucide-react';
import { clsx } from 'clsx';
import { JobStatus, JobState } from '@/types/job';
import { useJobMonitor } from '@/hooks/useJobMonitor';

interface JobMonitorProps {
  jobId?: string;
  jobIds?: string[];
  className?: string;
  showControls?: boolean;
  showStats?: boolean;
  compact?: boolean;
  autoStart?: boolean;
}

interface JobItemProps {
  job: JobStatus;
  isCompact?: boolean;
}

const JobItem: React.FC<JobItemProps> = ({ job, isCompact = false }) => {
  const getStatusIcon = (state: JobState) => {
    switch (state) {
      case 'queued':
        return <Clock className="w-4 h-4 text-gray-400" />;
      case 'running':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'done':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (state: JobState) => {
    switch (state) {
      case 'queued':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      case 'running':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'done':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'error':
        return 'bg-red-50 text-red-700 border-red-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const getProgressColor = (state: JobState) => {
    switch (state) {
      case 'running':
        return 'bg-blue-500';
      case 'done':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  if (isCompact) {
    return (
      <div className="flex items-center gap-2 p-2 bg-white rounded-lg border border-gray-200">
        {getStatusIcon(job.state)}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {job.job_id}
          </p>
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <motion.div
              className={clsx("h-1.5 rounded-full transition-all duration-300", getProgressColor(job.state))}
              initial={{ width: 0 }}
              animate={{ width: `${job.progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
        <span className="text-xs text-gray-500 min-w-0">
          {job.progress}%
        </span>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          {getStatusIcon(job.state)}
          <div>
            <h3 className="font-medium text-gray-900">{job.job_id}</h3>
            <p className="text-xs text-gray-500">
              {job.type?.toUpperCase() || 'UNKNOWN'} •
              {new Date(job.created_at || '').toLocaleTimeString()}
            </p>
          </div>
        </div>
        <span className={clsx(
          "px-2 py-1 text-xs font-medium rounded-full border",
          getStatusColor(job.state)
        )}>
          {job.state.toUpperCase()}
        </span>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Progress</span>
          <span className="font-medium text-gray-900">{job.progress}%</span>
        </div>

        <div className="w-full bg-gray-200 rounded-full h-2">
          <motion.div
            className={clsx("h-2 rounded-full transition-all duration-500", getProgressColor(job.state))}
            initial={{ width: 0 }}
            animate={{ width: `${job.progress}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>

        {job.outputs && job.outputs.length > 0 && (
          <div className="pt-2 border-t border-gray-100">
            <p className="text-xs text-gray-500 mb-1">
              {job.outputs.filter(o => o.status === 'done').length} / {job.outputs.length} items completed
            </p>
            <div className="grid grid-cols-8 gap-1">
              {job.outputs.slice(0, 16).map((output, index) => (
                <div
                  key={index}
                  className={clsx(
                    "w-full h-2 rounded-xs",
                    output.status === 'done' ? 'bg-green-400' :
                    output.status === 'running' ? 'bg-blue-400' :
                    output.status === 'error' ? 'bg-red-400' :
                    'bg-gray-300'
                  )}
                />
              ))}
              {job.outputs.length > 16 && (
                <div className="w-full h-2 rounded-xs bg-gray-300 flex items-center justify-center">
                  <span className="text-[8px] text-gray-600">+{job.outputs.length - 16}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {job.error_message && (
          <div className="p-2 bg-red-50 border border-red-200 rounded-md">
            <p className="text-xs text-red-700">{job.error_message}</p>
          </div>
        )}

        {job.metadata && Object.keys(job.metadata).length > 0 && (
          <details className="text-xs">
            <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
              Details
            </summary>
            <div className="mt-1 p-2 bg-gray-50 rounded text-gray-600">
              {Object.entries(job.metadata).map(([key, value]) => (
                <div key={key}>
                  <span className="font-medium">{key}:</span>{' '}
                  <span>{JSON.stringify(value)}</span>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </motion.div>
  );
};

export const JobMonitor: React.FC<JobMonitorProps> = ({
  jobId,
  jobIds,
  className,
  showControls = true,
  showStats = true,
  compact = false,
  autoStart = true,
}) => {
  const {
    jobs,
    isLoading,
    isConnected,
    error,
    lastUpdate,
    startMonitoring,
    stopMonitoring,
    removeJob,
    retryJob,
    activeJobsCount,
    completedJobsCount,
    averageProgress,
  } = useJobMonitor({
    jobId,
    jobIds,
    autoStart,
  });

  const activeJobs = jobs.filter(job => ['queued', 'running'].includes(job.state));
  const completedJobs = jobs.filter(job => ['done', 'error'].includes(job.state));

  if (compact) {
    return (
      <div className={clsx("space-y-2", className)}>
        <AnimatePresence mode="popLayout">
          {activeJobs.map((job) => (
            <JobItem key={job.job_id} job={job} isCompact />
          ))}
        </AnimatePresence>
        {activeJobs.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-4">No active jobs</p>
        )}
      </div>
    );
  }

  return (
    <div className={clsx("bg-gray-50 rounded-xl border border-gray-200", className)}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white rounded-t-xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Job Monitor</h2>
            <div className="flex items-center gap-4 mt-1">
              <span className="text-sm text-gray-500">
                {activeJobsCount} active
              </span>
              {showStats && (
                <>
                  <span className="text-sm text-gray-500">
                    {completedJobsCount} completed
                  </span>
                  {activeJobsCount > 0 && (
                    <div className="flex items-center gap-1">
                      <TrendingUp className="w-3 h-3 text-gray-400" />
                      <span className="text-sm text-gray-500">
                        {Math.round(averageProgress)}% avg
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          {showControls && (
            <div className="flex items-center gap-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={isConnected ? stopMonitoring : startMonitoring}
                className={clsx(
                  "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  isConnected
                    ? "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    : "bg-blue-500 text-white hover:bg-blue-600"
                )}
              >
                {isConnected ? (
                  <>
                    <Pause className="w-4 h-4" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Start
                  </>
                )}
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => window.location.reload()}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </motion.button>
            </div>
          )}
        </div>

        {/* Status indicator */}
        <div className="flex items-center gap-2 mt-3">
          <div className={clsx(
            "w-2 h-2 rounded-full",
            isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"
          )} />
          <span className="text-xs text-gray-500">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
          {error && (
            <span className="text-xs text-red-500 ml-2">{error}</span>
          )}
          {lastUpdate > 0 && (
            <span className="text-xs text-gray-400 ml-auto">
              Last update: {new Date(lastUpdate).toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {isLoading && jobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-2" />
            <p className="text-sm text-gray-500">Loading jobs...</p>
          </div>
        ) : (
          <>
            {/* Active Jobs */}
            {activeJobs.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Active Jobs</h3>
                <div className="space-y-3">
                  <AnimatePresence mode="popLayout">
                    {activeJobs.map((job) => (
                      <JobItem key={job.job_id} job={job} />
                    ))}
                  </AnimatePresence>
                </div>
              </div>
            )}

            {/* Completed Jobs */}
            {completedJobs.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">Recent Completed Jobs</h3>
                <div className="space-y-3">
                  <AnimatePresence mode="popLayout">
                    {completedJobs.slice(0, 5).map((job) => (
                      <JobItem key={job.job_id} job={job} />
                    ))}
                  </AnimatePresence>
                </div>
                {completedJobs.length > 5 && (
                  <p className="text-xs text-gray-500 text-center mt-2">
                    +{completedJobs.length - 5} more completed jobs
                  </p>
                )}
              </div>
            )}

            {/* Empty state */}
            {jobs.length === 0 && (
              <div className="text-center py-8">
                <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-500">No jobs found</p>
                <p className="text-xs text-gray-400 mt-1">
                  Jobs will appear here when they are created
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default JobMonitor;