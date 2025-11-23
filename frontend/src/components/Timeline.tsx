import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import {
  Play,
  Download,
  Plus,
  Trash2,
  Loader2,
  Film,
  Clock,
  Volume2,
  Type,
  Settings,
  Eye,
  CheckCircle,
  AlertCircle,
  Music,
  FileVideo,
  Wand2
} from 'lucide-react';
import { toast } from 'sonner';
import { apiService } from '@/services/api';
import { useJobsStore } from '@/store/jobsStore';

const KENBURNS_EFFECTS = [
  { id: 'none', name: 'Sin Efecto', description: 'Imagen estática' },
  { id: 'slow-zoom-in', name: 'Zoom In Lento', description: 'Aumento gradual' },
  { id: 'slow-zoom-out', name: 'Zoom Out Lento', description: 'Reducción gradual' },
  { id: 'pan-left', name: 'Pan Izquierda', description: 'Movimiento horizontal' },
  { id: 'pan-right', name: 'Pan Derecha', description: 'Movimiento horizontal' },
];

const TEXT_POSITIONS = [
  { id: 'top', name: 'Arriba' },
  { id: 'center', name: 'Centro' },
  { id: 'bottom', name: 'Abajo' },
];

const FONTS = [
  { id: 'default', name: 'Default', style: 'sans-serif' },
  { id: 'modern', name: 'Modern', style: 'Arial, sans-serif' },
  { id: 'classic', name: 'Classic', style: 'Georgia, serif' },
  { id: 'tech', name: 'Tech', style: 'Courier New, monospace' },
];

interface TimelineItem {
  id: string;
  imageUrl: string;
  duration: number;
  kenburns: string;
  text: string;
  textPosition: string;
  fontSize: number;
  fontColor: string;
  startTime: number;
}

interface VideoSettings {
  fadeInMs: number;
  fadeOutMs: number;
  loudnorm: boolean;
  outputName: string;
}

export function Timeline() {
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [audioUrl, setAudioUrl] = useState<string>('');
  const [srtContent, setSrtContent] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentJob, setCurrentJob] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('timeline');
  const [videoSettings, setVideoSettings] = useState<VideoSettings>({
    fadeInMs: 500,
    fadeOutMs: 500,
    loudnorm: true,
    outputName: '',
  });

  const { addJob, updateJob } = useJobsStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Load sample images on mount
    const sampleImages = [
      'https://picsum.photos/1080/1920?random=1',
      'https://picsum.photos/1080/1920?random=2',
      'https://picsum.photos/1080/1920?random=3',
    ];

    const initialTimeline: TimelineItem[] = sampleImages.map((url, index) => ({
      id: `${index + 1}`,
      imageUrl: url,
      duration: 5,
      kenburns: 'none',
      text: '',
      textPosition: 'bottom',
      fontSize: 48,
      fontColor: '#ffffff',
      startTime: index * 5,
    }));

    setTimeline(initialTimeline);
  }, []);

  const addTimelineItem = (imageUrl?: string) => {
    const newItem: TimelineItem = {
      id: Date.now().toString(),
      imageUrl: imageUrl || `https://picsum.photos/1080/1920?random=${Date.now()}`,
      duration: 5,
      kenburns: 'none',
      text: '',
      textPosition: 'bottom',
      fontSize: 48,
      fontColor: '#ffffff',
      startTime: timeline.length > 0 ?
        Math.max(...timeline.map(item => item.startTime + item.duration)) : 0,
    };

    setTimeline([...timeline, newItem]);
    toast.success('Clip agregado al timeline');
  };

  const removeTimelineItem = (id: string) => {
    setTimeline(timeline.filter(item => item.id !== id));
    toast.success('Clip eliminado del timeline');
  };

  const updateTimelineItem = (id: string, updates: Partial<TimelineItem>) => {
    setTimeline(timeline.map(item =>
      item.id === id ? { ...item, ...updates } : item
    ));
  };

  const getTotalDuration = () => {
    return Math.max(...timeline.map(item => item.startTime + item.duration), 0);
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const dataUrl = e.target?.result as string;
        addTimelineItem(dataUrl);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAudioUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const dataUrl = e.target?.result as string;
        setAudioUrl(dataUrl);
        toast.success('Audio cargado exitosamente');
      };
      reader.readAsDataURL(file);
    }
  };

  const generateSRT = () => {
    const itemsWithText = timeline.filter(item => item.text.trim());

    if (itemsWithText.length === 0) {
      toast.error('No hay texto en el timeline para generar subtítulos');
      return;
    }

    let srtContent = '';
    itemsWithText.forEach((item, index) => {
      const startTime = item.startTime;
      const endTime = startTime + item.duration;

      const formatTime = (seconds: number) => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`;
      };

      srtContent += `${index + 1}\n`;
      srtContent += `${formatTime(startTime)} --> ${formatTime(endTime)}\n`;
      srtContent += `${item.text}\n\n`;
    });

    setSrtContent(srtContent);
    toast.success(`SRT generado con ${itemsWithText.length} subtítulos`);
  };

  const composeVideo = async () => {
    if (timeline.length === 0) {
      toast.error('Por favor agrega clips al timeline');
      return;
    }

    const jobId = `timeline-${Date.now()}`;
    setCurrentJob(jobId);
    setIsGenerating(true);
    setProgress(0);

    try {
      // Prepare images array
      const images = timeline.map(item => ({
        url: item.imageUrl,
        duration: item.duration,
        kenburns: item.kenburns,
        text: item.text,
        pos: item.textPosition,
      }));

      // Prepare output filename
      const outputName = videoSettings.outputName || `video-${jobId}.mp4`;

      // Prepare payload
      const payload = {
        job_id: jobId,
        images,
        audio: audioUrl,
        srt: srtContent,
        out: outputName,
        fade_in_ms: videoSettings.fadeInMs,
        fade_out_ms: videoSettings.fadeOutMs,
        loudnorm: videoSettings.loudnorm,
      };

      // Add job to store
      const newJob = {
        job_id: jobId,
        state: 'queued' as const,
        progress: 0,
        outputs: [],
        type: 'compose' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      addJob(newJob);
      toast.info('Iniciando composición de video...');

      // Call compose API
      await apiService.createComposeJob(payload);

      // Monitor progress
      const progressInterval = setInterval(async () => {
        try {
          const status = await apiService.getJobStatus(jobId);

          if (status.state === 'done') {
            clearInterval(progressInterval);
            setProgress(100);

            // Get video result
            const result = await apiService.getComposeResult(jobId);

            if (result.video_url) {
              setVideoUrl(result.video_url);
              toast.success(`Video completado: ${(result.size_bytes! / 1024 / 1024).toFixed(1)}MB`);
            }

            updateJob(jobId, {
              state: 'done',
              progress: 100,
            });

            setIsGenerating(false);
            setCurrentJob(null);
          } else if (status.state === 'error') {
            clearInterval(progressInterval);
            toast.error('Error en la composición del video');
            setIsGenerating(false);
            setCurrentJob(null);
          } else {
            setProgress(status.progress);
          }
        } catch (error) {
          clearInterval(progressInterval);
          console.error('Error checking progress:', error);
        }
      }, 3000);

    } catch (error) {
      console.error('Error composing video:', error);

      if (currentJob) {
        updateJob(currentJob, {
          state: 'error',
          error_message: error instanceof Error ? error.message : 'Error desconocido',
        });
      }

      toast.error('Error al componer video: ' + (error instanceof Error ? error.message : 'Error desconocido'));
      setIsGenerating(false);
      setCurrentJob(null);
    }
  };

  const downloadVideo = () => {
    if (videoUrl) {
      const link = document.createElement('a');
      link.href = videoUrl;
      link.download = videoSettings.outputName || `timeline-${Date.now()}.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success('Descarga iniciada');
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold flex items-center justify-center gap-2">
          <Film className="w-8 h-8 text-blue-500" />
          Timeline de Video
        </h1>
        <p className="text-gray-600">
          Compone tu video profesional con imágenes, audio y efectos
        </p>
      </div>

      {/* Timeline Stats */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">{timeline.length}</div>
              <div className="text-sm text-gray-600">Clips</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">{getTotalDuration()}s</div>
              <div className="text-sm text-gray-600">Duración Total</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {timeline.filter(item => item.text.trim()).length}
              </div>
              <div className="text-sm text-gray-600">Textos</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-600">
                {audioUrl ? 'Sí' : 'No'}
              </div>
              <div className="text-sm text-gray-600">Audio</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="audio">Audio</TabsTrigger>
          <TabsTrigger value="settings">Configuración</TabsTrigger>
          <TabsTrigger value="result">Resultado</TabsTrigger>
        </TabsList>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="space-y-4">
          {/* Add Clip Bar */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex gap-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  variant="outline"
                  className="flex-1"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Subir Imagen
                </Button>
                <Button
                  onClick={() => addTimelineItem()}
                  variant="outline"
                >
                  <Eye className="w-4 h-4 mr-2" />
                  Imagen Demo
                </Button>
                <Button
                  onClick={composeVideo}
                  disabled={isGenerating || timeline.length === 0}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Componiendo...
                    </>
                  ) : (
                    <>
                      <Wand2 className="w-4 h-4 mr-2" />
                      Componer Video
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Timeline Items */}
          <div className="space-y-4">
            {timeline.map((item, index) => (
              <Card key={item.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Clip {index + 1}</CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">
                        <Clock className="w-3 h-3 mr-1" />
                        {item.startTime}s - {item.startTime + item.duration}s
                      </Badge>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => removeTimelineItem(item.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Image Preview */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Imagen</Label>
                      <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
                        <img
                          src={item.imageUrl}
                          alt={`Clip ${index + 1}`}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    </div>

                    {/* Settings */}
                    <div className="space-y-3">
                      {/* Duration */}
                      <div className="space-y-2">
                        <Label>Duración (segundos)</Label>
                        <Input
                          type="number"
                          value={item.duration}
                          onChange={(e) => updateTimelineItem(item.id, { duration: parseInt(e.target.value) || 1 })}
                          min="1"
                          max="30"
                        />
                      </div>

                      {/* Ken Burns Effect */}
                      <div className="space-y-2">
                        <Label>Efecto Ken Burns</Label>
                        <Select
                          value={item.kenburns}
                          onValueChange={(value) => updateTimelineItem(item.id, { kenburns: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {KENBURNS_EFFECTS.map((effect) => (
                              <SelectItem key={effect.id} value={effect.id}>
                                <div>
                                  <div className="font-medium">{effect.name}</div>
                                  <div className="text-xs text-gray-500">{effect.description}</div>
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Text Settings */}
                      <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                          <Type className="w-4 h-4" />
                          Texto en Video
                        </Label>
                        <Textarea
                          placeholder="Texto para mostrar en este clip..."
                          value={item.text}
                          onChange={(e) => updateTimelineItem(item.id, { text: e.target.value })}
                          className="min-h-[60px]"
                        />
                      </div>

                      {/* Text Position */}
                      {item.text && (
                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-2">
                            <Label>Posición</Label>
                            <Select
                              value={item.textPosition}
                              onValueChange={(value) => updateTimelineItem(item.id, { textPosition: value })}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {TEXT_POSITIONS.map((pos) => (
                                  <SelectItem key={pos.id} value={pos.id}>
                                    {pos.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Tamaño Fuente</Label>
                            <Input
                              type="number"
                              value={item.fontSize}
                              onChange={(e) => updateTimelineItem(item.id, { fontSize: parseInt(e.target.value) || 24 })}
                              min="12"
                              max="72"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Audio Tab */}
        <TabsContent value="audio" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Volume2 className="w-5 h-5" />
                Configuración de Audio
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Audio Upload */}
              <div className="space-y-2">
                <Label>Archivo de Audio (Opcional)</Label>
                <input
                  ref={audioInputRef}
                  type="file"
                  accept="audio/*"
                  onChange={handleAudioUpload}
                  className="hidden"
                />
                <Button
                  onClick={() => audioInputRef.current?.click()}
                  variant="outline"
                  className="w-full"
                >
                  <Music className="w-4 h-4 mr-2" />
                  Subir Audio
                </Button>
              </div>

              {/* Audio Preview */}
              {audioUrl && (
                <div className="space-y-2">
                  <Label>Audio Cargado</Label>
                  <audio controls className="w-full" src={audioUrl}>
                    Tu navegador no soporta el elemento de audio.
                  </audio>
                </div>
              )}

              {/* SRT Subtitles */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Subtítulos SRT</Label>
                  <Button
                    onClick={generateSRT}
                    variant="outline"
                    size="sm"
                    disabled={timeline.filter(item => item.text.trim()).length === 0}
                  >
                    Generar desde Textos
                  </Button>
                </div>
                <Textarea
                  placeholder="Pega el contenido SRT aquí o genera automáticamente..."
                  value={srtContent}
                  onChange={(e) => setSrtContent(e.target.value)}
                  className="min-h-[120px] font-mono text-xs"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Configuración de Video
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                {/* Fade In */}
                <div className="space-y-2">
                  <Label>Fade In (ms)</Label>
                  <Input
                    type="number"
                    value={videoSettings.fadeInMs}
                    onChange={(e) => setVideoSettings(prev => ({ ...prev, fadeInMs: parseInt(e.target.value) || 0 }))}
                    min="0"
                    max="5000"
                    step="100"
                  />
                </div>

                {/* Fade Out */}
                <div className="space-y-2">
                  <Label>Fade Out (ms)</Label>
                  <Input
                    type="number"
                    value={videoSettings.fadeOutMs}
                    onChange={(e) => setVideoSettings(prev => ({ ...prev, fadeOutMs: parseInt(e.target.value) || 0 }))}
                    min="0"
                    max="5000"
                    step="100"
                  />
                </div>

                {/* Output Name */}
                <div className="space-y-2">
                  <Label>Nombre del Archivo</Label>
                  <Input
                    placeholder="mi-video.mp4"
                    value={videoSettings.outputName}
                    onChange={(e) => setVideoSettings(prev => ({ ...prev, outputName: e.target.value }))}
                  />
                </div>

                {/* Loudnorm */}
                <div className="space-y-2">
                  <Label>Normalización de Audio</Label>
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={videoSettings.loudnorm}
                      onCheckedChange={(checked) => setVideoSettings(prev => ({ ...prev, loudnorm: checked }))}
                    />
                    <span className="text-sm text-gray-600">
                      {videoSettings.loudnorm ? 'Activada' : 'Desactivada'}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Result Tab */}
        <TabsContent value="result" className="space-y-4">
          {/* Progress */}
          {isGenerating && (
            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Componiendo video...</span>
                    <span>{progress}%</span>
                  </div>
                  <Progress value={progress} className="h-2" />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Video Result */}
          {videoUrl && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileVideo className="w-5 h-5 text-green-500" />
                  Video Generado
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Video Player */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <video
                    controls
                    className="w-full max-w-2xl mx-auto rounded-lg"
                    src={videoUrl}
                  >
                    Tu navegador no soporta el elemento de video.
                  </video>
                </div>

                {/* Video Info */}
                <div className="grid md:grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-lg font-semibold">Duración</div>
                    <div className="text-sm text-gray-600">{getTotalDuration()} segundos</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold">Resolución</div>
                    <div className="text-sm text-gray-600">1080 x 1920 (Vertical)</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold">Clips</div>
                    <div className="text-sm text-gray-600">{timeline.length} escenas</div>
                  </div>
                </div>

                {/* Download Button */}
                <div className="flex justify-center">
                  <Button onClick={downloadVideo} size="lg" className="bg-green-600 hover:bg-green-700">
                    <Download className="w-5 h-5 mr-2" />
                    Descargar Video MP4
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Empty State */}
          {!isGenerating && !videoUrl && (
            <Card>
              <CardContent className="pt-12 pb-12">
                <div className="text-center space-y-4">
                  <FileVideo className="w-16 h-16 text-gray-400 mx-auto" />
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Sin video generado
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Configura tu timeline y haz clic en "Componer Video" para generar tu video.
                    </p>
                    <Button
                      onClick={() => setActiveTab('timeline')}
                      variant="outline"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      Configurar Timeline
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}