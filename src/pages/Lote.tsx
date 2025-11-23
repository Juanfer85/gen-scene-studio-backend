import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { Input } from '@/components/ui/Input';
import { Package, Upload, Download, Play, Pause, CheckCircle, XCircle, Clock, RefreshCw, AlertCircle } from 'lucide-react';
import { useApiCall } from '@/hooks/useApiCall';
import { usePolling } from '@/hooks/usePolling';
import apiClient from '@/lib/api';
import { RenderBatchIn, RenderItemIn, JobStatusOut, Quality } from '@/types';

interface BatchJob {
  id: string;
  name: string;
  status: 'idle' | 'queued' | 'running' | 'done' | 'error';
  progress: number;
  items: RenderItemIn[];
  createdAt: string;
  completedAt?: string;
  outputs?: any[];
}

const Lote: React.FC = () => {
  const [batchJobs, setBatchJobs] = useState<BatchJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<BatchJob | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newJobName, setNewJobName] = useState('');
  const [csvContent, setCsvContent] = useState('');
  const [model, setModel] = useState('kolors');
  const [aspectRatio, setAspectRatio] = useState('16:9');

  // Load jobs from localStorage on mount
  useEffect(() => {
    const savedJobs = localStorage.getItem('batchJobs');
    if (savedJobs) {
      setBatchJobs(JSON.parse(savedJobs));
    }
  }, []);

  // Save jobs to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('batchJobs', JSON.stringify(batchJobs));
  }, [batchJobs]);

  const {
    execute: processBatch,
    loading: processingBatch,
    error: batchError
  } = useApiCall(
    (payload: RenderBatchIn) => apiClient.renderBatch(payload),
    {
      onSuccess: (result) => {
        console.log('Batch processing started:', result);
        // Update job status to queued
        if (selectedJob) {
          setBatchJobs(prev => prev.map(job =>
            job.id === selectedJob.id
              ? { ...job, status: 'queued' as const, progress: 0 }
              : job
          ));
        }
      },
      onError: (error) => {
        console.error('Error processing batch:', error);
        if (selectedJob) {
          setBatchJobs(prev => prev.map(job =>
            job.id === selectedJob.id
              ? { ...job, status: 'error' as const }
              : job
          ));
        }
      }
    }
  );

  // Poll for job status when a job is running
  const { data: jobStatus, loading: pollingLoading } = usePolling(
    async () => {
      if (!selectedJob || !['queued', 'running'].includes(selectedJob.status)) {
        return null;
      }
      return await apiClient.getJobStatus(selectedJob.id);
    },
    [selectedJob?.id, selectedJob?.status],
    {
      interval: 3000,
      immediate: false,
      onSuccess: (status) => {
        if (status && selectedJob) {
          setBatchJobs(prev => prev.map(job =>
            job.id === selectedJob.id
              ? { ...job, status: status.state, progress: status.progress, outputs: status.outputs }
              : job
          ));
        }
      }
    }
  );

  const parseCSV = (csv: string): RenderItemIn[] => {
    const lines = csv.trim().split('\n');
    if (lines.length < 2) return [];

    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    const items: RenderItemIn[] = [];

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim());
      const item: any = {};

      headers.forEach((header, index) => {
        const value = values[index] || '';

        switch (header) {
          case 'id':
            item.id = value || `item_${Date.now()}_${i}`;
            break;
          case 'prompt':
            item.prompt = value;
            break;
          case 'negative':
            item.negative = value;
            break;
          case 'seed':
            item.seed = parseInt(value) || Math.floor(Math.random() * 1000000);
            break;
          case 'quality':
            item.quality = (value as Quality) || 'draft';
            break;
        }
      });

      if (item.prompt) {
        items.push(item as RenderItemIn);
      }
    }

    return items;
  };

  const handleCreateJob = () => {
    if (!newJobName.trim()) {
      alert('Por favor ingresa un nombre para el lote');
      return;
    }

    const items = parseCSV(csvContent);
    if (items.length === 0) {
      alert('Por favor ingresa datos CSV válidos con al menos una fila de prompts');
      return;
    }

    const newJob: BatchJob = {
      id: `batch_${Date.now()}`,
      name: newJobName.trim(),
      status: 'idle',
      progress: 0,
      items,
      createdAt: new Date().toISOString()
    };

    setBatchJobs([...batchJobs, newJob]);
    setNewJobName('');
    setCsvContent('');
    setIsCreating(false);
  };

  const handleProcessBatch = async (job: BatchJob) => {
    setSelectedJob(job);

    const payload: RenderBatchIn = {
      job_id: job.id,
      model,
      aspectRatio,
      enableTranslation: false,
      planos: job.items
    };

    try {
      await processBatch(payload);
    } catch (error) {
      console.error('Error processing batch:', error);
    }
  };

  const handleDeleteJob = (jobId: string) => {
    if (confirm('¿Estás seguro de eliminar este lote?')) {
      setBatchJobs(batchJobs.filter(job => job.id !== jobId));
      if (selectedJob?.id === jobId) {
        setSelectedJob(null);
      }
    }
  };

  const handleDownloadCSV = (job: BatchJob) => {
    const headers = ['ID', 'Prompt', 'Negative', 'Seed', 'Quality', 'Status', 'URL'];
    const rows = job.items.map(item => {
      const output = job.outputs?.find(o => o.id === item.id);
      return [
        item.id,
        item.prompt,
        item.negative,
        item.seed.toString(),
        item.quality,
        output?.status || 'pending',
        output?.url || ''
      ];
    });

    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${job.name}_results.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

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
        return <Package className="h-4 w-4 text-gray-500" />;
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

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-foreground">Procesamiento por Lotes</h1>
          <p className="text-muted-foreground">Genera múltiples imágenes en batch utilizando archivos CSV</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Job List */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Lotes ({batchJobs.length})
                </CardTitle>
                <CardDescription>
                  Administra tus trabajos por lotes
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  onClick={() => setIsCreating(true)}
                  className="w-full"
                  variant="outline"
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Crear Nuevo Lote
                </Button>

                <div className="space-y-2">
                  {batchJobs.map((job) => (
                    <div
                      key={job.id}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedJob?.id === job.id
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:bg-muted'
                      }`}
                      onClick={() => setSelectedJob(job)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(job.status)}
                          <div className="text-sm font-medium truncate">
                            {job.name}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteJob(job.id);
                          }}
                          className="text-destructive hover:text-destructive"
                        >
                          <XCircle className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {job.items.length} items • {new Date(job.createdAt).toLocaleDateString()}
                      </div>
                      {job.status !== 'idle' && (
                        <div className="mt-2">
                          <Progress value={job.progress} className="h-1" />
                        </div>
                      )}
                    </div>
                  ))}

                  {batchJobs.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground text-sm">
                      No hay lotes creados aún
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Job Details */}
          <div className="lg:col-span-2">
            {isCreating ? (
              <Card>
                <CardHeader>
                  <CardTitle>Crear Nuevo Lote</CardTitle>
                  <CardDescription>
                    Importa tus prompts desde un archivo CSV
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Nombre del Lote
                    </label>
                    <Input
                      value={newJobName}
                      onChange={(e) => setNewJobName(e.target.value)}
                      placeholder="Ej: Lote de personajes animados"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Datos CSV
                    </label>
                    <textarea
                      value={csvContent}
                      onChange={(e) => setCsvContent(e.target.value)}
                      placeholder="id,prompt,negative,seed,quality&#10;1,persona feliz,,42,draft&#10;2,paisaje montañoso,,123,draft"
                      className="w-full h-64 p-3 border border-input rounded-md bg-background text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 font-mono text-sm"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Modelo
                      </label>
                      <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full p-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                      >
                        <option value="kolors">Kolors</option>
                        <option value="sd">Stable Diffusion</option>
                        <option value="dalle">DALL-E</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Relación de Aspecto
                      </label>
                      <select
                        value={aspectRatio}
                        onChange={(e) => setAspectRatio(e.target.value)}
                        className="w-full p-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                      >
                        <option value="16:9">16:9</option>
                        <option value="4:3">4:3</option>
                        <option value="1:1">1:1</option>
                        <option value="9:16">9:16</option>
                      </select>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={handleCreateJob}
                      disabled={!newJobName.trim() || !csvContent.trim()}
                    >
                      Crear Lote
                    </Button>
                    <Button variant="outline" onClick={() => setIsCreating(false)}>
                      Cancelar
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : selectedJob ? (
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {getStatusIcon(selectedJob.status)}
                      {selectedJob.name}
                    </CardTitle>
                    <CardDescription>
                      {selectedJob.items.length} items • Creado: {new Date(selectedJob.createdAt).toLocaleString()}
                      {selectedJob.completedAt && (
                        <span> • Completado: {new Date(selectedJob.completedAt).toLocaleString()}</span>
                      )}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedJob.status)}`}>
                        {selectedJob.status.toUpperCase()}
                      </div>
                      <div className="space-x-2">
                        {selectedJob.status === 'idle' && (
                          <Button
                            onClick={() => handleProcessBatch(selectedJob)}
                            loading={processingBatch && selectedJob.id === selectedJob.id}
                          >
                            {processingBatch ? 'Procesando...' : 'Iniciar Procesamiento'}
                          </Button>
                        )}
                        {['queued', 'running'].includes(selectedJob.status) && (
                          <Button variant="outline" disabled>
                            <Clock className="h-4 w-4 mr-2 animate-spin" />
                            Procesando...
                          </Button>
                        )}
                        {selectedJob.status === 'done' && (
                          <Button
                            variant="outline"
                            onClick={() => handleDownloadCSV(selectedJob)}
                          >
                            <Download className="h-4 w-4 mr-2" />
                            Descargar Resultados
                          </Button>
                        )}
                      </div>
                    </div>

                    {selectedJob.status !== 'idle' && (
                      <div>
                        <div className="flex justify-between text-sm mb-2">
                          <span>Progreso</span>
                          <span>{selectedJob.progress}%</span>
                        </div>
                        <Progress value={selectedJob.progress} />
                      </div>
                    )}

                    {batchError && (
                      <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md">
                        <div className="text-sm text-destructive">
                          Error: {batchError.message}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Items del Lote</CardTitle>
                    <CardDescription>
                      {selectedJob.items.length} imágenes para generar
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {selectedJob.items.map((item, index) => {
                        const output = selectedJob.outputs?.find(o => o.id === item.id);
                        return (
                          <div
                            key={item.id}
                            className="flex items-center justify-between p-3 border border-border rounded-lg"
                          >
                            <div className="flex-1">
                              <div className="font-medium text-sm">
                                Item {index + 1}
                              </div>
                              <div className="text-xs text-muted-foreground truncate">
                                {item.prompt}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {getStatusIcon(output?.status || 'pending')}
                              <div className="text-xs text-muted-foreground">
                                {output?.status || 'pending'}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-12">
                    <Package className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-foreground mb-2">
                      Selecciona un lote
                    </h3>
                    <p className="text-muted-foreground">
                      Elige un lote existente o crea uno nuevo para comenzar
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

export default Lote;