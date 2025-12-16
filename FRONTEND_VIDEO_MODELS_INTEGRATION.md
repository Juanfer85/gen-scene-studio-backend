# 🎬 Guía de Integración: Selección de Modelos de Video

Esta guía explica cómo integrar el sistema híbrido de selección de modelos de video en el frontend de Gen Scene Studio.

## 📋 Resumen del Sistema

El sistema utiliza un **enfoque híbrido**:
1. **Por defecto**: El modelo se selecciona automáticamente según el `style_key`
2. **Override**: El usuario puede elegir manualmente un modelo específico

---

## 🔧 Archivos Creados/Modificados

### Backend
- `backend/src/worker/enterprise_manager.py` - Lógica de mapeo estilo→modelo
- `backend/src/main.py` - Nuevos endpoints de API

### Frontend
- `frontend/src/types/videoModels.ts` - Tipos TypeScript
- `frontend/src/components/VideoModelSelector.tsx` - Componente de selección
- `frontend/src/services/api.ts` - Métodos de API actualizados

---

## 🚀 Cómo Usar el Componente VideoModelSelector

### Importación
```tsx
import { VideoModelSelector } from '@/components/VideoModelSelector';
```

### Uso Básico
```tsx
const [selectedModel, setSelectedModel] = useState<string | null>(null);
const [styleKey, setStyleKey] = useState('cinematic_realism');

<VideoModelSelector
  styleKey={styleKey}           // Estilo actual (para recomendación)
  value={selectedModel}         // null = automático
  onChange={setSelectedModel}   // Callback cuando cambia
  videoDuration={5}             // Para calcular créditos
/>
```

### Propiedades
| Prop | Tipo | Default | Descripción |
|------|------|---------|-------------|
| `styleKey` | `string` | `'default'` | Estilo seleccionado para auto-selección |
| `value` | `string \| null` | - | Modelo seleccionado (null = auto) |
| `onChange` | `(model: string \| null) => void` | - | Callback cuando cambia |
| `videoDuration` | `number` | `5` | Duración del video en segundos |
| `disabled` | `boolean` | `false` | Si está deshabilitado |
| `showAutoOption` | `boolean` | `true` | Mostrar opción "Automático" |

---

## 📡 Nuevos Endpoints de API

### `GET /api/video-models`
Lista todos los modelos de video disponibles.

**Respuesta:**
```json
{
  "models": [
    {
      "id": "runway-gen3",
      "name": "Runway Gen-3",
      "tier": "high",
      "credits_5s": 200,
      "max_duration": 10,
      "features": ["text-to-video", "image-to-video", "video-extension"],
      "description": "Balance óptimo calidad/precio",
      "recommended_for": ["cinematic_realism", "cinematic", "documentary"]
    }
    // ... más modelos
  ],
  "total": 7,
  "default_model": "runway-gen3"
}
```

### `GET /api/style-model-mapping`
Obtiene el mapeo de estilos a modelos.

**Respuesta:**
```json
{
  "mapping": {
    "cinematic_realism": "runway-gen3",
    "anime_style": "kling/v2-1-pro",
    "fantasy_epic": "sora-2-pro-text-to-video"
    // ...
  },
  "available_styles": ["cinematic_realism", "anime_style", ...],
  "note": "When video_model is not specified, the model is auto-selected based on style_key"
}
```

### `GET /api/recommended-model/{style_key}`
Obtiene el modelo recomendado para un estilo específico.

**Ejemplo:** `GET /api/recommended-model/cinematic_realism`

**Respuesta:**
```json
{
  "style_key": "cinematic_realism",
  "recommended_model": "runway-gen3",
  "model_info": {
    "id": "runway-gen3",
    "name": "Runway Gen-3",
    "tier": "high",
    "credits_5s": 200,
    "max_duration": 10,
    "features": ["text-to-video", "image-to-video", "video-extension"],
    "description": "Balance óptimo calidad/precio"
  },
  "can_override": true,
  "available_models": ["runway-gen3", "veo3", "sora-2-pro-text-to-video", ...]
}
```

---

## 📤 Enviar Jobs con Modelo Específico

### Usando apiService.quickCreateWithModel()

```typescript
// Auto-selección basada en estilo (recomendado para la mayoría de usuarios)
await apiService.quickCreateWithModel({
  idea_text: "Un dragón volando sobre montañas",
  duration: "30s",
  style_key: "fantasy_epic",
  auto_create_universe: true,
  // video_model omitido = auto-selección
});

// Selección manual de modelo (para usuarios avanzados)
await apiService.quickCreateWithModel({
  idea_text: "Un dragón volando sobre montañas",
  duration: "30s",
  style_key: "fantasy_epic",
  auto_create_universe: true,
  video_model: "veo3",  // Override manual
  video_duration: 10,
  video_quality: "1080p",
  aspect_ratio: "16:9"
});
```

---

## 🎨 Mapeo Estilo → Modelo

| Estilo | Modelo por Defecto | Tier | Créditos/5s |
|--------|-------------------|------|-------------|
| `cinematic_realism` | Runway Gen-3 | High | 200 |
| `realistic` / `photorealistic` | Google Veo 3.1 | Premium | 350 |
| `anime_style` / `anime` | Kling v2.1 Pro | High | 250 |
| `fantasy_epic` / `fantasy` | OpenAI Sora 2 Pro | Premium | 400 |
| `minimalist` / `simple` | Wan Turbo | Economic | 120 |
| `social_media` / `tiktok` | Bytedance v1 | Economic | 150 |
| `artistic` | Hailuo I2V | Economic | 180 |

---

## 📊 Modelos Disponibles

### 👑 Premium
| Modelo | Créditos/5s | Duración Máx | Ideal Para |
|--------|-------------|--------------|------------|
| Google Veo 3.1 | 350 | 8s | Máxima calidad |
| OpenAI Sora 2 Pro | 400 | 20s | Narrativa compleja |

### ⚡ Alta Calidad
| Modelo | Créditos/5s | Duración Máx | Ideal Para |
|--------|-------------|--------------|------------|
| Runway Gen-3 | 200 | 10s | Balance calidad/precio |
| Kling v2.1 Pro | 250 | 10s | Control creativo |

### 💰 Económico
| Modelo | Créditos/5s | Duración Máx | Ideal Para |
|--------|-------------|--------------|------------|
| Wan Turbo | 120 | 5s | Más económico |
| Bytedance v1 | 150 | 5s | Social media |
| Hailuo I2V | 180 | 6s | Estilos artísticos |

---

## 🔄 Ejemplo de Integración Completa

```tsx
import { useState, useEffect } from 'react';
import { VideoModelSelector } from '@/components/VideoModelSelector';
import { VideoStyleSelector } from '@/components/VideoStyleSelector';
import { apiService } from '@/services/api';

function VideoCreator() {
  const [styleKey, setStyleKey] = useState('cinematic_realism');
  const [videoModel, setVideoModel] = useState<string | null>(null);
  const [ideaText, setIdeaText] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreate = async () => {
    setIsCreating(true);
    try {
      const result = await apiService.quickCreateWithModel({
        idea_text: ideaText,
        duration: '30s',
        style_key: styleKey,
        auto_create_universe: true,
        video_model: videoModel,  // null = auto
      });
      console.log('Job created:', result.job_id);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label>Idea del video</label>
        <textarea 
          value={ideaText} 
          onChange={(e) => setIdeaText(e.target.value)}
          placeholder="Describe tu video..."
        />
      </div>

      <VideoStyleSelector
        value={styleKey}
        onChange={setStyleKey}
      />

      <VideoModelSelector
        styleKey={styleKey}
        value={videoModel}
        onChange={setVideoModel}
        videoDuration={5}
      />

      <button 
        onClick={handleCreate}
        disabled={isCreating || !ideaText}
      >
        {isCreating ? 'Creando...' : 'Crear Video'}
      </button>
    </div>
  );
}
```

---

## ✅ Checklist de Integración

- [ ] Importar `VideoModelSelector` en el componente de creación de video
- [ ] Agregar estado para `videoModel` (inicializado como `null`)
- [ ] Conectar el estilo actual al prop `styleKey`
- [ ] Usar `apiService.quickCreateWithModel()` para enviar jobs
- [ ] Mostrar créditos estimados al usuario (opcional)
- [ ] Probar con diferentes estilos para verificar auto-selección

---

## 🐛 Troubleshooting

### El modelo no se auto-selecciona
- Verifica que `video_model` sea `null` o no esté en el payload
- Asegúrate que el `style_key` exista en el mapeo

### Error de créditos insuficientes
- Cambia a un modelo de tier más económico
- Reduce la duración del video

### Modelo no disponible
- Verifica la lista de modelos con `GET /api/video-models`
- Algunos modelos pueden tener limitaciones de duración

---

*Última actualización: 16 de Diciembre de 2025*
