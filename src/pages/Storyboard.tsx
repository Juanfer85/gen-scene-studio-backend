import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { Image, Plus, Trash2, Download, Eye, Clock, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import { useApiCall } from '@/hooks/useApiCall';
import apiClient from '@/lib/api';
import { RenderBatchIn, RenderItemIn, JobStatusOut, Quality } from '@/types';

interface StoryboardItem {
  id: string;
  prompt: string;
  negative: string;
  seed: number;
  quality: Quality;
  url?: string;
  status: 'queued' | 'running' | 'done' | 'error';
  hash?: string;
}

const Storyboard: React.FC = () => {
  const [items, setItems] = useState<StoryboardItem[]>([]);
  const [model, setModel] = useState('kolors');
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [enableTranslation, setEnableTranslation] = useState(false);
  const [jobId] = useState(() => `render_${Date.now()}`);
  const [jobStatus, setJobStatus] = useState<JobStatusOut | null>(null);

  const {
    execute: renderBatch,
    loading,
    error
  } = useApiCall(
    (payload: RenderBatchIn) => apiClient.renderBatch(payload),
    {
      onSuccess: (result) => {
        console.log('Batch render started:', result);
        // Start polling for job status
        pollJobStatus();
      },
      onError: (error) => {
        console.error('Error starting batch render:', error);
      }
    }
  );

  const pollJobStatus = async () => {
    try {
      const status = await apiClient.pollJobStatus(
        jobId,
        (status) => {
          setJobStatus(status);
          // Update items with status and URLs
          setItems(prevItems =>
            prevItems.map(item => {
              const output = status.outputs.find(o => o.id === item.id);
              if (output) {
                return {
                  ...item,
                  status: output.status,
                  url: output.url,
                  hash: output.hash
                };
              }
              return item;
            })
          );
        },
        3000,
        600000 // 10 minutes timeout
      );
      setJobStatus(status);
    } catch (error) {
      console.error('Error polling job status:', error);
    }
  };

  const addItem = () => {
    const newItem: StoryboardItem = {
      id: `item_${Date.now()}`,
      prompt: '',
      negative: '',
      seed: Math.floor(Math.random() * 1000000),
      quality: 'draft',
      status: 'queued'
    };
    setItems([...items, newItem]);
  };

  const removeItem = (id: string) => {
    setItems(items.filter(item => item.id !== id));
  };

  const updateItem = (id: string, updates: Partial<StoryboardItem>) => {
    setItems(items.map(item =>
      item.id === id ? { ...item, ...updates } : item
    ));
  };

  const handleGenerate = async () => {
    if (items.length === 0) {
      alert('Por favor agrega al menos un elemento al storyboard');
      return;
    }

    const validItems = items.filter(item => item.prompt.trim());
    if (validItems.length === 0) {
      alert('Por favor agrega prompts para los elementos del storyboard');
      return;
    }

    const renderItems: RenderItemIn[] = items.map(item => ({
      id: item.id,
      prompt: item.prompt.trim(),
      negative: item.negative.trim(),
      seed: item.seed,
      quality: item.quality
    }));

    const payload: RenderBatchIn = {
      job_id: jobId,
      model,
      aspectRatio,
      enableTranslation,
      planos: renderItems
    };

    try {
      // Reset job status
      setJobStatus(null);
      // Reset all items to queued status
      setItems(items.map(item => ({ ...item, status: 'queued' as const, url: undefined })));

      await renderBatch(payload);
    } catch (error) {
      console.error('Error generating storyboard:', error);
    }
  };

  const handleDownload = (url: string, index: number) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = `storyboard_${jobId}_${index + 1}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const regenerateRandomSeed = (id: string) => {
    updateItem(id, { seed: Math.floor(Math.random() * 1000000) });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getQualityLabel = (quality: Quality): string => {
    switch (quality) {
      case 'draft':
        return 'Borrador (rápido)';
      case 'upscale':
        return 'Alta calidad';
      default:
        return quality;
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-foreground">Storyboard con IA</h1>
          <p className="text-muted-foreground">Genera imágenes para tu storyboard usando inteligencia artificial</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Configuración del Lote</CardTitle>
            <CardDescription>
              Configura el modelo y opciones de generación
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="model" className="block text-sm font-medium mb-2">
                  Modelo
                </label>
                <select
                  id="model"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                >
                  <option value="kolors">Kolors</option>
                  <option value="sd">Stable Diffusion</option>
                  <option value="dalle">DALL-E</option>
                  <option value="midjourney">Midjourney</option>
                </select>
              </div>

              <div>
                <label htmlFor="aspectRatio" className="block text-sm font-medium mb-2">
                  Relación de Aspecto
                </label>
                <select
                  id="aspectRatio"
                  value={aspectRatio}
                  onChange={(e) => setAspectRatio(e.target.value)}
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                >
                  <option value="16:9">16:9 (Widescreen)</option>
                  <option value="4:3">4:3 (Estándar)</option>
                  <option value="1:1">1:1 (Cuadrado)</option>
                  <option value="9:16">9:16 (Vertical)</option>
                  <option value="3:2">3:2 (Cámara)</option>
                </select>
              </div>

              <div className="flex items-center space-x-2 pt-6">
                <input
                  id="enableTranslation"
                  type="checkbox"
                  checked={enableTranslation}
                  onChange={(e) => setEnableTranslation(e.target.checked)}
                  className="h-4 w-4 border border-input rounded bg-background text-primary focus:ring-2 focus:ring-ring focus:ring-offset-2"
                />
                <label htmlFor="enableTranslation" className="text-sm font-medium">
                  Habilitar traducción automática
                </label>
              </div>
            </div>

            <div className="flex justify-between items-center">
              <div className="text-sm text-muted-foreground">
                {items.length} elementos • Job ID: {jobId}
              </div>
              <div className="space-x-2">
                <Button onClick={addItem} variant="outline">
                  <Plus className="h-4 w-4 mr-2" />
                  Agregar Elemento
                </Button>
                <Button
                  onClick={handleGenerate}
                  disabled={loading || items.length === 0}
                  loading={loading}
                >
                  {loading ? 'Generando...' : 'Generar Storyboard'}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Image className="h-5 w-5" />
              Elementos del Storyboard
            </CardTitle>
            <CardDescription>
              Define los prompts y configuración para cada escena
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {items.map((item, index) => (
                <div key={item.id} className="p-4 border border-border rounded-lg space-y-3">
                  <div className="flex justify-between items-center">
                    <h4 className="font-medium">Escena {index + 1}</h4>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(item.status)}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => removeItem(item.id)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Prompt *</label>
                      <textarea
                        value={item.prompt}
                        onChange={(e) => updateItem(item.id, { prompt: e.target.value })}
                        placeholder="Describe la escena..."
                        className="w-full min-h-[80px] p-2 border border-input rounded-md bg-background text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-1">Prompt Negativo</label>
                      <textarea
                        value={item.negative}
                        onChange={(e) => updateItem(item.id, { negative: e.target.value })}
                        placeholder="Describe lo que NO quieres en la imagen..."
                        className="w-full min-h-[60px] p-2 border border-input rounded-md bg-background text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-medium mb-1">Semilla</label>
                        <div className="flex gap-2">
                          <Input
                            type="number"
                            value={item.seed}
                            onChange={(e) => updateItem(item.id, { seed: parseInt(e.target.value) || 0 })}
                            min="0"
                            max="999999"
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => regenerateRandomSeed(item.id)}
                            title="Generar semilla aleatoria"
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1">Calidad</label>
                        <select
                          value={item.quality}
                          onChange={(e) => updateItem(item.id, { quality: e.target.value as Quality })}
                          className="w-full p-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                        >
                          <option value="draft">Borrador</option>
                          <option value="upscale">Alta Calidad</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {item.url && (
                    <div className="space-y-2">
                      <div className="aspect-video bg-muted rounded-lg overflow-hidden">
                        <img
                          src={item.url}
                          alt={`Escena ${index + 1}`}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(item.url!, '_blank')}
                          className="flex items-center gap-1"
                        >
                          <Eye className="h-3 w-3" />
                          Ver
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownload(item.url!, index)}
                          className="flex items-center gap-1"
                        >
                          <Download className="h-3 w-3" />
                          Descargar
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {items.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No hay elementos en el storyboard. Haz clic en "Agregar Elemento" para comenzar.
              </div>
            )}
          </CardContent>
        </Card>

        {jobStatus && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {getStatusIcon(jobStatus.state)}
                Estado del Trabajo
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Progreso</span>
                  <span>{jobStatus.progress}%</span>
                </div>
                <Progress value={jobStatus.progress} />
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Estado:</span>
                  <div className="font-medium capitalize">{jobStatus.state}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Completados:</span>
                  <div className="font-medium">
                    {jobStatus.outputs.filter(o => o.status === 'done').length} / {jobStatus.outputs.length}
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Errores:</span>
                  <div className="font-medium text-destructive">
                    {jobStatus.outputs.filter(o => o.status === 'error').length}
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Job ID:</span>
                  <div className="font-medium">{jobStatus.job_id}</div>
                </div>
              </div>

              {jobStatus.state === 'error' && (
                <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md">
                  <div className="text-sm text-destructive">
                    El proceso de generación falló. Por favor verifica los prompts e intenta nuevamente.
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {error && (
          <Card>
            <CardContent className="pt-6">
              <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md">
                <div className="text-sm text-destructive">
                  Error: {error.message}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Storyboard;