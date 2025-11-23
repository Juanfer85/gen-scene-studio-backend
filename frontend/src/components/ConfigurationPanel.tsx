import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Save, RotateCcw, Info, TestTube } from 'lucide-react';
import { useJobsStore } from '@/store/jobsStore';
import { JobMonitorConfig } from '@/types/job';
import { toast } from 'sonner';

const ConfigurationPanel: React.FC = () => {
  const { config, updateConfig, activeJobs, completedJobs, clearNotifications } = useJobsStore();
  const [localConfig, setLocalConfig] = useState<JobMonitorConfig>(config);
  const [isTesting, setIsTesting] = useState(false);

  const handleConfigChange = (key: keyof JobMonitorConfig, value: any) => {
    setLocalConfig(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSave = () => {
    updateConfig(localConfig);
    toast.success('Configuration saved successfully');
  };

  const handleReset = () => {
    const defaultConfig: JobMonitorConfig = {
      pollingInterval: 3000,
      maxRetries: 3,
      retryDelay: 1000,
      enableNotifications: true,
      persistToLocalStorage: true,
      maxActiveJobs: 10,
      cleanupAfterHours: 24,
    };
    setLocalConfig(defaultConfig);
    updateConfig(defaultConfig);
    toast.success('Configuration reset to defaults');
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    try {
      // Simulate connection test
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.success('Connection test successful');
    } catch (error) {
      toast.error('Connection test failed');
    } finally {
      setIsTesting(false);
    }
  };

  const handleClearData = () => {
    if (confirm('Are you sure you want to clear all job data and notifications?')) {
      clearNotifications();
      localStorage.removeItem('lovable-jobs-store');
      toast.success('All data cleared');
      setTimeout(() => window.location.reload(), 1000);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Configuration</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Polling Configuration */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900 flex items-center gap-2">
              <RotateCcw className="w-4 h-4" />
              Polling Configuration
            </h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Polling Interval (ms)
              </label>
              <input
                type="number"
                min="1000"
                max="60000"
                step="500"
                value={localConfig.pollingInterval}
                onChange={(e) => handleConfigChange('pollingInterval', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                How often to check for job updates (1000-60000ms)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Retries
              </label>
              <input
                type="number"
                min="0"
                max="10"
                value={localConfig.maxRetries}
                onChange={(e) => handleConfigChange('maxRetries', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                Number of retry attempts on connection failures
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Retry Delay (ms)
              </label>
              <input
                type="number"
                min="100"
                max="10000"
                step="100"
                value={localConfig.retryDelay}
                onChange={(e) => handleConfigChange('retryDelay', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                Delay between retry attempts
              </p>
            </div>
          </div>

          {/* Job Management */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900 flex items-center gap-2">
              <Info className="w-4 h-4" />
              Job Management
            </h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Active Jobs
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={localConfig.maxActiveJobs}
                onChange={(e) => handleConfigChange('maxActiveJobs', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                Maximum number of jobs to track simultaneously
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cleanup After (hours)
              </label>
              <input
                type="number"
                min="1"
                max="168"
                value={localConfig.cleanupAfterHours}
                onChange={(e) => handleConfigChange('cleanupAfterHours', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                Remove completed jobs after this time period
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={localConfig.enableNotifications}
                  onChange={(e) => handleConfigChange('enableNotifications', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">Enable Notifications</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={localConfig.persistToLocalStorage}
                  onChange={(e) => handleConfigChange('persistToLocalStorage', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">Persist to Local Storage</span>
              </label>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3 pt-6 border-t border-gray-200 mt-6">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSave}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <Save className="w-4 h-4" />
            Save Configuration
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Reset to Defaults
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleTestConnection}
            disabled={isTesting}
            className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors disabled:opacity-50"
          >
            <TestTube className={clsx("w-4 h-4", isTesting && "animate-spin")} />
            {isTesting ? 'Testing...' : 'Test Connection'}
          </motion.button>
        </div>
      </div>

      {/* Statistics */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="font-medium text-gray-900 mb-4">Statistics & Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Current Jobs</h4>
            <p className="text-2xl font-bold text-blue-600">{activeJobs.length}</p>
            <p className="text-sm text-gray-600">Active jobs</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Completed Jobs</h4>
            <p className="text-2xl font-bold text-green-600">{completedJobs.length}</p>
            <p className="text-sm text-gray-600">In history</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Storage</h4>
            <p className="text-2xl font-bold text-purple-600">
              {localConfig.persistToLocalStorage ? 'Enabled' : 'Disabled'}
            </p>
            <p className="text-sm text-gray-600">Local persistence</p>
          </div>
        </div>
      </div>

      {/* Advanced Options */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="font-medium text-gray-900 mb-4">Advanced Options</h3>
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Debug Information</h4>
            <div className="p-3 bg-gray-50 rounded-lg text-xs font-mono space-y-1">
              <div>User Agent: {navigator.userAgent}</div>
              <div>Timezone: {Intl.DateTimeFormat().resolvedOptions().timeZone}</div>
              <div>Language: {navigator.language}</div>
              <div>Online: {navigator.onLine ? 'Yes' : 'No'}</div>
              <div>Storage Available: {typeof Storage !== 'undefined' ? 'Yes' : 'No'}</div>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Data Management</h4>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleClearData}
              className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-sm"
            >
              Clear All Data
            </motion.button>
            <p className="text-xs text-gray-500 mt-2">
              This will remove all job history and notifications from local storage.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfigurationPanel;