import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Textarea,
  Select,
  SelectItem,
  Input,
  Label,
  Badge,
  Progress
} from './ui';
import { Play, Download, Loader2, Mic, Volume2 } from 'lucide-react';
import { toast } from 'sonner';
import { apiService } from '@/services/api';
import { useJobsStore } from '@/store/jobsStore';

const VOICES = [
  { id: 'es_ES-carlfm-high', name: 'Carlos (Masculino)', language: 'es-ES' },
  { id: 'es_ES-davefx-high', name: 'David (Masculino)', language: 'es-ES' },
  { id: 'en_US-lessac-high', name: 'Lessac (Inglés)', language: 'en-US' },
];

const WPM_OPTIONS = [
  { value: 120, label: 'Lento (120 WPM)' },
  { value: 160, label: 'Normal (160 WPM)' },
  { value: 200, label: 'Rápido (200 WPM)' },
  { value: 240, label: 'Muy Rápido (240 WPM)' },
];

export function Voz() {
  const [text, setText] = useState('');
  const [voice, setVoice] = useState('es_ES-carlfm-high');
  const [wpm, setWpm] = useState(160);
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentJob, setCurrentJob] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const [progress, setProgress] = useState(0);

  const { addJob, updateJob } = useJobsStore();

  const generateAudio = async () => {
    if (!text.trim()) {
      toast.error('Por favor ingresa un texto para generar audio');
      return;
    }

    const jobId = `tts-${Date.now()}`;
    setCurrentJob(jobId);
    setIsGenerating(true);
    setProgress(0);

    try {
      // Add job to store
      const newJob = {
        job_id: jobId,
        state: 'queued' as const,
        progress: 0,
        outputs: [],
        type: 'tts' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      addJob(newJob);
      toast.info('Iniciando generación de audio...');

      // Call TTS API
      const payload = {
        job_id: jobId,
        text: text.trim(),
        voice,
        wpm,
      };

      const result = await apiService.createTTSJob(payload);

      // Update job with result
      updateJob(jobId, {
        state: 'done',
        progress: 100,
        outputs: [{
          id: '1',
          prompt: text.trim(),
          negative: '',
          seed: 0,
          quality: 'draft' as const,
          url: result.audio_url,
          status: 'done' as const,
        }],
      });

      setAudioUrl(result.audio_url);
      setDuration(result.duration_s);
      setProgress(100);

      toast.success(`Audio generado exitosamente (${result.duration_s.toFixed(1)}s)`);

    } catch (error) {
      console.error('Error generating TTS:', error);

      if (currentJob) {
        updateJob(currentJob, {
          state: 'error',
          error_message: error instanceof Error ? error.message : 'Error desconocido',
        });
      }

      toast.error('Error al generar audio: ' + (error instanceof Error ? error.message : 'Error desconocido'));
    } finally {
      setIsGenerating(false);
      setCurrentJob(null);
    }
  };

  const downloadAudio = () => {
    if (audioUrl) {
      const link = document.createElement('a');
      link.href = audioUrl;
      link.download = `tts-${Date.now()}.wav`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success('Descarga iniciada');
    }
  };

  const playAudio = () => {
    if (audioUrl) {
      const audio = new Audio(audioUrl);
      audio.play();
      toast.info('Reproduciendo audio...');
    }
  };

  const sampleTexts = [
    "¿Qué pasaría si los humanos pudieran volar? Las ciudades cambiarían para siempre...",
    "Imagina despertar un día y descubrir que tienes superpoderes...",
    "Si los animales pudieran hablar, ¿qué secretos nos contarían?",
    "What if gravity suddenly disappeared for just 5 minutes?",
  ];

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold flex items-center justify-center gap-2">
          <Volume2 className="w-8 h-8 text-blue-500" />
          Generador de Voz AI
        </h1>
        <p className="text-gray-600">
          Convierte tu texto en voz humana natural con inteligencia artificial
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Configuration Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mic className="w-5 h-5" />
              Configuración de Voz
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Voice Selection */}
            <div className="space-y-2">
              <Label>Voz</Label>
              <Select value={voice} onValueChange={setVoice}>
                <option value="" disabled>Selecciona una voz</option>
                {VOICES.map((v) => (
                  <SelectItem key={v.id} value={v.id}>
                    {v.name} ({v.language})
                  </SelectItem>
                ))}
              </Select>
            </div>

            {/* Speed (WPM) */}
            <div className="space-y-2">
              <Label>Velocidad</Label>
              <Select value={wpm.toString()} onValueChange={(val) => setWpm(parseInt(val))}>
                <option value="" disabled>Selecciona velocidad</option>
                {WPM_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value.toString()}>
                    {option.label}
                  </SelectItem>
                ))}
              </Select>
            </div>

            {/* Sample Texts */}
            <div className="space-y-2">
              <Label>Textos de Ejemplo</Label>
              <div className="space-y-1">
                {sampleTexts.map((sample, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    className="w-full text-left justify-start h-auto p-2 text-xs"
                    onClick={() => setText(sample)}
                  >
                    {sample.substring(0, 60)}...
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Text Input Panel */}
        <Card>
          <CardHeader>
            <CardTitle>Texto para Convertir</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="Pega o escribe el texto que quieres convertir a voz..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="min-h-[200px] resize-none"
              disabled={isGenerating}
            />

            <div className="text-sm text-gray-500">
              Caracteres: {text.length} |
              Palabras aprox: {text.split(/\s+/).filter(w => w.length > 0).length}
            </div>

            <Button
              onClick={generateAudio}
              disabled={isGenerating || !text.trim()}
              className="w-full"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generando Audio...
                </>
              ) : (
                <>
                  <Volume2 className="w-4 h-4 mr-2" />
                  Generar Audio
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Progress Section */}
      {isGenerating && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Generando audio...</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Section */}
      {audioUrl && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Play className="w-5 h-5 text-green-500" />
              Audio Generado
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Audio Player */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <audio controls className="w-full" src={audioUrl}>
                  Tu navegador no soporta el elemento de audio.
                </audio>
              </div>

              {/* Audio Info */}
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">
                  Duración: {duration?.toFixed(1)}s
                </Badge>
                <Badge variant="secondary">
                  Voz: {VOICES.find(v => v.id === voice)?.name}
                </Badge>
                <Badge variant="secondary">
                  Velocidad: {wpm} WPM
                </Badge>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                <Button onClick={playAudio} variant="outline">
                  <Play className="w-4 h-4 mr-2" />
                  Reproducir
                </Button>
                <Button onClick={downloadAudio}>
                  <Download className="w-4 h-4 mr-2" />
                  Descargar WAV
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}