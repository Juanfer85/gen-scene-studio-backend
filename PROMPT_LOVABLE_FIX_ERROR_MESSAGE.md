# 🔧 PROMPT PARA LOVABLE - Corregir Mensaje "Error" en Jobs

---

## 📋 INSTRUCCIONES PARA LOVABLE

Copia y pega este prompt en Lovable.dev:

---

# Corregir Mensaje "Error" Falso en Estado de Jobs

Hay un problema cosmético en el frontend donde se muestra "Error: 🤖 Dreaming up concept (Kie.ai)..." cuando un video se está generando correctamente.

## Problema Actual:

El frontend está mostrando incorrectamente un mensaje de "Error:" cuando el job está en progreso. El video se genera exitosamente, pero el usuario ve un mensaje de error que causa confusión.

## Causa del Problema:

El backend envía el estado del job con un campo `metadata.current_phase` que contiene mensajes como:
- "🧠 Dreaming up concept (Kie.ai)..."
- "🎬 Generating AI video..."
- "✨ Finalizing..."

El frontend está interpretando estos mensajes como errores cuando en realidad son mensajes de progreso normal.

## Solución Requerida:

### 1. Encontrar el Componente que Muestra el Estado del Job

Buscar en el código del frontend el componente que muestra el estado de los jobs (probablemente en `src/pages/quick-create.tsx` o `src/components/JobStatus.tsx` o similar).

### 2. Corregir la Lógica de Visualización

**Antes (Código Incorrecto):**
```typescript
// NO hacer esto:
if (job.metadata?.current_phase) {
  return <div className="text-red-500">Error: {job.metadata.current_phase}</div>
}
```

**Después (Código Correcto):**
```typescript
// Verificar el estado real del job, no solo el metadata
if (job.status === "error" && job.error_message) {
  // Solo mostrar error si el job realmente falló
  return (
    <div className="flex items-center gap-2 text-red-500">
      <AlertTriangle className="w-4 h-4" />
      <span>Error: {job.error_message}</span>
    </div>
  );
}

if (job.status === "processing" && job.metadata?.current_phase) {
  // Mostrar como progreso, NO como error
  return (
    <div className="flex items-center gap-2 text-blue-500">
      <Loader2 className="w-4 h-4 animate-spin" />
      <span>{job.metadata.current_phase}</span>
    </div>
  );
}

if (job.status === "completed" || job.status === "done") {
  return (
    <div className="flex items-center gap-2 text-green-500">
      <CheckCircle className="w-4 h-4" />
      <span>✅ Video generado exitosamente</span>
    </div>
  );
}
```

### 3. Mejorar la Visualización del Progreso

Agregar una barra de progreso visual:

```typescript
import { Progress } from '@/components/ui/progress';
import { Loader2, CheckCircle, AlertTriangle } from 'lucide-react';

function JobStatusDisplay({ job }) {
  const getStatusColor = () => {
    if (job.status === "error") return "text-red-500";
    if (job.status === "completed" || job.status === "done") return "text-green-500";
    return "text-blue-500";
  };

  const getStatusIcon = () => {
    if (job.status === "error") return <AlertTriangle className="w-5 h-5" />;
    if (job.status === "completed" || job.status === "done") return <CheckCircle className="w-5 h-5" />;
    return <Loader2 className="w-5 h-5 animate-spin" />;
  };

  const getStatusMessage = () => {
    if (job.status === "error") return `Error: ${job.error_message || "Algo salió mal"}`;
    if (job.status === "completed" || job.status === "done") return "✅ Video generado exitosamente";
    if (job.status === "processing") return job.metadata?.current_phase || "Procesando...";
    if (job.status === "queued") return "⏳ En cola...";
    return "Procesando...";
  };

  return (
    <div className="space-y-3">
      {/* Estado */}
      <div className={`flex items-center gap-2 ${getStatusColor()}`}>
        {getStatusIcon()}
        <span className="font-medium">{getStatusMessage()}</span>
      </div>

      {/* Barra de progreso */}
      {job.status === "processing" && (
        <div className="space-y-1">
          <Progress value={job.progress || 0} className="h-2" />
          <p className="text-xs text-gray-500 text-right">{job.progress || 0}%</p>
        </div>
      )}

      {/* Información adicional */}
      {job.status === "processing" && job.metadata?.video_model && (
        <p className="text-xs text-gray-400">
          Modelo: {job.metadata.video_model}
        </p>
      )}
    </div>
  );
}
```

### 4. Agregar Polling Correcto

Asegurarse de que el polling del estado del job se hace correctamente:

```typescript
useEffect(() => {
  if (!jobId || job?.status === "completed" || job?.status === "done") {
    return; // No hacer polling si no hay job o ya se completó
  }

  const pollInterval = setInterval(async () => {
    try {
      const response = await fetch(`https://api.genscenestudio.com/api/status?job_id=${jobId}`);
      const data = await response.json();
      
      setJob(data);
      
      // Detener polling si el job terminó (éxito o error)
      if (data.status === "completed" || data.status === "done" || data.status === "error") {
        clearInterval(pollInterval);
      }
    } catch (error) {
      console.error("Error polling job status:", error);
    }
  }, 2000); // Poll cada 2 segundos

  return () => clearInterval(pollInterval);
}, [jobId, job?.status]);
```

## Estados Válidos del Job:

- `queued`: Job en cola, esperando procesamiento
- `processing`: Job en progreso (mostrar current_phase)
- `completed` o `done`: Job completado exitosamente
- `error`: Job falló (mostrar error_message)

## Reglas Importantes:

1. **NUNCA mostrar "Error:" si `job.status !== "error"`**
2. **Usar `job.metadata.current_phase` solo para progreso, NO para errores**
3. **Mostrar `job.error_message` solo cuando `job.status === "error"`**
4. **Detener el polling cuando el job termine (completed/done/error)**
5. **Usar colores apropiados:**
   - Azul para "processing"
   - Verde para "completed/done"
   - Rojo solo para "error"

## Testing:

Después de implementar, verificar que:
1. ✅ No se muestra "Error:" cuando el job está en progreso
2. ✅ Se muestra correctamente "🧠 Dreaming up concept..." como progreso
3. ✅ Se muestra "✅ Video generado exitosamente" cuando termina
4. ✅ Solo se muestra error real cuando `job.status === "error"`
5. ✅ La barra de progreso se actualiza correctamente

---

¿Puedes implementar estos cambios para corregir el mensaje de error falso?
