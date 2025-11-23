# 🚀 INTEGRACIÓN INMEDIATA - GEN SCENE STUDIO

**Configuración para Lovable HOY MISMO**

---

## 🎯 **ESTADO ACTUAL CONFIRMADO**

### **✅ Backend 100% Funcional:**
- **Health Check:** `http://94.72.113.216:8000/health` → 200 OK ✅
- **TTS Endpoint:** Funciona perfectamente ✅
- **File Serving:** Descargas funcionando ✅
- **API Security:** API key validation OK ✅

### **❌ Cloudflare Temporalmente:**
- **Error 522:** Cloudflare no puede conectar con puerto 8000
- **Solución temporal:** Usar IP directa hasta arreglar Cloudflare

---

## 🔧 **CONFIGURACIÓN INMEDIATA PARA LOVABLE**

### **Paso 1: Variables de Entorno en Lovable**

En tu dashboard de Lovable:
```
Settings → Environment Variables
```

Agrega estas variables:
```bash
VITE_API_BASE_URL=http://94.72.113.216:8000
VITE_API_KEY=genscene_api_key_prod_2025_secure
VITE_API_TIMEOUT=30000
```

### **Paso 2: Código de Conexión**

Crea un archivo `src/config/api.ts` en Lovable:
```typescript
export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://94.72.113.216:8000',
  apiKey: import.meta.env.VITE_API_KEY || 'genscene_api_key_prod_2025_secure',
  timeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': import.meta.env.VITE_API_KEY || 'genscene_api_key_prod_2025_secure'
  }
};

// Endpoints
export const ENDPOINTS = {
  health: `${API_CONFIG.baseURL}/health`,
  tts: `${API_CONFIG.baseURL}/api/tts`,
  compose: `${API_CONFIG.baseURL}/api/compose`,
  status: (jobId: string) => `${API_CONFIG.baseURL}/api/status?job_id=${jobId}`,
  files: (jobId: string, filename: string) => `${API_CONFIG.baseURL}/files/${jobId}/${filename}`
};
```

### **Paso 3: Service API**

Crea `src/services/api.ts`:
```typescript
import { API_CONFIG, ENDPOINTS } from '../config/api';

class GenSceneAPI {
  async healthCheck() {
    const response = await fetch(ENDPOINTS.health);
    return response.json();
  }

  async generateTTS(jobId: string, text: string, voiceId: string = 'es_ES-carlfm-high') {
    const response = await fetch(ENDPOINTS.tts, {
      method: 'POST',
      headers: API_CONFIG.headers,
      body: JSON.stringify({
        job_id: jobId,
        text,
        voice_id: voiceId
      })
    });

    if (!response.ok) {
      throw new Error(`TTS Error: ${response.status}`);
    }

    return response.json();
  }

  async generateVideo(jobId: string, config: any) {
    const response = await fetch(ENDPOINTS.compose, {
      method: 'POST',
      headers: API_CONFIG.headers,
      body: JSON.stringify({
        job_id: jobId,
        ...config
      })
    });

    if (!response.ok) {
      throw new Error(`Compose Error: ${response.status}`);
    }

    return response.json();
  }

  async getJobStatus(jobId: string) {
    const response = await fetch(ENDPOINTS.status(jobId), {
      headers: {
        'X-API-Key': API_CONFIG.apiKey
      }
    });

    return response.json();
  }

  getFileUrl(jobId: string, filename: string): string {
    return ENDPOINTS.files(jobId, filename);
  }
}

export const genSceneAPI = new GenSceneAPI();
```

---

## 🎤 **EJEMPLO: COMPONENTE VOZ FUNCIONAL**

```typescript
// src/components/Voz.tsx
import React, { useState } from 'react';
import { genSceneAPI } from '../services/api';

export default function Voz() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState('');

  const generateAudio = async () => {
    if (!text.trim()) return;

    setLoading(true);
    const jobId = `voice-${Date.now()}`;

    try {
      // Generar TTS
      const result = await genSceneAPI.generateTTS(jobId, text);

      // Monitorear status
      let status = await genSceneAPI.getJobStatus(jobId);
      while (status.status !== 'completed' && status.status !== 'failed') {
        await new Promise(resolve => setTimeout(resolve, 1000));
        status = await genSceneAPI.getJobStatus(jobId);
      }

      if (status.status === 'completed') {
        const audioUrl = genSceneAPI.getFileUrl(jobId, 'tts.wav');
        setAudioUrl(audioUrl);
      }
    } catch (error) {
      console.error('Error:', error);
    }

    setLoading(false);
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">🎤 Voz AI</h2>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Escribe tu guion aquí..."
        className="w-full p-3 border rounded-lg mb-4"
        rows={4}
      />

      <button
        onClick={generateAudio}
        disabled={loading || !text.trim()}
        className="bg-blue-500 text-white px-6 py-3 rounded-lg disabled:opacity-50"
      >
        {loading ? 'Generando...' : '🎵 Generar Audio'}
      </button>

      {audioUrl && (
        <div className="mt-4">
          <h3 className="font-semibold mb-2">Audio generado:</h3>
          <audio controls className="w-full">
            <source src={audioUrl} type="audio/wav" />
          </audio>
          <a href={audioUrl} download className="block mt-2 text-blue-500">
            📥 Descargar audio
          </a>
        </div>
      )}
    </div>
  );
}
```

---

## 🧪 **TESTING INMEDIATO**

### **Test de Conexión:**
```javascript
// En cualquier componente de Lovable
import { genSceneAPI } from '../services/api';

useEffect(() => {
  const testConnection = async () => {
    try {
      const health = await genSceneAPI.healthCheck();
      console.log('✅ Gen Scene Studio API conectada:', health);
    } catch (error) {
      console.error('❌ Error de conexión:', error);
    }
  };

  testConnection();
}, []);
```

---

## 🎯 **RESULTADO ESPERADO**

Con esta configuración:

✅ **Tu frontend Lovable se conecta directamente** al backend VPS
✅ **Puedes generar audio** en tiempo real
✅ **Puedes generar videos** cuando implementes compose
✅ **Descargas funcionales** de archivos generados
✅ **Experiencia completa** para el usuario final

---

## 🚨 **NOTAS DE SECURITY (TEMPORAL)**

**Esta configuración es funcional pero temporal:**

- **API Key en frontend:** Solo para testing/testing rápido
- **HTTP sin HTTPS:** Solo para fase de desarrollo
- **IP directa:** Migraremos a dominio con Cloudflare

**Próximamente:** Fase 2 para producción con HTTPS + security ✅

---

## 📞 **SOPORTE**

Si algo no funciona:

1. **Verificar variables de entorno** en Lovable
2. **Check console errores** en browser dev tools
3. **Validar backend health:** `curl http://94.72.113.216:8000/health`
4. **Revisar API key:** `genscene_api_key_prod_2025_secure`

**¡Listo para empezar a generar videos!** 🚀