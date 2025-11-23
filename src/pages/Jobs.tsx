import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { Input } from '@/components/ui/Input';
import { Briefcase, Search, RefreshCw, Download, Eye, CheckCircle, XCircle, Clock, Filter, Trash2 } from 'lucide-react';
import { usePolling } from '@/hooks/usePolling';
import apiClient from '@/lib/api';
import { JobStatusOut, RenderItemOut } from '@/types';

interface JobWithDetails extends JobStatusOut {
  createdAt: string;
  type: 'render' | 'compose' | 'tts';
  metadata?: any;
}

const Jobs: React.FC = () => {
  const [jobs, setJobs] = useState<JobWithDetails[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobWithDetails | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(5000);

  // Load jobs from localStorage and API on mount
  useEffect(() => {
    loadJobs();
  }, []);

  // Auto-refresh functionality
  const { data: refreshedJobs, loading: refreshLoading } = usePolling(
    async () => {
      if (!autoRefresh || !jobs.length) return null;

      const updatedJobs = await Promise.all(
        jobs.map(async (job) => {
          try {
            const status = await apiClient.getJobStatus(job.job_id);
            return { ...job, ...status };
          } catch (error) {
            console.error(`Error refreshing job ${job.job_id}:`, error);
            return job;
          }
        })
      );

      return updatedJobs;
    },
    [autoRefresh, jobs],
    {
      interval: refreshInterval,
      immediate: false,
      onSuccess: (updatedJobs) => {
        if (updatedJobs) {
          setJobs(updatedJobs);
        }
      }
    }
  );

  const loadJobs = async () => {
    // Load from localStorage first
    const savedJobs = localStorage.getItem('jobs');
    if (savedJobs) {
      const parsedJobs = JSON.parse(savedJobs);
      setJobs(parsedJobs);

      // Try to refresh status for active jobs
      const activeJobs = parsedJobs.filter((job: JobWithDetails) =>
        ['queued', 'running'].includes(job.state)
      );

      if (activeJobs.length > 0) {
        const refreshedJobs = await Promise.all(
          activeJobs.map(async (job: JobWithDetails) => {
            try {
              const status = await apiClient.getJobStatus(job.job_id);
              return { ...job, ...status };
            } catch (error) {
              return job;
            }
          })
        );

        // Update jobs with refreshed data
        setJobs(prev =>
          prev.map(job => {
            const refreshed = refreshedJobs.find(rj => rj.job_id === job.job_id);
            return refreshed || job;
          })
        );
      }
    }
  };

  const saveJobs = (jobsToSave: JobWithDetails[]) => {
    localStorage.setItem('jobs', JSON.stringify(jobsToSave));
    setJobs(jobsToSave);
  };

  const addJob = (jobData: Partial<JobWithDetails>) => {
    const newJob: JobWithDetails = {
      job_id: jobData.job_id || `job_${Date.now()}`,
      state: jobData.state || 'idle',
      progress: jobData.progress || 0,
      outputs: jobData.outputs || [],
      createdAt: jobData.createdAt || new Date().toISOString(),
      type: jobData.type || 'render',
      metadata: jobData.metadata
    };

    saveJobs([...jobs, newJob]);
  };

  const removeJob = (jobId: string) => {
    if (confirm('¿Estás seguro de eliminar este trabajo?')) {
      saveJobs(jobs.filter(job => job.job_id !== jobId));
      if (selectedJob?.job_id === jobId) {
        setSelectedJob(null);
      }
    }
  };

  const refreshJob = async (jobId: string) => {
    try {
      const status = await apiClient.getJobStatus(jobId);
      setJobs(prev => prev.map(job =>
        job.job_id === jobId ? { ...job, ...status } : job
      ));

      if (selectedJob?.job_id === jobId) {
        setSelectedJob(prev => prev ? { ...prev, ...status } : null);
      }
    } catch (error) {
      console.error(`Error refreshing job ${jobId}:`, error);
    }
  };

  const refreshAllJobs = async () => {
    for (const job of jobs) {
      await refreshJob(job.job_id);
    }
  };

  const getComposeResult = async (jobId: string) => {
    try {
      const result = await apiClient.getComposeResult(jobId);
      return result;
    } catch (error) {
      console.error(`Error getting compose result for ${jobId}:`, error);
      return null;
    }
  };

  const filteredJobs = jobs.filter(job => {
    const matchesSearch = job.job_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         job.metadata?.name?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = filterStatus === 'all' || job.state === filterStatus;
    const matchesType = filterType === 'all' || job.type === filterType;

    return matchesSearch && matchesStatus && matchesType;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'queued':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'done':
        return 'text-green-600 bg-green-50';
      case 'error':
        return 'text-red-600 bg-red-50';
      case 'running':
        return 'text-blue-600 bg-blue-50';
      case 'queued':
        return 'text-yellow-600 bg-yellow-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'render':
        return 'Renderizado';
      case 'compose':
        return 'Composición';
      case 'tts':
        return 'Voz (TTS)';
      default:
        return type;
    }
  };

  const getJobStats = () => {
    const stats = {
      total: jobs.length,
      idle: jobs.filter(j => j.state === 'idle').length,
      queued: jobs.filter(j => j.state === 'queued').length,
      running: jobs.filter(j => j.state === 'running').length,
      done: jobs.filter(j => j.state === 'done').length,
      error: jobs.filter(j => j.state === 'error').length
    };
    return stats;
  };

  const stats = getJobStats();

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-foreground">Monitor de Trabajos</h1>
          <p className="text-muted-foreground">Visualiza y gestiona el estado de todos tus trabajos</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{stats.total}</div>
              <div className="text-xs text-muted-foreground">Total</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-yellow-600">{stats.queued}</div>
              <div className="text-xs text-muted-foreground">En Cola</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-blue-600">{stats.running}</div>
              <div className="text-xs text-muted-foreground">Ejecutando</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-green-600">{stats.done}</div>
              <div className="text-xs text-muted-foreground">Completados</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-red-600">{stats.error}</div>
              <div className="text-xs text-muted-foreground">Errores</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-gray-600">{stats.idle}</div>
              <div className="text-xs text-muted-foreground">Inactivos</div>
            </CardContent>
          </Card>
        </div>

        {/* Controls */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filtros y Controles
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Buscar</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Buscar por ID o nombre..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Estado</label>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                >
                  <option value="all">Todos</option>
                  <option value="idle">Inactivos</option>
                  <option value="queued">En Cola</option>
                  <option value="running">Ejecutando</option>
                  <option value="done">Completados</option>
                  <option value="error">Errores</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Tipo</label>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                >
                  <option value="all">Todos</option>
                  <option value="render">Renderizado</option>
                  <option value="compose">Composición</option>
                  <option value="tts">Voz (TTS)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Auto-refresh</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="autoRefresh"
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                    className="h-4 w-4 border border-input rounded bg-background text-primary focus:ring-2 focus:ring-ring focus:ring-offset-2"
                  />
                  <label htmlFor="autoRefresh" className="text-sm">
                    Cada {refreshInterval / 1000}s
                  </label>
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={refreshAllJobs}
                loading={refreshLoading}
                size="sm"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Actualizar Todos
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Jobs List */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Briefcase className="h-5 w-5" />
                  Trabajos ({filteredJobs.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 max-h-96 overflow-y-auto">
                {filteredJobs.map((job) => (
                  <div
                    key={job.job_id}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedJob?.job_id === job.job_id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:bg-muted'
                    }`}
                    onClick={() => setSelectedJob(job)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(job.state)}
                        <div className="text-sm font-medium truncate">
                          {job.metadata?.name || job.job_id}
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeJob(job.job_id);
                        }}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {getTypeLabel(job.type)} • {new Date(job.createdAt).toLocaleDateString()}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {job.outputs?.length || 0} items
                    </div>
                    {job.state !== 'idle' && (
                      <div className="mt-2">
                        <Progress value={job.progress} className="h-1" />
                      </div>
                    )}
                  </div>
                ))}

                {filteredJobs.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground text-sm">
                    No se encontraron trabajos con los filtros actuales
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Job Details */}
          <div className="lg:col-span-2">
            {selectedJob ? (
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {getStatusIcon(selectedJob.state)}
                      {selectedJob.metadata?.name || selectedJob.job_id}
                    </CardTitle>
                    <CardDescription>
                      {getTypeLabel(selectedJob.type)} • ID: {selectedJob.job_id}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Estado:</span>
                        <div className={`px-2 py-1 rounded-full text-xs font-medium inline-block mt-1 ${getStatusColor(selectedJob.state)}`}>
                          {selectedJob.state.toUpperCase()}
                        </div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Progreso:</span>
                        <div className="font-medium">{selectedJob.progress}%</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Creado:</span>
                        <div className="font-medium">
                          {new Date(selectedJob.createdAt).toLocaleString()}
                        </div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Items:</span>
                        <div className="font-medium">{selectedJob.outputs?.length || 0}</div>
                      </div>
                    </div>

                    {selectedJob.state !== 'idle' && (
                      <div>
                        <div className="flex justify-between text-sm mb-2">
                          <span>Progreso</span>
                          <span>{selectedJob.progress}%</span>
                        </div>
                        <Progress value={selectedJob.progress} />
                      </div>
                    )}

                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => refreshJob(selectedJob.job_id)}
                      >
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Actualizar
                      </Button>

                      {selectedJob.type === 'render' && selectedJob.state === 'done' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            const urls = selectedJob.outputs?.filter(o => o.url).map(o => o.url) || [];
                            urls.forEach((url, index) => {
                              const link = document.createElement('a');
                              link.href = url;
                              link.download = `${selectedJob.job_id}_item_${index + 1}.png`;
                              document.body.appendChild(link);
                              link.click();
                              document.body.removeChild(link);
                            });
                          }}
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Descargar Todos
                        </Button>
                      )}

                      {selectedJob.type === 'compose' && selectedJob.state === 'done' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={async () => {
                            const result = await getComposeResult(selectedJob.job_id);
                            if (result?.video_url) {
                              const link = document.createElement('a');
                              link.href = result.video_url;
                              link.download = `${selectedJob.job_id}.mp4`;
                              document.body.appendChild(link);
                              link.click();
                              document.body.removeChild(link);
                            }
                          }}
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Descargar Video
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Outputs */}
                {selectedJob.outputs && selectedJob.outputs.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Outputs</CardTitle>
                      <CardDescription>
                        {selectedJob.outputs.length} elementos generados
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 max-h-96 overflow-y-auto">
                        {selectedJob.outputs.map((output, index) => (
                          <div
                            key={output.id}
                            className="flex items-center justify-between p-3 border border-border rounded-lg"
                          >
                            <div className="flex-1">
                              <div className="font-medium text-sm">
                                Item {index + 1}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                ID: {output.id} • Hash: {output.hash?.substring(0, 8)}...
                              </div>
                              <div className="text-xs text-muted-foreground">
                                Calidad: {output.quality}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {getStatusIcon(output.status)}
                              <div className="text-xs text-muted-foreground">
                                {output.status}
                              </div>
                              {output.url && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => window.open(output.url!, '_blank')}
                                >
                                  <Eye className="h-3 w-3" />
                                </Button>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-12">
                    <Briefcase className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-foreground mb-2">
                      Selecciona un trabajo
                    </h3>
                    <p className="text-muted-foreground">
                      Elige un trabajo de la lista para ver sus detalles
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Jobs;