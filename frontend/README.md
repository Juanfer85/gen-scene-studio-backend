# Lovable Job Monitor - Real-time Job Monitoring System

A comprehensive real-time job monitoring system for Lovable frontend applications. Built with React, TypeScript, and modern web technologies.

## 🚀 Features

### Core Functionality
- **Real-time Job Monitoring**: WebSocket-like polling system for live job status updates
- **Multiple Job Types**: Support for render_batch, compose, and TTS jobs
- **Visual Progress Tracking**: Animated progress bars and status indicators
- **Smart Caching**: Intelligent caching system to minimize API calls
- **Error Handling**: Robust error handling with retry mechanisms

### User Interface
- **Job Monitor Component**: Clean, responsive component for displaying job status
- **Job Panel**: Advanced management interface with filtering, sorting, and bulk operations
- **Notification System**: Real-time notifications for job state changes
- **Compact Views**: Both detailed and compact display modes
- **Demo System**: Built-in demo creator for testing

### Technical Features
- **TypeScript**: Full type safety throughout the application
- **React Query**: Advanced data fetching and caching with TanStack Query
- **Zustand**: Lightweight state management
- **Framer Motion**: Smooth animations and transitions
- **Tailwind CSS**: Utility-first CSS framework
- **Local Storage**: Persistent state across browser sessions

## Prerequisites

- Node.js (v18 or higher)
- npm or yarn
- Backend server running on `http://localhost:8000`

## Getting Started

### 1. Install Dependencies

```bash
npm install
# or
yarn install
```

### 2. Environment Configuration

Copy the environment template and configure your variables:

```bash
cp .env.example .env.local
```

Edit `.env.local` with your configuration:

```env
# Required
VITE_API_URL=http://localhost:8000
VITE_API_KEY=your_api_key_here

# Optional
VITE_API_TIMEOUT=30000
VITE_DEBUG=true
VITE_DEFAULT_POLLING_INTERVAL=3000
VITE_MAX_ACTIVE_JOBS=10
```

### 3. Start Development Server

```bash
npm run dev
# or
yarn dev
```

The application will be available at `http://localhost:3000`.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | Yes | - | Backend API URL |
| `VITE_API_KEY` | Yes | - | GenScene API authentication key |
| `VITE_API_TIMEOUT` | No | 30000 | API request timeout in milliseconds |
| `VITE_DEBUG` | No | false | Enable debug logging |
| `VITE_DEFAULT_POLLING_INTERVAL` | No | 3000 | Job status polling interval (ms) |
| `VITE_MAX_ACTIVE_JOBS` | No | 10 | Maximum concurrent jobs to track |

## Security Notes

- **Never commit** `.env.local` or any `.env` files to version control
- API keys are stored securely in environment variables
- All environment variables are prefixed with `VITE_` to be exposed to the frontend
- CORS is properly configured for development

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Type check without emitting files

## API Integration

The frontend communicates with the following backend endpoints:

- `/api/tts` - Text-to-Speech conversion
- `/api/compose` - Video composition
- `/api/status` - Job status checking
- `/api/compose-result` - Composition results

## 🎯 Usage

### Basic Implementation

```tsx
import React from 'react';
import { JobMonitor } from '@/components/JobMonitor';

function MyComponent() {
  return (
    <JobMonitor
      jobId="your-job-id"
      autoStart={true}
      showControls={true}
      showStats={true}
    />
  );
}
```

### Advanced Usage with Hook

```tsx
import React from 'react';
import { useJobMonitor } from '@/hooks/useJobMonitor';

function MyComponent() {
  const {
    jobs,
    isLoading,
    isConnected,
    startMonitoring,
    stopMonitoring,
    activeJobsCount,
  } = useJobMonitor({
    jobId: 'your-job-id',
    autoStart: true,
    config: {
      pollingInterval: 2000,
      enableNotifications: true,
    },
    onJobComplete: (job) => {
      console.log('Job completed:', job);
    },
    onJobError: (job) => {
      console.error('Job failed:', job);
    },
  });

  return (
    <div>
      <div>Active Jobs: {activeJobsCount}</div>
      <div>Status: {isConnected ? 'Connected' : 'Disconnected'}</div>
      <button onClick={isConnected ? stopMonitoring : startMonitoring}>
        {isConnected ? 'Stop' : 'Start'} Monitoring
      </button>
    </div>
  );
}
```

### Job Panel with Full Management

```tsx
import React from 'react';
import JobPanel from '@/components/JobPanel';

function JobsPage() {
  return (
    <JobPanel
      showCompact={false}
      autoRefresh={true}
      maxJobs={50}
    />
  );
}
```

## 🧩 Components

### JobMonitor
The main component for displaying real-time job status.

**Props:**
- `jobId?: string` - Single job ID to monitor
- `jobIds?: string[]` - Multiple job IDs to monitor
- `autoStart?: boolean` - Start monitoring automatically
- `showControls?: boolean` - Show control buttons
- `showStats?: boolean` - Show statistics
- `compact?: boolean` - Use compact display mode

### JobPanel
Advanced job management interface with filtering and actions.

**Props:**
- `showCompact?: boolean` - Use compact mode
- `autoRefresh?: boolean` - Enable auto-refresh
- `maxJobs?: number` - Maximum jobs to display

### NotificationCenter
Toast notification system for job events.

**Usage:**
```tsx
import { NotificationCenter } from '@/components/NotificationSystem';

function App() {
  return (
    <>
      <YourApp />
      <NotificationCenter maxVisible={5} />
    </>
  );
}
```

## 🔧 Hooks

### useJobMonitor
The main hook for job monitoring functionality.

**Returns:**
- `jobs: JobStatus[]` - All monitored jobs
- `isLoading: boolean` - Loading state
- `isConnected: boolean` - Connection status
- `activeJobsCount: number` - Number of active jobs
- `startMonitoring/stopMonitoring` - Control functions
- Event callbacks for job completion/errors

### useJobsStore
Zustand store for global job state management.

**Methods:**
- `addJob(job: JobStatus)` - Add a job to monitor
- `updateJob(jobId: string, updates: Partial<JobStatus>)` - Update job
- `removeJob(jobId: string)` - Remove job from monitoring
- `addNotification(notification)` - Add notification
- `updateConfig(config)` - Update configuration

## 🏗️ Project Structure

```
src/
├── components/
│   ├── JobMonitor.tsx        # Main job monitoring component
│   ├── JobPanel.tsx          # Advanced job management interface
│   ├── NotificationSystem.tsx # Toast notification system
│   ├── DemoJobsCreator.tsx   # Demo system for testing
│   └── ConfigurationPanel.tsx # Settings and configuration
├── hooks/
│   └── useJobMonitor.ts      # Main monitoring hook
├── services/
│   └── api.ts               # API client with caching
├── store/
│   └── jobsStore.ts         # Zustand state management
├── types/
│   └── job.ts               # Job-related type definitions
├── lib/
│   └── queryClient.ts       # React Query configuration
├── utils/
│   └── helpers.ts           # Utility functions
└── [main.tsx, App.tsx, index.css] # Application entry points
```

## Development

The project uses:

- **Vite** for fast development and building
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Zustand** for state management
- **Axios** for API communication
- **React Query** for server state management

## CORS Configuration

The development server is configured with proxy settings to handle CORS issues:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      secure: false,
    },
  },
}
```

## Build and Deployment

For production deployment:

1. Set production environment variables
2. Build the application:

```bash
npm run build
```

3. Deploy the `dist/` folder to your hosting provider

The build process includes:

- TypeScript compilation
- Code splitting
- Asset optimization
- Environment variable injection

## Troubleshooting

### API Connection Issues

1. Verify the backend is running on `http://localhost:8000`
2. Check your API key in `.env.local`
3. Ensure CORS is properly configured on the backend

### Environment Variables Not Working

1. Make sure all frontend variables are prefixed with `VITE_`
2. Restart the development server after changing `.env.local`
3. Check that `.env.local` is not tracked by git

### TypeScript Errors

Run the type checker:

```bash
npm run type-check
```

## Contributing

1. Follow the existing code style
2. Use TypeScript strictly
3. Add proper type definitions for new features
4. Test environment variable changes