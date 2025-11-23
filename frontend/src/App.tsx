import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';
import { Settings, Monitor, Zap, Code, TestTube, Download, Upload, Image, Volume2, Film } from 'lucide-react';
import { useJobsStore } from './store/jobsStore';
import { useJobMonitor } from './hooks/useJobMonitor';
import JobMonitor from './components/JobMonitor';
import JobPanel from './components/JobPanel';
import NotificationCenter from './components/NotificationSystem';
import { generateJobId } from './utils/helpers';
import { JobStatus, JobState } from './types/job';

// Demo components
import DemoJobsCreator from './components/DemoJobsCreator';
import ConfigurationPanel from './components/ConfigurationPanel';

// WhatIf Video Generation components
import { Voz } from './components/Voz';
import { Storyboard } from './components/Storyboard';
import { Timeline } from './components/Timeline';

function App() {
  const [activeTab, setActiveTab] = useState<'voz' | 'storyboard' | 'timeline' | 'panel' | 'monitor' | 'demo' | 'config'>('voz');
  const { isConnected, activeJobsCount, completedJobsCount, notifications } = useJobsStore();

  // Demo: Add some sample jobs on mount
  useEffect(() => {
    if (activeJobsCount === 0 && completedJobsCount === 0) {
      addSampleJobs();
    }
  }, []);

  const addSampleJobs = () => {
    const sampleJobs: JobStatus[] = [
      {
        job_id: generateJobId(),
        state: 'running',
        progress: 45,
        type: 'render_batch',
        created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
        outputs: [
          { id: '1', prompt: 'Beautiful landscape', negative: 'blurry', seed: 123, quality: 'draft', status: 'done', url: 'https://example.com/1.jpg' },
          { id: '2', prompt: 'City skyline', negative: 'dark', seed: 456, quality: 'draft', status: 'running', url: null },
          { id: '3', prompt: 'Forest path', negative: 'desert', seed: 789, quality: 'draft', status: 'queued', url: null },
        ],
        metadata: { model: 'stable-diffusion-xl', aspectRatio: '16:9' },
      },
      {
        job_id: generateJobId(),
        state: 'queued',
        progress: 0,
        type: 'compose',
        created_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
        metadata: { duration: '30s', resolution: '1920x1080' },
      },
      {
        job_id: generateJobId(),
        state: 'done',
        progress: 100,
        type: 'render_batch',
        created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        updated_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
        outputs: [
          { id: '1', prompt: 'Portrait', negative: 'cartoon', seed: 111, quality: 'upscale', status: 'done', url: 'https://example.com/portrait.jpg' },
          { id: '2', prompt: 'Abstract art', negative: 'realistic', seed: 222, quality: 'upscale', status: 'done', url: 'https://example.com/abstract.jpg' },
        ],
        metadata: { model: 'stable-diffusion-xl', aspectRatio: '1:1' },
      },
    ];

    const { addJob } = useJobsStore.getState();
    sampleJobs.forEach(job => addJob(job));
  };

  const tabs = [
    { id: 'voz' as const, label: '🎤 Voz AI', icon: Volume2 },
    { id: 'storyboard' as const, label: '🎨 Storyboard', icon: Image },
    { id: 'timeline' as const, label: '🎬 Timeline', icon: Film },
    { id: 'panel' as const, label: 'Jobs', icon: Monitor },
    { id: 'monitor' as const, label: 'Monitor', icon: Zap },
    { id: 'demo' as const, label: 'Demo', icon: TestTube },
    { id: 'config' as const, label: 'Config', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Film className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-xl font-bold text-gray-900">WhatIf Video Generation</h1>
              </div>

              {/* Status indicators */}
              <div className="hidden sm:flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1">
                  <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                  <span className="text-gray-600">{isConnected ? 'Connected' : 'Disconnected'}</span>
                </div>
                <span className="text-gray-400">•</span>
                <span className="text-gray-600">{activeJobsCount} active</span>
                <span className="text-gray-400">•</span>
                <span className="text-gray-600">{completedJobsCount} completed</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <NotificationCenter />
              <a
                href="https://github.com/lovable/job-monitor"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
              >
                <Download className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={clsx(
                    'flex items-center gap-2 px-1 py-4 border-b-2 text-sm font-medium transition-colors',
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === 'voz' && <Voz />}
          {activeTab === 'storyboard' && <Storyboard />}
          {activeTab === 'timeline' && <Timeline />}
          {activeTab === 'panel' && <JobPanel />}
          {activeTab === 'monitor' && (
            <div className="space-y-6">
              <JobMonitor />
              <JobMonitor compact={true} />
            </div>
          )}
          {activeTab === 'demo' && <DemoJobsCreator />}
          {activeTab === 'config' && <ConfigurationPanel />}
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-gray-500">
              Real-time job monitoring system for Lovable applications
            </p>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>Built with React, TypeScript, and Tailwind CSS</span>
              <span>•</span>
              <span>v1.0.0</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;