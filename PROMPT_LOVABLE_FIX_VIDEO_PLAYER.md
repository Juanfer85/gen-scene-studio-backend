# 🎬 PROMPT PARA LOVABLE - Corregir Video Player en Jobs Hub

---

## 📋 INSTRUCCIONES PARA LOVABLE

Copia y pega este prompt en Lovable.dev:

---

# Corregir Video Player en Blanco en Jobs Hub

El video player en Jobs Hub muestra una pantalla en blanco con un ícono de imagen rota, pero el video existe y es accesible.

## Problema Actual:

El componente de video en Jobs Hub no está cargando correctamente el video. Se ve una pantalla en blanco aunque el archivo existe y es accesible en:
```
https://api.genscenestudio.com/files/{job_id}/universe_complete.mp4
```

## Verificación:

El video SÍ existe y es accesible:
- ✅ Archivo: 2.3 MB
- ✅ URL funciona: `https://api.genscenestudio.com/files/qcf-0d98327b-652/universe_complete.mp4`
- ✅ Content-Type: `video/mp4`
- ✅ Status: 200 OK

## Solución Requerida:

### **IMPORTANTE: Manejo de Aspect Ratio**

Los videos generados por Gen Scene Studio son principalmente **verticales (9:16)** para TikTok, Reels y Shorts.

**Problema Actual:**
```
┌─────────────────────────────────────┐
│ ⬛⬛⬛⬛  VIDEO  ⬛⬛⬛⬛              │  ← Mucho espacio negro
│ ⬛⬛⬛⬛ VERTICAL ⬛⬛⬛⬛             │     a los lados
└─────────────────────────────────────┘
   Container 16:9 (horizontal)
```

**Solución Correcta:**
```
    ┌──────────┐
    │          │
    │  VIDEO   │  ← Video vertical centrado
    │ VERTICAL │     con ancho máximo
    │          │
    └──────────┘
   Container adaptado a 9:16
```

### 1. Encontrar el Componente del Video Player

Buscar en el código del frontend el componente que muestra los videos en Jobs Hub (probablemente en `src/pages/jobs-hub.tsx` o `src/components/JobCard.tsx` o similar).

### 2. Corregir la URL del Video

**Verificar que la URL se construye correctamente:**

```typescript
// ❌ INCORRECTO - URLs que NO funcionan:
const videoUrl = `/media/${jobId}/universe_complete.mp4`; // 401
const videoUrl = `https://genscenestudio.com/media/${jobId}/universe_complete.mp4`; // 401

// ✅ CORRECTO - URLs que SÍ funcionan:
const videoUrl = `https://api.genscenestudio.com/files/${jobId}/universe_complete.mp4`; // 200 OK
const videoUrl = `https://genscenestudio.com/files/${jobId}/universe_complete.mp4`; // 200 OK
```

### 3. Implementar Video Player Correcto

**Opción A: Usar elemento HTML5 video nativo**

```typescript
interface JobVideoPlayerProps {
  jobId: string;
  fileName?: string;
  aspectRatio?: string; // "9:16" para vertical, "16:9" para horizontal
}

function JobVideoPlayer({ 
  jobId, 
  fileName = "universe_complete.mp4",
  aspectRatio = "9:16" // Default a vertical para TikTok/Reels/Shorts
}: JobVideoPlayerProps) {
  const videoUrl = `https://api.genscenestudio.com/files/${jobId}/${fileName}`;
  
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  // Determinar si es video vertical u horizontal
  const isVertical = aspectRatio === "9:16" || aspectRatio === "1080:1920";
  
  return (
    <div className={`relative w-full bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center ${
      isVertical ? 'max-w-md mx-auto' : 'aspect-video'
    }`}>
      {/* Container con aspect ratio correcto */}
      <div className={`relative ${
        isVertical ? 'aspect-[9/16] w-full' : 'aspect-video w-full'
      }`}>
        {loading && !error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center z-10">
            <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
            <span className="ml-2 text-gray-400 text-sm mt-2">Cargando video...</span>
          </div>
        )}
        
        {error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-red-400 z-10">
            <AlertTriangle className="w-12 h-12 mb-2" />
            <p className="text-sm">Error al cargar el video</p>
            <button 
              onClick={() => { setError(false); setLoading(true); }}
              className="mt-2 px-4 py-2 bg-purple-600 rounded hover:bg-purple-700 text-sm"
            >
              Reintentar
            </button>
          </div>
        )}
      
      <video
        src={videoUrl}
        controls
        className="w-full h-full object-contain"
        onLoadedData={() => setLoading(false)}
        onError={() => {
          setError(true);
          setLoading(false);
          console.error('Error loading video:', videoUrl);
        }}
        preload="metadata"
      >
        Tu navegador no soporta el elemento de video.
      </video>
    </div>
  );
}
```

**Opción B: Usar ReactPlayer (si ya está instalado)**

```typescript
import ReactPlayer from 'react-player';

function JobVideoPlayer({ jobId, fileName = "universe_complete.mp4" }: JobVideoPlayerProps) {
  const videoUrl = `https://api.genscenestudio.com/files/${jobId}/${fileName}`;
  
  return (
    <div className="relative w-full aspect-video bg-gray-900 rounded-lg overflow-hidden">
      <ReactPlayer
        url={videoUrl}
        controls
        width="100%"
        height="100%"
        config={{
          file: {
            attributes: {
              controlsList: 'nodownload', // Opcional: deshabilitar descarga
              onContextMenu: (e) => e.preventDefault() // Opcional: deshabilitar menú contextual
            }
          }
        }}
      />
    </div>
  );
}
```

### 4. Agregar Botón de Descarga

```typescript
function JobVideoActions({ jobId, fileName = "universe_complete.mp4" }) {
  const videoUrl = `https://api.genscenestudio.com/files/${jobId}/${fileName}`;
  
  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = videoUrl;
    link.download = `${jobId}_${fileName}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(videoUrl);
      toast.success('Enlace copiado al portapapeles');
    } catch (error) {
      console.error('Error copying link:', error);
    }
  };

  return (
    <div className="flex gap-2 mt-3">
      <button
        onClick={handleDownload}
        className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
      >
        <Download className="w-4 h-4" />
        Descargar
      </button>
      
      <button
        onClick={handleCopyLink}
        className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
      >
        <Link className="w-4 h-4" />
        Copiar enlace
      </button>
    </div>
  );
}
```

### 5. Integrar en Jobs Hub

```typescript
// En el componente de Jobs Hub
function JobCard({ job }) {
  // Extraer aspect ratio del metadata del job
  const aspectRatio = job.metadata?.aspect_ratio || "9:16"; // Default a vertical
  
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      {/* Header del job */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">{job.job_id}</h3>
          <p className="text-sm text-gray-400">
            Creado: {new Date(job.created_at).toLocaleString()}
          </p>
          {/* Mostrar info del aspect ratio */}
          {job.metadata?.aspect_ratio && (
            <span className="inline-block mt-1 px-2 py-0.5 bg-purple-900/30 text-purple-400 text-xs rounded">
              {job.metadata.aspect_ratio === "9:16" ? "📱 Vertical" : "🖥️ Horizontal"}
            </span>
          )}
        </div>
        <span className={`px-3 py-1 rounded-full text-sm ${
          job.status === 'completed' ? 'bg-green-900/30 text-green-400' :
          job.status === 'processing' ? 'bg-blue-900/30 text-blue-400' :
          job.status === 'error' ? 'bg-red-900/30 text-red-400' :
          'bg-gray-700 text-gray-400'
        }`}>
          {job.status === 'completed' ? 'Completado' :
           job.status === 'processing' ? 'Procesando' :
           job.status === 'error' ? 'Error' :
           job.status}
        </span>
      </div>

      {/* Video Player - Solo mostrar si está completado */}
      {/* IMPORTANTE: Pasar aspectRatio al componente */}
      {job.status === 'completed' && (
        <>
          <JobVideoPlayer 
            jobId={job.job_id} 
            aspectRatio={aspectRatio}
          />
          <JobVideoActions jobId={job.job_id} />
        </>
      )}

      {/* Estado de procesamiento */}
      {job.status === 'processing' && (
        <div className={`bg-gray-900 rounded-lg flex items-center justify-center ${
          aspectRatio === "9:16" ? 'aspect-[9/16] max-w-md mx-auto' : 'aspect-video'
        }`}>
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-purple-500 mx-auto mb-3" />
            <p className="text-gray-400">{job.metadata?.current_phase || 'Procesando...'}</p>
            {job.progress && (
              <div className="mt-3 w-64 mx-auto">
                <Progress value={job.progress} className="h-2" />
                <p className="text-xs text-gray-500 mt-1">{job.progress}%</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error */}
      {job.status === 'error' && (
        <div className={`bg-red-900/10 rounded-lg flex items-center justify-center border border-red-500/30 ${
          aspectRatio === "9:16" ? 'aspect-[9/16] max-w-md mx-auto' : 'aspect-video'
        }`}>
          <div className="text-center text-red-400">
            <AlertTriangle className="w-12 h-12 mx-auto mb-3" />
            <p>Error al generar el video</p>
            {job.error_message && (
              <p className="text-sm mt-2 text-gray-400">{job.error_message}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

### 6. Agregar Estilos Responsivos

Para que se vea bien en diferentes tamaños de pantalla:

```typescript
// Estilos CSS adicionales si es necesario
const videoContainerStyles = {
  vertical: "max-w-md mx-auto", // Máximo 28rem (448px) de ancho para verticales
  horizontal: "w-full"
};

// En el componente:
<div className={`
  relative w-full bg-gray-900 rounded-lg overflow-hidden 
  flex items-center justify-center
  ${isVertical ? videoContainerStyles.vertical : videoContainerStyles.horizontal}
`}>
```

### 7. Soporte para Múltiples Aspect Ratios

Si en el futuro soportas más formatos:

```typescript
const getAspectRatioClass = (ratio: string) => {
  switch(ratio) {
    case "9:16":
    case "1080:1920":
      return "aspect-[9/16] max-w-md mx-auto"; // Vertical (TikTok, Reels)
    case "16:9":
    case "1920:1080":
      return "aspect-video w-full"; // Horizontal (YouTube)
    case "1:1":
    case "1080:1080":
      return "aspect-square max-w-lg mx-auto"; // Cuadrado (Instagram)
    case "4:5":
    case "1080:1350":
      return "aspect-[4/5] max-w-lg mx-auto"; // Instagram Portrait
    default:
      return "aspect-[9/16] max-w-md mx-auto"; // Default vertical
  }
};
```

## Puntos Importantes:

1. **URL Correcta:** Usar `https://api.genscenestudio.com/files/{jobId}/universe_complete.mp4`
2. **Aspect Ratio:** Videos son principalmente verticales (9:16) - usar `max-w-md mx-auto` para centrarlos
3. **Manejo de Errores:** Mostrar mensaje claro si el video no carga
4. **Estados:** Mostrar diferentes UIs para processing/completed/error con aspect ratio correcto
5. **Preload:** Usar `preload="metadata"` para cargar solo metadata inicialmente
6. **Container Adaptativo:** 
   - Vertical (9:16): `aspect-[9/16] max-w-md mx-auto` (máx 448px ancho)
   - Horizontal (16:9): `aspect-video w-full`
7. **Metadata:** Extraer `job.metadata.aspect_ratio` para determinar orientación
8. **Object Fit:** Usar `object-contain` para que el video se ajuste sin recortar

## Testing:

Después de implementar, verificar que:
1. ✅ El video se muestra correctamente en Jobs Hub
2. ✅ **Videos verticales (9:16) se muestran centrados con ancho máximo de ~448px**
3. ✅ **No hay barras negras excesivas a los lados de videos verticales**
4. ✅ Los controles de reproducción funcionan
5. ✅ El botón de descarga funciona
6. ✅ Se muestra loading mientras carga
7. ✅ Se muestra error si falla la carga
8. ✅ Solo se muestra video player si job.status === 'completed'
9. ✅ El aspect ratio se adapta correctamente según el metadata del job
10. ✅ En móvil, el video vertical ocupa todo el ancho disponible (hasta max-w-md)

### Casos de Prueba:

**Video Vertical (9:16):**
- Container debe tener `max-w-md mx-auto`
- Video debe verse centrado
- No debe haber mucho espacio negro a los lados

**Video Horizontal (16:9):**
- Container debe ocupar todo el ancho
- Video debe verse en formato landscape

**Responsive:**
- En desktop: Video vertical centrado con máx 448px
- En móvil: Video vertical ocupa casi todo el ancho

---

¿Puedes implementar estos cambios para que los videos se muestren correctamente en Jobs Hub?
