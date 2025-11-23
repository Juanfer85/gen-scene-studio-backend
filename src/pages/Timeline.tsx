import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { Video, Plus, Trash2, Download, Eye, Clock, CheckCircle, XCircle } from 'lucide-react';
import { useApiCall } from '@/hooks/useApiCall';
import apiClient from '@/lib/api';
import { ComposeIn, ComposeImage } from '@/types';

interface TimelineItem {
  id: string;
  url: string;
  duration: number;
  kenburns: string;
  text: string;
  pos: string;
}

const Timeline: React.FC = () => {
  const [items, setItems] = useState<TimelineItem[]>([]);
  const [audioUrl, setAudioUrl] = useState('');
  const [srtContent, setSrtContent] = useState('');
  const [outputName, setOutputName] = useState('');
  const [jobId] = useState(() => `compose_${Date.now()}`);
  const [composeStatus, setComposeStatus] = useState<{
    state: string;
    progress: number;
    videoUrl?: string;
  } | null>(null);

  const {
    execute: composeVideo,
    loading,
    error
  } = useApiCall(
    (payload: ComposeIn) => apiClient.composeVideo(payload),
    {
      onSuccess: (result) => {
        console.log('Video composition started:', result);
        // Start polling for result
        pollComposeResult();
      },
      onError: (error) => {
        console.error('Error composing video:', error);
      }
    }
  );

  const pollComposeResult = async () => {
    try {
      const result = await apiClient.pollComposeResult(
        jobId,
        (result) => {
          setComposeStatus({
            state: result.ready ? 'done' : 'processing',
            progress: result.ready ? 100 : 50,
            videoUrl: result.video_url
          });
        },
        3000,
        300000
      );

      setComposeStatus({
        state: 'done',
        progress: 100,
        videoUrl: result.video_url
      });
    } catch (error) {
      setComposeStatus({
        state: 'error',
        progress: 0
      });
    }
  };

  const addItem = () => {
    const newItem: TimelineItem = {
      id: `item_${Date.now()}`,
      url: '',
      duration: 3,
      kenburns: 'in',
      text: '',
      pos: 'bottom'
    };
    setItems([...items, newItem]);
  };

  const removeItem = (id: string) => {
    setItems(items.filter(item => item.id !== id));
  };

  const updateItem = (id: string, updates: Partial<TimelineItem>) => {
    setItems(items.map(item =>
      item.id === id ? { ...item, ...updates } : item
    ));
  };

  const getTotalDuration = (): number => {
    return items.reduce((total, item) => total + item.duration, 0);
  };

  const handleCompose = async () => {
    if (items.length === 0) {
      alert('Por favor agrega al menos un elemento a la timeline');
      return;
    }

    if (!audioUrl) {
      alert('Por favor ingresa la URL del archivo de audio');
      return;
    }

    if (getTotalDuration() > 59) {
      alert('La duración total no puede exceder los 59 segundos');
      return;
    }

    const composeImages: ComposeImage[] = items.map(item => ({
      url: item.url,
      duration: item.duration,
      kenburns: item.kenburns,
      text: item.text,
      pos: item.pos
    }));

    const payload: ComposeIn = {
      job_id: jobId,
      images: composeImages,
      audio: audioUrl,
      srt: srtContent,
      out: outputName || `${jobId}.mp4`
    };

    try {
      setComposeStatus({ state: 'queued', progress: 0 });
      await composeVideo(payload);
    } catch (error) {
      setComposeStatus(null);
    }
  };

  const handleDownload = () => {
    if (composeStatus?.videoUrl) {
      const link = document.createElement('a');
      link.href = composeStatus.videoUrl;
      link.download = outputName || `${jobId}.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const getStatusIcon = (state: string) => {
    switch (state) {
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

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-foreground">Timeline de Video</h1>
          <p className="text-muted-foreground">Crea videos a partir de imágenes y audio</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Video className="h-5 w-5" />
              Elementos de la Timeline
            </CardTitle>
            <CardDescription>
              Agrega imágenes y configura su duración y efectos
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <div className="text-sm text-muted-foreground">
                {items.length} elementos • Duración total: {getTotalDuration()}s (máx. 59s)
              </div>
              <Button onClick={addItem} size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Agregar Elemento
              </Button>
            </div>

            <div className="space-y-3">
              {items.map((item, index) => (
                <div key={item.id} className="p-4 border border-border rounded-lg space-y-3">
                  <div className="flex justify-between items-center">
                    <h4 className="font-medium">Elemento {index + 1}</h4>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeItem(item.id)}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">URL de imagen</label>
                      <Input
                        value={item.url}
                        onChange={(e) => updateItem(item.id, { url: e.target.value })}
                        placeholder="https://..."
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-1">Duración (segundos)</label>
                      <Input
                        type="number"
                        value={item.duration}
                        onChange={(e) => updateItem(item.id, { duration: parseInt(e.target.value) || 1 })}
                        min="1"
                        max="30"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-1">Efecto Ken Burns</label>
                      <select
                        value={item.kenburns}
                        onChange={(e) => updateItem(item.id, { kenburns: e.target.value })}
                        className="w-full p-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                      >
                        <option value="in">Zoom In</option>
                        <option value="out">Zoom Out</option>
                        <option value="left">Pan Left</option>
                        <option value="right">Pan Right</option>
                        <option value="up">Pan Up</option>
                        <option value="down">Pan Down</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-1">Texto (opcional)</label>
                      <Input
                        value={item.text}
                        onChange={(e) => updateItem(item.id, { text: e.target.value })}
                        placeholder="Texto overlay"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-1">Posición del texto</label>
                      <select
                        value={item.pos}
                        onChange={(e) => updateItem(item.id, { pos: e.target.value })}
                        className="w-full p-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                      >
                        <option value="top">Arriba</option>
                        <option value="bottom">Abajo</option>
                        <option value="center">Centro</option>
                        <option value="left">Izquierda</option>
                        <option value="right">Derecha</option>
                      </select>
                    </div>
                  </div>
                </div>
              ))}

              {items.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No hay elementos en la timeline. Haz clic en "Agregar Elemento" para comenzar.
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Configuración de Composición</CardTitle>
            <CardDescription>
              Configura el audio y opciones de salida
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label htmlFor="audioUrl" className="block text-sm font-medium mb-2">
                URL del Audio
              </label>
              <Input
                id="audioUrl"
                value={audioUrl}
                onChange={(e) => setAudioUrl(e.target.value)}
                placeholder="https://ejemplo.com/audio.wav"
              />
            </div>

            <div>
              <label htmlFor="srtContent" className="block text-sm font-medium mb-2">
                Contenido SRT (opcional)
              </label>
              <textarea
                id="srtContent"
                value={srtContent}
                onChange={(e) => setSrtContent(e.target.value)}
                placeholder="1&#10;00:00:00,000 --> 00:00:03,000&#10;Tu texto aquí&#10;&#10;2&#10;00:00:03,000 --> 00:00:06,000&#10;Otro texto aquí"
                className="w-full min-h-[120px] p-3 border border-input rounded-md bg-background text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 font-mono text-sm"
              />
            </div>

            <div>
              <label htmlFor="outputName" className="block text-sm font-medium mb-2">
                Nombre de salida (opcional)
              </label>
              <Input
                id="outputName"
                value={outputName}
                onChange={(e) => setOutputName(e.target.value)}
                placeholder="video_final.mp4"
              />
            </div>

            <div className="flex justify-between items-center">
              <div className="text-sm text-muted-foreground">
                Job ID: {jobId}
              </div>
              <Button
                onClick={handleCompose}
                disabled={loading || items.length === 0 || !audioUrl}
                loading={loading}
              >
                {loading ? 'Componiendo...' : 'Componer Video'}
              </Button>
            </div>

            {error && (
              <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md">
                <div className="text-sm text-destructive">
                  Error: {error.message}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {composeStatus && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {getStatusIcon(composeStatus.state)}
                Estado del Compose
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Progreso</span>
                  <span>{composeStatus.progress}%</span>
                </div>
                <Progress value={composeStatus.progress} />
              </div>

              {composeStatus.state === 'done' && composeStatus.videoUrl && (
                <div className="space-y-3">
                  <div className="p-3 bg-muted rounded-md">
                    <div className="text-sm font-mono text-muted-foreground break-all">
                      {composeStatus.videoUrl}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() => window.open(composeStatus.videoUrl, '_blank')}
                      className="flex items-center gap-2"
                    >
                      <Eye className="h-4 w-4" />
                      Ver Video
                    </Button>

                    <Button
                      variant="outline"
                      onClick={handleDownload}
                      className="flex items-center gap-2"
                    >
                      <Download className="h-4 w-4" />
                      Descargar
                    </Button>
                  </div>
                </div>
              )}

              {composeStatus.state === 'error' && (
                <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md">
                  <div className="text-sm text-destructive">
                    El proceso de composición falló. Por favor verifica los archivos de entrada e intenta nuevamente.
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Timeline;