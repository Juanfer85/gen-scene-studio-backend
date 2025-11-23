import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { Volume2, Download, Play, Pause } from 'lucide-react';
import { useApiCall } from '@/hooks/useApiCall';
import apiClient from '@/lib/api';
import { TTSIn } from '@/types';

const Voz: React.FC = () => {
  const [text, setText] = useState('');
  const [voice, setVoice] = useState('');
  const [wpm, setWpm] = useState(160);
  const [jobId] = useState(() => `tts_${Date.now()}`);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioDuration, setAudioDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const {
    execute: generateSpeech,
    loading,
    error
  } = useApiCall(
    (payload: TTSIn) => apiClient.generateSpeech(payload),
    {
      onSuccess: (result) => {
        setAudioUrl(result.audio_url);
        setAudioDuration(result.duration_s);
      },
      onError: (error) => {
        console.error('Error generating speech:', error);
      }
    }
  );

  const handleGenerate = async () => {
    if (!text.trim()) {
      alert('Por favor ingresa texto para convertir a voz');
      return;
    }

    const payload: TTSIn = {
      job_id: jobId,
      text: text.trim(),
      voice: voice || undefined,
      wpm: wpm || undefined
    };

    try {
      await generateSpeech(payload);
    } catch (error) {
      console.error('Error generating speech:', error);
    }
  };

  const handlePlayPause = () => {
    const audio = document.getElementById('audio-player') as HTMLAudioElement;
    if (audio) {
      if (isPlaying) {
        audio.pause();
      } else {
        audio.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleDownload = () => {
    if (audioUrl) {
      const link = document.createElement('a');
      link.href = audioUrl;
      link.download = `voice_${jobId}.wav`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-foreground">Generador de Voz</h1>
          <p className="text-muted-foreground">Convierte texto a audio usando IA</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Volume2 className="h-5 w-5" />
              Texto a Voz
            </CardTitle>
            <CardDescription>
              Ingresa el texto que quieres convertir a audio
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label htmlFor="text" className="block text-sm font-medium mb-2">
                Texto
              </label>
              <textarea
                id="text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Ingresa el texto que quieres convertir a voz..."
                className="w-full min-h-[120px] p-3 border border-input rounded-md bg-background text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                maxLength={1000}
              />
              <div className="text-right text-sm text-muted-foreground mt-1">
                {text.length}/1000 caracteres
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="voice" className="block text-sm font-medium mb-2">
                  Voz (opcional)
                </label>
                <Input
                  id="voice"
                  value={voice}
                  onChange={(e) => setVoice(e.target.value)}
                  placeholder="ej: es-ES-Standard-A"
                />
              </div>

              <div>
                <label htmlFor="wpm" className="block text-sm font-medium mb-2">
                  Palabras por minuto
                </label>
                <Input
                  id="wpm"
                  type="number"
                  value={wpm}
                  onChange={(e) => setWpm(parseInt(e.target.value) || 160)}
                  min="50"
                  max="300"
                />
              </div>
            </div>

            <div className="flex justify-between items-center">
              <div className="text-sm text-muted-foreground">
                Job ID: {jobId}
              </div>
              <Button
                onClick={handleGenerate}
                disabled={loading || !text.trim()}
                loading={loading}
              >
                {loading ? 'Generando...' : 'Generar Voz'}
              </Button>
            </div>

            {loading && (
              <div className="space-y-2">
                <div className="text-sm text-muted-foreground">Procesando audio...</div>
                <Progress value={undefined} className="h-2" />
              </div>
            )}

            {error && (
              <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md">
                <div className="text-sm text-destructive">
                  Error: {error.message}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {audioUrl && (
          <Card>
            <CardHeader>
              <CardTitle>Audio Generado</CardTitle>
              <CardDescription>
                Duración: {formatDuration(audioDuration)}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <audio
                id="audio-player"
                src={audioUrl}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                onEnded={() => setIsPlaying(false)}
                className="w-full"
                controls
              />

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={handlePlayPause}
                  className="flex items-center gap-2"
                >
                  {isPlaying ? (
                    <>
                      <Pause className="h-4 w-4" />
                      Pausar
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Reproducir
                    </>
                  )}
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

              <div className="p-3 bg-muted rounded-md">
                <div className="text-sm font-mono text-muted-foreground">
                  URL: {audioUrl}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Voz;