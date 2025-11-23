# Example Integration Guide

This guide shows how to integrate the Lovable Job Monitor system into existing pages and applications.

## Quick Start Integration

### 1. Basic Job Status Display

```tsx
// In any React component
import React from 'react';
import { JobMonitor } from '@/components/JobMonitor';

function VideoProcessingPage() {
  // Job ID from your backend or URL parameter
  const jobId = 'job_abc123';

  return (
    <div>
      <h1>Video Processing</h1>
      <p>Your video is being processed...</p>

      {/* Simple job status display */}
      <JobMonitor
        jobId={jobId}
        compact={true}
        autoStart={true}
      />
    </div>
  );
}
```

### 2. Advanced Job Management

```tsx
import React, { useState } from 'react';
import { useJobMonitor } from '@/hooks/useJobMonitor';
import { Button } from '@/components/ui/button';

function BatchProcessingPage() {
  const [jobIds, setJobIds] = useState<string[]>([]);

  const {
    jobs,
    isLoading,
    isConnected,
    startMonitoring,
    stopMonitoring,
    addJob,
  } = useJobMonitor({
    jobIds,
    autoStart: true,
    onJobComplete: (job) => {
      console.log('Processing completed:', job.job_id);
      // Handle completion - maybe redirect to results
    },
    onJobError: (job) => {
      console.error('Processing failed:', job.job_id);
      // Handle error - show error message
    },
  });

  const handleStartProcessing = async () => {
    // Start your backend processing
    const response = await fetch('/api/start-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files: selectedFiles }),
    });

    const { jobId } = await response.json();

    // Add to monitoring
    addJob({
      job_id: jobId,
      state: 'queued',
      progress: 0,
      type: 'render_batch',
      created_at: new Date().toISOString(),
    });

    setJobIds(prev => [...prev, jobId]);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1>Batch Processing</h1>
        <div className="flex gap-2">
          <Button onClick={handleStartProcessing}>
            Start Processing
          </Button>
          <Button
            variant="outline"
            onClick={isConnected ? stopMonitoring : startMonitoring}
          >
            {isConnected ? 'Pause' : 'Resume'} Monitoring
          </Button>
        </div>
      </div>

      {/* Display all jobs */}
      <div className="grid gap-4">
        {jobs.map(job => (
          <div key={job.job_id} className="border rounded-lg p-4">
            <h3>Job {job.job_id}</h3>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${job.progress}%` }}
              />
            </div>
            <p>Status: {job.state}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 3. Integration with Existing Forms

```tsx
import React, { useState } from 'react';
import { useJobMonitor } from '@/hooks/useJobMonitor';
import { toast } from 'sonner';

function ImageGeneratorForm() {
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const { addJob } = useJobMonitor();

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);

    try {
      // Start the generation process
      const response = await fetch('/api/generate-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });

      const { jobId } = await response.json();

      // Add to job monitoring
      addJob({
        job_id: jobId,
        state: 'queued',
        progress: 0,
        type: 'render_batch',
        created_at: new Date().toISOString(),
        metadata: { prompt },
      });

      toast.success('Image generation started!');

      // Optionally redirect to status page
      // router.push(`/status/${jobId}`);

    } catch (error) {
      toast.error('Failed to start generation');
      console.error(error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <form onSubmit={handleGenerate} className="max-w-md mx-auto">
      <h2>Generate Image</h2>

      <div className="mb-4">
        <label htmlFor="prompt" className="block text-sm font-medium mb-2">
          Prompt
        </label>
        <textarea
          id="prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="w-full p-2 border rounded-lg"
          rows={3}
          placeholder="Describe the image you want to generate..."
          required
        />
      </div>

      <button
        type="submit"
        disabled={isGenerating || !prompt.trim()}
        className="w-full bg-blue-500 text-white py-2 rounded-lg disabled:opacity-50"
      >
        {isGenerating ? 'Starting...' : 'Generate Image'}
      </button>
    </form>
  );
}
```

### 4. Global Integration (App-wide)

```tsx
// In your main App.tsx or layout component
import React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { NotificationProvider } from '@/components/NotificationSystem';
import { NotificationCenter } from '@/components/NotificationSystem';
import { JobPanel } from '@/components/JobPanel';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <NotificationProvider>
        {/* Your existing app layout */}
        <Header>
          <Logo />
          <Navigation />
          <NotificationCenter />
        </Header>

        <MainContent>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/create" element={<CreatePage />} />
            <Route path="/jobs" element={<JobsPage />} />
          </Routes>
        </MainContent>

        {/* Optional: Global job management */}
        {process.env.NODE_ENV === 'development' && (
          <div className="fixed bottom-4 right-4 z-50">
            <JobPanel compact={true} />
          </div>
        )}
      </NotificationProvider>
    </QueryClientProvider>
  );
}

// Dedicated jobs page
function JobsPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-6">Job Management</h1>
      <JobPanel />
    </div>
  );
}
```

### 5. Status Page Integration

```tsx
// pages/status/[jobId].tsx
import React from 'react';
import { useRouter } from 'next/router';
import { JobMonitor } from '@/components/JobMonitor';
import { Button } from '@/components/ui/button';

export default function JobStatusPage() {
  const router = useRouter();
  const { jobId } = router.query;

  if (!jobId || typeof jobId !== 'string') {
    return <div>Invalid job ID</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="mb-6">
          <Button
            variant="outline"
            onClick={() => router.back()}
            className="mb-4"
          >
            ← Back
          </Button>

          <h1 className="text-3xl font-bold">Job Status</h1>
          <p className="text-gray-600">Job ID: {jobId}</p>
        </div>

        <JobMonitor
          jobId={jobId}
          autoStart={true}
          showControls={true}
          showStats={true}
          onJobComplete={(job) => {
            // Redirect to results or show completion UI
            console.log('Job completed!', job);
          }}
          onJobError={(job) => {
            // Show error UI
            console.error('Job failed!', job);
          }}
        />

        {/* Additional job-specific actions */}
        <div className="mt-8 p-6 bg-white rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Actions</h2>
          <div className="flex gap-4">
            <Button onClick={() => window.location.reload()}>
              Refresh Status
            </Button>
            <Button variant="outline" onClick={() => navigator.clipboard.writeText(jobId!)}>
              Copy Job ID
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

### 6. Custom Job Type Integration

```tsx
// For custom job types, extend the type definitions
interface CustomJobStatus extends JobStatus {
  type: 'custom_processing';
  customData: {
    inputFile: string;
    outputFile?: string;
    processingSteps: string[];
  };
}

function CustomJobMonitor({ jobId }: { jobId: string }) {
  const { jobs } = useJobMonitor({
    jobId,
    onStatusChange: (job, previousState) => {
      // Custom logic for status changes
      if (job.type === 'custom_processing') {
        const customJob = job as CustomJobStatus;
        console.log('Processing step:', customJob.customData.processingSteps);
      }
    },
  });

  const job = jobs.find(j => j.job_id === jobId) as CustomJobStatus;

  if (!job) return <div>Job not found</div>;

  return (
    <div>
      {/* Standard job display */}
      <JobMonitor jobId={jobId} compact={true} />

      {/* Custom job-specific display */}
      {job.customData && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <h3>Processing Details</h3>
          <p>Input: {job.customData.inputFile}</p>
          {job.customData.outputFile && (
            <p>Output: {job.customData.outputFile}</p>
          )}

          <div className="mt-2">
            <h4>Processing Steps:</h4>
            <ul className="list-disc list-inside">
              {job.customData.processingSteps.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
```

## Configuration Examples

### Environment Variables

```env
# .env.local
VITE_API_URL=https://your-api.com
VITE_API_KEY=your-secure-api-key
VITE_DEFAULT_POLLING_INTERVAL=2000  # 2 seconds
VITE_MAX_ACTIVE_JOBS=20
VITE_ENABLE_DEBUG=false
```

### Custom Default Configuration

```tsx
// src/config/monitoring.ts
import { JobMonitorConfig } from '@/types/job';

export const defaultMonitoringConfig: JobMonitorConfig = {
  pollingInterval: 2000,        // Check every 2 seconds
  maxRetries: 5,                // Retry 5 times
  retryDelay: 1500,            // 1.5 second delays
  enableNotifications: true,    // Show notifications
  persistToLocalStorage: true,  // Save state locally
  maxActiveJobs: 15,           // Track 15 jobs max
  cleanupAfterHours: 12,       // Clean up after 12 hours
};
```

### Integration with Existing State Management

```tsx
// If you use Redux, Zustand, or other state management
import { useDispatch } from 'react-redux';
import { addJob as addJobToRedux } from '@/store/jobsSlice';
import { useJobMonitor } from '@/hooks/useJobMonitor';

function ExistingComponent() {
  const dispatch = useDispatch();
  const { addJob: addJobToMonitor } = useJobMonitor();

  const handleJobCreated = (jobData: JobStatus) => {
    // Add to both your existing store and job monitor
    dispatch(addJobToRedux(jobData));
    addJobToMonitor(jobData);
  };

  return (
    // Your component JSX
  );
}
```

## Best Practices

1. **Always provide job IDs**: Ensure your backend returns unique job IDs
2. **Handle offline scenarios**: Implement offline detection and graceful degradation
3. **Use appropriate polling intervals**: Balance real-time updates with server load
4. **Implement error boundaries**: Wrap components in error boundaries for better UX
5. **Clean up old jobs**: Implement cleanup to prevent memory leaks
6. **Test with different network conditions**: Test slow and unreliable connections
7. **Monitor performance**: Keep an eye on memory usage and performance metrics

## Troubleshooting

### Common Issues

1. **Jobs not updating**: Check API connectivity and CORS configuration
2. **Memory leaks**: Ensure proper cleanup in useEffect hooks
3. **Performance issues**: Reduce polling frequency or limit concurrent jobs
4. **Type errors**: Ensure proper TypeScript types are imported
5. **State inconsistencies**: Check for multiple state management conflicts

### Debug Mode

Enable debug mode for detailed logging:

```env
VITE_ENABLE_DEBUG=true
```

This will provide detailed console logs for:
- API requests and responses
- Job state changes
- Cache operations
- Connection status changes