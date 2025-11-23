import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Image,
  Download,
  Plus,
  Trash2,
  Loader2,
  Palette,
  Eye,
  Grid,
  Copy,
  CheckCircle,
  Clock,
  AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import { apiService } from '@/services/api';
import { useJobsStore } from '@/store/jobsStore';
import { Quality, RenderItem } from '@/types/job';

const MODELS = [
  { id: 'flux-dev', name: 'FLUX Dev (Calidad Alta)', description: 'Mejor calidad, más lento' },
  { id: 'flux-schnell', name: 'FLUX Schnell (Rápido)', description: 'Generación rápida' },
  { id: 'sdxl-turbo', name: 'SDXL Turbo (Ultra Rápido)', description: 'Velocidad máxima' },
];

const ASPECT_RATIOS = [
  { id: '9:16', name: 'Vertical (9:16)', label: 'TikTok/Reels' },
  { id: '16:9', name: 'Horizontal (16:9)', label: 'YouTube' },
  { id: '1:1', name: 'Cuadrado (1:1)', label: 'Instagram' },
];

const QUALITY_OPTIONS: { value: Quality; label: string; description: string }[] = [
  { value: 'draft', label: 'Borrador', description: 'Rápido, buena calidad' },
  { value: 'upscale', label: 'Alta Calidad', description: 'Mejor resolución, más tiempo' },
];

const PROMPT_TEMPLATES = [
  {
    category: 'What If - Humano',
    prompts: [
      'Human flying over futuristic city with wings made of light',
      'Crowd of people floating in the air, surprised expressions, aerial view',
      'Traffic jam in the sky with flying cars and humans, sunset',
    ]
  },
  {
    category: 'What If - Animales',
    prompts: [
      'Animals having business meeting in office, wearing suits, professional',
      'Dogs and cats walking on two legs, shopping in supermarket',
      'Forest animals using smartphones and laptops, modern tech',
    ]
  },
  {
    category: 'What If - Ciencia Ficción',
    prompts: [
      'Android robots serving coffee in futuristic café, neon lights',
      'Space station with Earth visible through window, astronauts working',
      'Time machine interior with glowing portals, vintage and futuristic elements',
    ]
  },
];

interface SceneItem {
  id: string;
  prompt: string;
  negative: string;
  quality: Quality;
}

export function Storyboard() {
  const [scenes, setScenes] = useState<SceneItem[]>([
    { id: '1', prompt: '', negative: '', quality: 'draft' }
  ]);
  const [model, setModel] = useState('flux-dev');
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentJob, setCurrentJob] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<RenderItem[]>([]);
  const [activeTab, setActiveTab] = useState('scenes');

  const { addJob, updateJob } = useJobsStore();

  const addScene = () => {
    const newScene: SceneItem = {
      id: Date.now().toString(),
      prompt: '',
      negative: '',
      quality: 'draft'
    };
    setScenes([...scenes, newScene]);
  };

  const removeScene = (id: string) => {
    if (scenes.length > 1) {
      setScenes(scenes.filter(scene => scene.id !== id));
    }
  };

  const updateScene = (id: string, updates: Partial<SceneItem>) => {
    setScenes(scenes.map(scene =>
      scene.id === id ? { ...scene, ...updates } : scene
    ));
  };

  const useTemplate = (prompt: string) => {
    const currentScene = scenes[scenes.length - 1];
    if (currentScene) {
      updateScene(currentScene.id, { prompt });
    }
  };

  const generateImages = async () => {
    const validScenes = scenes.filter(scene => scene.prompt.trim());

    if (validScenes.length === 0) {
      toast.error('Por favor agrega al menos una escena con texto');
      return;
    }

    const jobId = `storyboard-${Date.now()}`;
    setCurrentJob(jobId);
    setIsGenerating(true);
    setProgress(0);

    try {
      // Prepare payload
      const payload = {
        job_id: jobId,
        model,
        aspectRatio,
        planos: validScenes.map((scene, index) => ({
          id: `${index + 1}`,
          prompt: scene.prompt.trim(),
          negative: scene.negative || 'ugly, blurry, bad quality',
          seed: Math.floor(Math.random() * 1000000),
          quality: scene.quality,
        })),
      };

      // Add job to store
      const newJob = {
        job_id: jobId,
        state: 'queued' as const,
        progress: 0,
        outputs: [],
        type: 'render_batch' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      addJob(newJob);
      toast.info(`Iniciando generación de ${validScenes.length} imágenes...`);

      // Call render batch API
      const result = await apiService.createRenderBatch(payload);

      // Monitor progress
      let completedImages = 0;
      const totalImages = validScenes.length;

      const progressInterval = setInterval(async () => {
        try {
          const status = await apiService.getJobStatus(jobId);
          const completed = status.outputs.filter(item => item.status === 'done').length;
          const newProgress = Math.round((completed / totalImages) * 100);

          setProgress(newProgress);
          completedImages = completed;

          if (status.state === 'done') {
            clearInterval(progressInterval);
            setResults(status.outputs);
            updateJob(jobId, {
              state: 'done',
              progress: 100,
              outputs: status.outputs,
            });
            toast.success(`Generación completada: ${completedImages} imágenes`);
            setIsGenerating(false);
            setCurrentJob(null);
          } else if (status.state === 'error') {
            clearInterval(progressInterval);
            toast.error('Error en la generación de imágenes');
            setIsGenerating(false);
            setCurrentJob(null);
          }
        } catch (error) {
          clearInterval(progressInterval);
          console.error('Error checking progress:', error);
        }
      }, 2000);

    } catch (error) {
      console.error('Error generating images:', error);

      if (currentJob) {
        updateJob(currentJob, {
          state: 'error',
          error_message: error instanceof Error ? error.message : 'Error desconocido',
        });
      }

      toast.error('Error al generar imágenes: ' + (error instanceof Error ? error.message : 'Error desconocido'));
      setIsGenerating(false);
      setCurrentJob(null);
    }
  };

  const downloadImage = (imageUrl: string, index: number) => {
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `storyboard-${Date.now()}-${index + 1}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Descarga iniciada');
  };

  const downloadAllImages = () => {
    const completedImages = results.filter(item => item.url);
    completedImages.forEach((item, index) => {
      if (item.url) {
        setTimeout(() => {
          downloadImage(item.url, index);
        }, index * 200); // Stagger downloads
      }
    });
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold flex items-center justify-center gap-2">
          <Image className="w-8 h-8 text-purple-500" />
          Storyboard AI
        </h1>
        <p className="text-gray-600">
          Genera imágenes increíbles para tu video con inteligencia artificial
        </p>
      </div>

      {/* Configuration Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid md:grid-cols-3 gap-4">
            {/* Model Selection */}
            <div className="space-y-2">
              <Label>Modelo IA</Label>
              <Select value={model} onValueChange={setModel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MODELS.map((m) => (
                    <SelectItem key={m.id} value={m.id}>
                      <div>
                        <div className="font-medium">{m.name}</div>
                        <div className="text-xs text-gray-500">{m.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Aspect Ratio */}
            <div className="space-y-2">
              <Label>Formato</Label>
              <Select value={aspectRatio} onValueChange={setAspectRatio}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ASPECT_RATIOS.map((ratio) => (
                    <SelectItem key={ratio.id} value={ratio.id}>
                      <div>
                        <div className="font-medium">{ratio.name}</div>
                        <div className="text-xs text-gray-500">{ratio.label}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Quick Actions */}
            <div className="space-y-2">
              <Label>Acciones</Label>
              <div className="flex gap-2">
                <Button
                  onClick={generateImages}
                  disabled={isGenerating || scenes.filter(s => s.prompt.trim()).length === 0}
                  className="flex-1"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generando...
                    </>
                  ) : (
                    <>
                      <Palette className="w-4 h-4 mr-2" />
                      Generar Todas
                    </>
                  )}
                </Button>
                <Button onClick={addScene} variant="outline" size="icon">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="scenes">Escenas ({scenes.length})</TabsTrigger>
          <TabsTrigger value="templates">Plantillas</TabsTrigger>
          <TabsTrigger value="results">Resultados ({results.filter(r => r.url).length})</TabsTrigger>
        </TabsList>

        {/* Scenes Tab */}
        <TabsContent value="scenes" className="space-y-4">
          {scenes.map((scene, index) => (
            <Card key={scene.id}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Escena {index + 1}</CardTitle>
                  <div className="flex items-center gap-2">
                    <Select
                      value={scene.quality}
                      onValueChange={(value: Quality) => updateScene(scene.id, { quality: value })}
                    >
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {QUALITY_OPTIONS.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            <div>
                              <div className="font-medium">{option.label}</div>
                              <div className="text-xs text-gray-500">{option.description}</div>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {scenes.length > 1 && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => removeScene(scene.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Prompt */}
                <div className="space-y-2">
                  <Label>Descripción de la imagen</Label>
                  <Textarea
                    placeholder="Describe la imagen que quieres generar..."
                    value={scene.prompt}
                    onChange={(e) => updateScene(scene.id, { prompt: e.target.value })}
                    className="min-h-[80px]"
                    disabled={isGenerating}
                  />
                </div>

                {/* Negative Prompt */}
                <div className="space-y-2">
                  <Label>Elementos a evitar (opcional)</Label>
                  <Input
                    placeholder="ugly, blurry, bad quality, text, watermark..."
                    value={scene.negative}
                    onChange={(e) => updateScene(scene.id, { negative: e.target.value })}
                    disabled={isGenerating}
                  />
                </div>

                {/* Character count */}
                <div className="text-sm text-gray-500">
                  Caracteres: {scene.prompt.length}
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Add Scene Button */}
          <Button onClick={addScene} variant="outline" className="w-full">
            <Plus className="w-4 h-4 mr-2" />
            Agregar Otra Escena
          </Button>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-4">
          {PROMPT_TEMPLATES.map((category) => (
            <Card key={category.category}>
              <CardHeader>
                <CardTitle className="text-lg">{category.category}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-1 gap-2">
                  {category.prompts.map((prompt, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      className="w-full text-left justify-start h-auto p-3"
                      onClick={() => useTemplate(prompt)}
                    >
                      <div className="text-sm">{prompt}</div>
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-4">
          {isGenerating && (
            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Generando imágenes...</span>
                    <span>{progress}%</span>
                  </div>
                  <Progress value={progress} className="h-2" />
                </div>
              </CardContent>
            </Card>
          )}

          {results.length > 0 && (
            <>
              {/* Results Header */}
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Grid className="w-5 h-5" />
                  Imágenes Generadas ({results.filter(r => r.url).length}/{results.length})
                </h3>
                {results.filter(r => r.url).length > 0 && (
                  <Button onClick={downloadAllImages} variant="outline">
                    <Download className="w-4 h-4 mr-2" />
                    Descargar Todas
                  </Button>
                )}
              </div>

              {/* Images Grid */}
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {results.map((item, index) => (
                  <Card key={item.id}>
                    <CardContent className="pt-4">
                      <div className="space-y-3">
                        {/* Image Preview */}
                        {item.url ? (
                          <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
                            <img
                              src={item.url}
                              alt={`Scene ${index + 1}`}
                              className="w-full h-full object-cover"
                            />
                          </div>
                        ) : (
                          <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
                            {item.status === 'running' ? (
                              <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
                            ) : item.status === 'error' ? (
                              <AlertCircle className="w-8 h-8 text-red-400" />
                            ) : (
                              <Clock className="w-8 h-8 text-gray-400" />
                            )}
                          </div>
                        )}

                        {/* Status and Info */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium">Escena {index + 1}</span>
                            {item.status === 'done' && (
                              <CheckCircle className="w-4 h-4 text-green-500" />
                            )}
                            {item.status === 'running' && (
                              <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                            )}
                            {item.status === 'error' && (
                              <AlertCircle className="w-4 h-4 text-red-500" />
                            )}
                          </div>
                          {item.url && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => downloadImage(item.url!, index)}
                            >
                              <Download className="w-3 h-3" />
                            </Button>
                          )}
                        </div>

                        {/* Quality Badge */}
                        <Badge variant="secondary" className="text-xs">
                          {item.quality === 'upscale' ? 'Alta Calidad' : 'Borrador'}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}