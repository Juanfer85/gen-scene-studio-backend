import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { Plus, Play, Settings, Download, Eye, CheckCircle, XCircle, Clock, AlertTriangle, Save } from 'lucide-react';
import { useApiCall } from '@/hooks/useApiCall';
import apiClient from '@/lib/api';
import { RenderBatchIn, ComposeIn, TTSIn, JobStatusOut, Quality } from '@/types';

interface JobStep {
  id: string;
  type: 'tts' | 'render' | 'compose';
  name: string;
  status: 'pending' | 'running' | 'done' | 'error';
  progress: number;
  data?: any;
  result?: any;
  error?: string;
}

interface JobTemplate {
  id: string;
  name: string;
  description: string;
  steps: JobStep[];
}

const NewJob: React.FC = () => {
  const [jobName, setJobName] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [customSteps, setCustomSteps] = useState<JobStep[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentJobId, setCurrentJobId] = useState('');
  const [savedTemplates, setSavedTemplates] = useState<JobTemplate[]>([]);

  // Load saved templates from localStorage
  useEffect(() => {
    const templates = localStorage.getItem('jobTemplates');
    if (templates) {
      setSavedTemplates(JSON.parse(templates));
    }
  }, []);

  // Predefined templates
  const predefinedTemplates: JobTemplate[] = [
    {
      id: 'simple-story',
      name: 'Historia Simple',
      description: 'Genera voz, 3 escenas y compone video',
      steps: [
        {
          id: 'tts-1',
          type: 'tts',
          name: 'Generar Voz',
          status: 'pending',
          progress: 0,
          data: {
            text: 'Había una vez un mundo lleno de colores mágicos donde los sueños cobraban vida.',
            voice: 'es-ES-Standard-A',
            wpm: 140
          }
        },
        {
          id: 'render-1',
          type: 'render',
          name: 'Generar Escena 1',
          status: 'pending',
          progress: 0,
          data: {
            model: 'kolors',
            aspectRatio: '16:9',
            planos: [
              {
                id: 'scene1',
                prompt: 'Un mundo mágico con colores vibrantes, estilo de fantasía, alta calidad',
                negative: 'oscuro, terrorífico',
                seed: 12345,
                quality: 'draft'
              }
            ]
          }
        },
        {
          id: 'render-2',
          type: 'render',
          name: 'Generar Escena 2',
          status: 'pending',
          progress: 0,
          data: {
            model: 'kolors',
            aspectRatio: '16:9',
            planos: [
              {
                id: 'scene2',
                prompt: 'Personajes soñando con colores flotantes, estilo surrealista',
                negative: 'realista, fotográfico',
                seed: 54321,
                quality: 'draft'
              }
            ]
          }
        },
        {
          id: 'render-3',
          type: 'render',
          name: 'Generar Escena 3',
          status: 'pending',
          progress: 0,
          data: {
            model: 'kolors',
            aspectRatio: '16:9',
            planos: [
              {
                id: 'scene3',
                prompt: 'Los sueños se hacen realidad, celebración mágica con fuegos artificiales',
                negative: 'triste, melancólico',
                seed: 98765,
                quality: 'draft'
              }
            ]
          }
        },
        {
          id: 'compose-1',
          type: 'compose',
          name: 'Componer Video',
          status: 'pending',
          progress: 0,
          data: {
            images: [], // Will be filled dynamically
            audio: '', // Will be filled dynamically
            srt: '',
            out: 'story_final.mp4'
          }
        }
      ]
    },
    {
      id: 'product-demo',
      name: 'Demo de Producto',
      description: 'Genera video promocional de producto con voz',
      steps: [
        {
          id: 'tts-1',
          type: 'tts',
          name: 'Generar Voz de Venta',
          status: 'pending',
          progress: 0,
          data: {
            text: 'Descubre el producto que revolucionará tu vida. Calidad, diseño y funcionalidad en uno.',
            voice: 'es-ES-Standard-B',
            wpm: 160
          }
        },
        {
          id: 'render-1',
          type: 'render',
          name: 'Generar Producto',
          status: 'pending',
          progress: 0,
          data: {
            model: 'kolors',
            aspectRatio: '1:1',
            planos: [
              {
                id: 'product',
                prompt: 'Producto premium moderno, fondo limpio, iluminación profesional, foto de producto',
                negative: 'distracciones, fondo desordenado',
                seed: 11111,
                quality: 'upscale'
              }
            ]
          }
        },
        {
          id: 'compose-1',
          type: 'compose',
          name: 'Componer Video',
          status: 'pending',
          progress: 0,
          data: {
            images: [],
            audio: '',
            srt: '',
            out: 'product_demo.mp4'
          }
        }
      ]
    }
  ];

  const allTemplates = [...savedTemplates, ...predefinedTemplates];

  const {
    execute: executeTTS,
    loading: ttsLoading
  } = useApiCall(
    (payload: TTSIn) => apiClient.generateSpeech(payload),
    {
      retries: 2,
      retryDelay: 2000
    }
  );

  const {
    execute: executeRender,
    loading: renderLoading
  } = useApiCall(
    (payload: RenderBatchIn) => apiClient.renderBatch(payload),
    {
      retries: 2,
      retryDelay: 3000
    }
  );

  const {
    execute: executeCompose,
    loading: composeLoading
  } = useApiCall(
    (payload: ComposeIn) => apiClient.composeVideo(payload),
    {
      retries: 2,
      retryDelay: 3000
    }
  );

  const getActiveSteps = (): JobStep[] => {
    if (selectedTemplate) {
      const template = allTemplates.find(t => t.id === selectedTemplate);
      return template?.steps || [];
    }
    return customSteps;
  };

  const updateStepStatus = (stepId: string, updates: Partial<JobStep>) => {
    const updateSteps = (steps: JobStep[]) => {
      return steps.map(step =>
        step.id === stepId ? { ...step, ...updates } : step
      );
    };

    if (selectedTemplate) {
      // This would need more complex state management for templates
      // For now, we'll handle custom steps only
    } else {
      setCustomSteps(updateSteps(customSteps));
    }
  };

  const executeStep = async (step: JobStep): Promise<any> => {
    updateStepStatus(step.id, { status: 'running', progress: 10 });

    try {
      let result;

      switch (step.type) {
        case 'tts':
          updateStepStatus(step.id, { progress: 30 });
          result = await executeTTS({
            job_id: `${currentJobId}_${step.id}`,
            text: step.data.text,
            voice: step.data.voice,
            wpm: step.data.wpm
          });
          updateStepStatus(step.id, { progress: 90 });
          break;

        case 'render':
          updateStepStatus(step.id, { progress: 30 });
          result = await executeRender({
            job_id: `${currentJobId}_${step.id}`,
            model: step.data.model,
            aspectRatio: step.data.aspectRatio,
            enableTranslation: false,
            planos: step.data.planos
          });
          updateStepStatus(step.id, { progress: 70 });

          // Poll for render completion
          const renderStatus = await apiClient.pollJobStatus(
            result.job_id,
            (status) => {
              const progress = Math.min(70 + status.progress * 0.3, 90);
              updateStepStatus(step.id, { progress });
            },
            3000,
            300000
          );
          result = { ...result, outputs: renderStatus.outputs };
          updateStepStatus(step.id, { progress: 90 });
          break;

        case 'compose':
          updateStepStatus(step.id, { progress: 30 });
          result = await executeCompose({
            job_id: `${currentJobId}_${step.id}`,
            images: step.data.images,
            audio: step.data.audio,
            srt: step.data.srt,
            out: step.data.out
          });
          updateStepStatus(step.id, { progress: 70 });

          // Poll for composition completion
          await apiClient.pollComposeResult(
            result.job_id,
            (composeResult) => {
              const progress = Math.min(70 + (composeResult.ready ? 30 : 0), 90);
              updateStepStatus(step.id, { progress });
            },
            3000,
            300000
          );
          updateStepStatus(step.id, { progress: 90 });
          break;

        default:
          throw new Error(`Unknown step type: ${step.type}`);
      }

      updateStepStatus(step.id, { status: 'done', progress: 100, result });
      return result;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      updateStepStatus(step.id, { status: 'error', progress: 0, error: errorMessage });
      throw error;
    }
  };

  const executeJob = async () => {
    if (!jobName.trim()) {
      alert('Por favor ingresa un nombre para el trabajo');
      return;
    }

    const steps = getActiveSteps();
    if (steps.length === 0) {
      alert('Por favor selecciona una plantilla o configura pasos personalizados');
      return;
    }

    setIsRunning(true);
    const jobId = `job_${Date.now()}`;
    setCurrentJobId(jobId);

    // Reset all steps to pending
    steps.forEach(step => {
      updateStepStatus(step.id, { status: 'pending', progress: 0, result: undefined, error: undefined });
    });

    try {
      // Prepare cross-step data sharing
      const sharedData: any = {};

      for (let i = 0; i < steps.length; i++) {
        const step = steps[i];

        // Inject shared data into step
        if (step.type === 'compose' && sharedData.audioUrl && sharedData.images) {
          step.data = {
            ...step.data,
            audio: sharedData.audioUrl,
            images: sharedData.images.map((url: string, index: number) => ({
              url,
              duration: 3,
              kenburns: 'in',
              text: '',
              pos: 'bottom'
            }))
          };
        }

        try {
          const result = await executeStep(step);

          // Store results for next steps
          if (step.type === 'tts') {
            sharedData.audioUrl = result.audio_url;
            sharedData.audioDuration = result.duration_s;
          } else if (step.type === 'render') {
            sharedData.images = result.outputs?.filter((o: any) => o.url).map((o: any) => o.url) || [];
          }

        } catch (error) {
          console.error(`Error in step ${step.name}:`, error);
          // Continue with next steps even if one fails
          continue;
        }

        // Small delay between steps
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

    } finally {
      setIsRunning(false);
    }
  };

  const saveTemplate = () => {
    if (!jobName.trim() || customSteps.length === 0) {
      alert('Por favor ingresa un nombre y configura al menos un paso');
      return;
    }

    const newTemplate: JobTemplate = {
      id: `custom_${Date.now()}`,
      name: jobName.trim(),
      description: `Plantilla personalizada con ${customSteps.length} pasos`,
      steps: customSteps
    };

    const updatedTemplates = [...savedTemplates, newTemplate];
    setSavedTemplates(updatedTemplates);
    localStorage.setItem('jobTemplates', JSON.stringify(updatedTemplates));
    alert('Plantilla guardada exitosamente');
  };

  const addCustomStep = (type: 'tts' | 'render' | 'compose') => {
    const newStep: JobStep = {
      id: `custom_${Date.now()}`,
      type,
      name: `Nuevo ${type.toUpperCase()}`,
      status: 'pending',
      progress: 0,
      data: type === 'tts' ? {
        text: '',
        voice: '',
        wpm: 160
      } : type === 'render' ? {
        model: 'kolors',
        aspectRatio: '16:9',
        planos: [{
          id: 'default',
          prompt: '',
          negative: '',
          seed: Math.floor(Math.random() * 1000000),
          quality: 'draft'
        }]
      } : {
        images: [],
        audio: '',
        srt: '',
        out: 'output.mp4'
      }
    };

    setCustomSteps([...customSteps, newStep]);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'running':
        return <Clock className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const isLoading = ttsLoading || renderLoading || composeLoading;

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-foreground">Nuevo Trabajo</h1>
          <p className="text-muted-foreground">Crea y ejecuta trabajos automatizados de generación de contenido</p>
        </div>

        {/* Job Configuration */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Configuración del Trabajo
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Nombre del Trabajo
              </label>
              <Input
                value={jobName}
                onChange={(e) => setJobName(e.target.value)}
                placeholder="Mi trabajo automatizado"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Plantilla Predefinida
              </label>
              <select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                className="w-full p-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                disabled={isRunning}
              >
                <option value="">Seleccionar plantilla...</option>
                <optgroup label="Plantillas Predefinidas">
                  {predefinedTemplates.map(template => (
                    <option key={template.id} value={template.id}>
                      {template.name} - {template.description}
                    </option>
                  ))}
                </optgroup>
                {savedTemplates.length > 0 && (
                  <optgroup label="Mis Plantillas">
                    {savedTemplates.map(template => (
                      <option key={template.id} value={template.id}>
                        {template.name}
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
            </div>

            {!selectedTemplate && (
              <div className="space-y-3">
                <label className="block text-sm font-medium">
                  Pasos Personalizados
                </label>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => addCustomStep('tts')}
                    disabled={isRunning}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    TTS
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => addCustomStep('render')}
                    disabled={isRunning}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Render
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => addCustomStep('compose')}
                    disabled={isRunning}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Compose
                  </Button>
                  {customSteps.length > 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={saveTemplate}
                      disabled={isRunning}
                    >
                      <Save className="h-4 w-4 mr-2" />
                      Guardar Plantilla
                    </Button>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <Button
                onClick={executeJob}
                disabled={isLoading || isRunning || (!selectedTemplate && customSteps.length === 0)}
                loading={isRunning}
                className="flex-1"
              >
                {isRunning ? 'Ejecutando Trabajo...' : 'Iniciar Trabajo'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Steps Timeline */}
        {(selectedTemplate || customSteps.length > 0) && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Play className="h-5 w-5" />
                Flujo de Trabajo
              </CardTitle>
              <CardDescription>
                Secuencia de pasos que se ejecutarán en orden
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {getActiveSteps().map((step, index) => (
                <div key={step.id} className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-medium">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-medium flex items-center gap-2">
                          {getStatusIcon(step.status)}
                          {step.name}
                        </div>
                        <div className="text-sm text-muted-foreground capitalize">
                          {step.type}
                        </div>
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {step.progress}%
                    </div>
                  </div>

                  {step.status === 'running' && (
                    <Progress value={step.progress} />
                  )}

                  {step.error && (
                    <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                      <div className="flex items-center gap-2 text-sm text-destructive">
                        <AlertTriangle className="h-4 w-4" />
                        {step.error}
                      </div>
                    </div>
                  )}

                  {step.result && (
                    <div className="p-3 bg-muted rounded-md space-y-2">
                      <div className="text-sm font-medium">Resultado:</div>
                      <div className="text-xs text-muted-foreground space-y-1">
                        {step.type === 'tts' && (
                          <>
                            <div>Audio URL: {step.result.audio_url}</div>
                            <div>Duración: {step.result.duration_s}s</div>
                          </>
                        )}
                        {step.type === 'render' && (
                          <>
                            <div>Job ID: {step.result.job_id}</div>
                            <div>Aceptados: {step.result.accepted}</div>
                            <div>Duplicados: {step.result.deduped}</div>
                          </>
                        )}
                        {step.type === 'compose' && (
                          <>
                            <div>Job ID: {step.result.job_id}</div>
                            <div>Aceptado: {step.result.accepted}</div>
                          </>
                        )}
                      </div>
                    </div>
                  )}

                  {index < getActiveSteps().length - 1 && (
                    <div className="border-l-2 border-border ml-4 h-4"></div>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default NewJob;