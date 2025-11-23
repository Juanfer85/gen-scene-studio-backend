import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Filter,
  Search,
  Download,
  Eye,
  Trash2,
  RefreshCw,
  Play,
  Pause,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Copy,
  ExternalLink,
} from 'lucide-react';
import { clsx } from 'clsx';
import { formatDistanceToNow } from 'date-fns';
import { JobStatus, JobState, JobType } from '@/types/job';
import { useJobsStore } from '@/store/jobsStore';
import { useJobMonitor } from '@/hooks/useJobMonitor';
import JobMonitor from './JobMonitor';

type SortField = 'created_at' | 'updated_at' | 'progress' | 'state' | 'job_id';
type SortOrder = 'asc' | 'desc';
type FilterState = JobState | 'all';

interface JobPanelProps {
  className?: string;
  showCompact?: boolean;
  autoRefresh?: boolean;
  maxJobs?: number;
}

interface JobRowProps {
  job: JobStatus;
  onJobAction: (jobId: string, action: string) => void;
  isSelected?: boolean;
  onSelect?: (jobId: string) => void;
  showDetails?: boolean;
}

const JobRow: React.FC<JobRowProps> = ({
  job,
  onJobAction,
  isSelected = false,
  onSelect,
  showDetails = false,
}) => {
  const [expanded, setExpanded] = useState(false);

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
        return 'bg-gray-100 text-gray-700 border-gray-300';
      case 'running':
        return 'bg-blue-100 text-blue-700 border-blue-300';
      case 'done':
        return 'bg-green-100 text-green-700 border-green-300';
      case 'error':
        return 'bg-red-100 text-red-700 border-red-300';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300';
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

  const copyJobId = () => {
    navigator.clipboard.writeText(job.job_id);
    // Could show a toast here
  };

  const formatTime = (dateString?: string) => {
    if (!dateString) return 'Never';
    return formatDistanceToNow(new Date(dateString), { addSuffix: true });
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={clsx(
        "bg-white border rounded-lg overflow-hidden transition-all",
        isSelected ? "border-blue-500 shadow-lg" : "border-gray-200",
        showDetails && "shadow-sm"
      )}
    >
      <div
        className={clsx(
          "p-4",
          onSelect && "cursor-pointer hover:bg-gray-50"
        )}
        onClick={() => onSelect?.(job.job_id)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {/* Selection checkbox */}
            {onSelect && (
              <input
                type="checkbox"
                checked={isSelected}
                onChange={(e) => {
                  e.stopPropagation();
                  onSelect(job.job_id);
                }}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            )}

            {/* Status icon */}
            {getStatusIcon(job.state)}

            {/* Job info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="font-medium text-gray-900 truncate">
                  {job.job_id}
                </h3>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    copyJobId();
                  }}
                  className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <Copy className="w-3 h-3" />
                </button>
              </div>
              <div className="flex items-center gap-4 mt-1">
                <span className="text-xs text-gray-500">
                  {job.type?.toUpperCase() || 'UNKNOWN'}
                </span>
                <span className="text-xs text-gray-500">
                  Created {formatTime(job.created_at)}
                </span>
                {job.updated_at !== job.created_at && (
                  <span className="text-xs text-gray-500">
                    Updated {formatTime(job.updated_at)}
                  </span>
                )}
              </div>
            </div>

            {/* Status badge */}
            <span className={clsx(
              "px-2 py-1 text-xs font-medium rounded-full border",
              getStatusColor(job.state)
            )}>
              {job.state.toUpperCase()}
            </span>
          </div>

          {/* Progress and actions */}
          <div className="flex items-center gap-3 ml-4">
            <div className="flex items-center gap-2">
              <div className="w-24 bg-gray-200 rounded-full h-2">
                <motion.div
                  className={clsx("h-2 rounded-full transition-all duration-500", getProgressColor(job.state))}
                  initial={{ width: 0 }}
                  animate={{ width: `${job.progress}%` }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                />
              </div>
              <span className="text-sm font-medium text-gray-900 w-8">
                {job.progress}%
              </span>
            </div>

            <button
              onClick={(e) => {
                e.stopPropagation();
                setExpanded(!expanded);
              }}
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
            >
              {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Expanded details */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="border-t border-gray-100 pt-4 mt-4"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Job details */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Details</h4>
                  <dl className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <dt className="text-gray-500">Progress:</dt>
                      <dd className="text-gray-900">{job.progress}%</dd>
                    </div>
                    <div className="flex justify-between text-xs">
                      <dt className="text-gray-500">Items:</dt>
                      <dd className="text-gray-900">
                        {job.outputs?.filter(o => o.status === 'done').length || 0} / {job.outputs?.length || 0}
                      </dd>
                    </div>
                    {job.error_message && (
                      <div className="col-span-2">
                        <dt className="text-xs text-gray-500 mb-1">Error:</dt>
                        <dd className="text-xs text-red-600 bg-red-50 p-2 rounded">
                          {job.error_message}
                        </dd>
                      </div>
                    )}
                  </dl>
                </div>

                {/* Actions */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Actions</h4>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => onJobAction(job.job_id, 'view')}
                      className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                    >
                      <Eye className="w-3 h-3" />
                      View
                    </button>
                    <button
                      onClick={() => onJobAction(job.job_id, 'download')}
                      className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                      disabled={job.state !== 'done'}
                    >
                      <Download className="w-3 h-3" />
                      Download
                    </button>
                    <button
                      onClick={() => onJobAction(job.job_id, 'retry')}
                      className="flex items-center gap-1 px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 transition-colors"
                      disabled={job.state !== 'error'}
                    >
                      <RefreshCw className="w-3 h-3" />
                      Retry
                    </button>
                    <button
                      onClick={() => onJobAction(job.job_id, 'delete')}
                      className="flex items-center gap-1 px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                    >
                      <Trash2 className="w-3 h-3" />
                      Delete
                    </button>
                  </div>
                </div>
              </div>

              {/* Outputs preview */}
              {job.outputs && job.outputs.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Outputs</h4>
                  <div className="grid grid-cols-10 gap-1">
                    {job.outputs.slice(0, 40).map((output, index) => (
                      <div
                        key={index}
                        className={clsx(
                          "h-2 rounded-xs",
                          output.status === 'done' ? 'bg-green-400' :
                          output.status === 'running' ? 'bg-blue-400' :
                          output.status === 'error' ? 'bg-red-400' :
                          'bg-gray-300'
                        )}
                        title={`Item ${output.id}: ${output.status}`}
                      />
                    ))}
                    {job.outputs.length > 40 && (
                      <div className="h-2 rounded-xs bg-gray-300 flex items-center justify-center">
                        <span className="text-[8px] text-gray-600">+{job.outputs.length - 40}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Metadata */}
              {job.metadata && Object.keys(job.metadata).length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Metadata</h4>
                  <div className="bg-gray-50 p-3 rounded text-xs">
                    {Object.entries(job.metadata).map(([key, value]) => (
                      <div key={key} className="flex justify-between py-1">
                        <span className="text-gray-600">{key}:</span>
                        <span className="text-gray-900 truncate ml-2">
                          {typeof value === 'string' ? value : JSON.stringify(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export const JobPanel: React.FC<JobPanelProps> = ({
  className,
  showCompact = false,
  autoRefresh = true,
  maxJobs = 50,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<FilterState>('all');
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [selectedJobs, setSelectedJobs] = useState<Set<string>>(new Set());
  const [showMonitor, setShowMonitor] = useState(false);

  const {
    activeJobs,
    completedJobs,
    removeJob,
    clearNotifications,
  } = useJobsStore();

  const {
    jobs,
    isLoading,
    isConnected,
    startMonitoring,
    stopMonitoring,
    retryJob,
    activeJobsCount,
    completedJobsCount,
  } = useJobMonitor({
    autoStart: autoRefresh,
  });

  // Combine and filter jobs
  const filteredAndSortedJobs = useMemo(() => {
    let filtered = jobs.filter(job => {
      // Filter by state
      if (selectedFilter !== 'all' && job.state !== selectedFilter) {
        return false;
      }

      // Filter by search query
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          job.job_id.toLowerCase().includes(query) ||
          job.type?.toLowerCase().includes(query) ||
          job.outputs?.some(output =>
            output.id.toLowerCase().includes(query) ||
            output.prompt?.toLowerCase().includes(query)
          )
        );
      }

      return true;
    });

    // Sort jobs
    filtered.sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];

      if (sortField === 'created_at' || sortField === 'updated_at') {
        aValue = new Date(aValue || 0).getTime();
        bValue = new Date(bValue || 0).getTime();
      }

      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      const result = aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      return sortOrder === 'asc' ? result : -result;
    });

    // Limit to maxJobs
    return filtered.slice(0, maxJobs);
  }, [jobs, searchQuery, selectedFilter, sortField, sortOrder, maxJobs]);

  const handleJobAction = async (jobId: string, action: string) => {
    switch (action) {
      case 'view':
        // Open job details modal or navigate to job page
        console.log('View job:', jobId);
        break;
      case 'download':
        // Trigger download
        console.log('Download job:', jobId);
        break;
      case 'retry':
        retryJob(jobId);
        break;
      case 'delete':
        removeJob(jobId);
        break;
      default:
        console.log('Unknown action:', action, jobId);
    }
  };

  const handleSelectJob = (jobId: string) => {
    const newSelected = new Set(selectedJobs);
    if (newSelected.has(jobId)) {
      newSelected.delete(jobId);
    } else {
      newSelected.add(jobId);
    }
    setSelectedJobs(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedJobs.size === filteredAndSortedJobs.length) {
      setSelectedJobs(new Set());
    } else {
      setSelectedJobs(new Set(filteredAndSortedJobs.map(job => job.job_id)));
    }
  };

  const handleBulkDelete = () => {
    selectedJobs.forEach(jobId => {
      removeJob(jobId);
    });
    setSelectedJobs(new Set());
  };

  if (showCompact) {
    return <JobMonitor compact={true} className={className} />;
  }

  return (
    <div className={clsx("bg-gray-50 rounded-xl border border-gray-200", className)}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white rounded-t-xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Job Management</h2>
            <div className="flex items-center gap-4 mt-1">
              <span className="text-sm text-gray-500">
                {activeJobsCount} active
              </span>
              <span className="text-sm text-gray-500">
                {completedJobsCount} completed
              </span>
              <span className="text-sm text-gray-500">
                {filteredAndSortedJobs.length} shown
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowMonitor(!showMonitor)}
              className={clsx(
                "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                showMonitor
                  ? "bg-blue-500 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              )}
            >
              {showMonitor ? 'Hide Monitor' : 'Show Monitor'}
            </button>

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
          </div>
        </div>

        {/* Filters and search */}
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search jobs by ID, type, or content..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* State filter */}
          <select
            value={selectedFilter}
            onChange={(e) => setSelectedFilter(e.target.value as FilterState)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All States</option>
            <option value="queued">Queued</option>
            <option value="running">Running</option>
            <option value="done">Done</option>
            <option value="error">Error</option>
          </select>

          {/* Sort */}
          <select
            value={`${sortField}-${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('-');
              setSortField(field as SortField);
              setSortOrder(order as SortOrder);
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="created_at-desc">Newest First</option>
            <option value="created_at-asc">Oldest First</option>
            <option value="updated_at-desc">Recently Updated</option>
            <option value="progress-desc">Highest Progress</option>
            <option value="progress-asc">Lowest Progress</option>
            <option value="state-asc">State A-Z</option>
          </select>
        </div>

        {/* Connection status */}
        <div className="flex items-center gap-2 mt-3">
          <div className={clsx(
            "w-2 h-2 rounded-full",
            isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"
          )} />
          <span className="text-xs text-gray-500">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
          {isLoading && (
            <Loader2 className="w-3 h-3 text-blue-500 animate-spin ml-2" />
          )}
        </div>
      </div>

      {/* Job Monitor Toggle */}
      <AnimatePresence>
        {showMonitor && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-b border-gray-200"
          >
            <div className="p-4">
              <JobMonitor showControls={false} showStats={false} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bulk actions */}
      {selectedJobs.size > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="px-4 py-2 bg-blue-50 border-b border-blue-200"
        >
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-700">
              {selectedJobs.size} job{selectedJobs.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={handleBulkDelete}
                className="flex items-center gap-1 px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
              >
                <Trash2 className="w-3 h-3" />
                Delete Selected
              </button>
              <button
                onClick={() => setSelectedJobs(new Set())}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Clear Selection
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Jobs list */}
      <div className="p-4">
        {filteredAndSortedJobs.length > 0 ? (
          <div className="space-y-3">
            {/* Select all checkbox */}
            {filteredAndSortedJobs.length > 1 && (
              <div className="flex items-center gap-2 pb-2">
                <input
                  type="checkbox"
                  checked={selectedJobs.size === filteredAndSortedJobs.length}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-600">Select all</span>
              </div>
            )}

            {/* Job rows */}
            <AnimatePresence mode="popLayout">
              {filteredAndSortedJobs.map((job) => (
                <JobRow
                  key={job.job_id}
                  job={job}
                  onJobAction={handleJobAction}
                  isSelected={selectedJobs.has(job.job_id)}
                  onSelect={handleSelectJob}
                  showDetails={true}
                />
              ))}
            </AnimatePresence>
          </div>
        ) : (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <h3 className="text-sm font-medium text-gray-900 mb-1">No jobs found</h3>
            <p className="text-sm text-gray-500">
              {searchQuery || selectedFilter !== 'all'
                ? 'Try adjusting your filters or search query'
                : 'Jobs will appear here when they are created'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobPanel;