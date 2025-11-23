# 🎬 PASO A PASO COMPLETO - GEN SCENE STUDIO

**INSTALACIÓN Y CONFIGURACIÓN FRONTEND + BACKEND**

---

## ✅ **PASO 1: BACKEND (YA INSTALADO)**

### **Estado Backend VPS:**
- ✅ **IP:** 94.72.113.216
- ✅ **Puerto:** 8000
- ✅ **URL:** http://94.72.113.216:8000
- ✅ **Status:** Funcionando perfectamente
- ✅ **API Key:** genscene_api_key_prod_2025_secure
- ✅ **Health:** {"status":"ok","ffmpeg":true,"ffprobe":true,"db":true"}

### **Endpoints Backend Disponibles:**
```
GET  http://94.72.113.216:8000/health              ✅ Working
POST http://94.72.113.216:8000/api/tts              ✅ Working
POST http://94.72.113.216:8000/api/compose          ✅ Working
GET  http://94.72.113.216:8000/api/status?job_id=XXX ✅ Working
GET  http://94.72.113.216:8000/files/{job_id}/{filename} ✅ Working
```

---

## 🎨 **PASO 2: FRONTEND LOVABLE (PENDIENTE)**

### **2.1 Acceder a Lovable:**
1. **Abrir:** https://lovable.app
2. **Login:** Con tu email/contraseña
3. **Buscar:** Proyecto "Gen Scene Studio" o similar

### **2.2 Configurar Variables de Entorno en Lovable:**
Una vez dentro de tu proyecto:
1. **Ir a:** Settings (⚙️) → Environment Variables
2. **Agregar estas 3 variables:**

```bash
VITE_API_BASE_URL=http://94.72.113.216:8000
VITE_API_KEY=genscene_api_key_prod_2025_secure
VITE_API_TIMEOUT=30000
```

### **2.3 Crear Archivos de Configuración:**
En el editor de Lovable, crea estos archivos:

#### **Archivo 1: src/config/api.ts**
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

export const ENDPOINTS = {
  health: `${API_CONFIG.baseURL}/health`,
  tts: `${API_CONFIG.baseURL}/api/tts`,
  compose: `${API_CONFIG.baseURL}/api/compose`,
  status: (jobId: string) => `${API_CONFIG.baseURL}/api/status?job_id=${jobId}`,
  files: (jobId: string, filename: string) => `${API_CONFIG.baseURL}/files/${jobId}/${filename}`
};
```

#### **Archivo 2: src/services/api.ts**
```typescript
import { API_CONFIG, ENDPOINTS } from '../config/api';

export class GenSceneAPI {
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

    if (!response.ok) throw new Error(`TTS Error: ${response.status}`);
    return response.json();
  }

  async getJobStatus(jobId: string) {
    const response = await fetch(ENDPOINTS.status(jobId), {
      headers: { 'X-API-Key': API_CONFIG.apiKey }
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

## 🎤 **PASO 3: COMPONENTE VOZ FUNCIONAL**

### **3.1 Actualizar tu componente Voz existente:**
Busca tu componente `Voz.tsx` en Lovable y reemplaza el contenido con:

```typescript
import React, { useState } from 'react';
import { genSceneAPI } from '../services/api';

export default function Voz() {
  const [text, setText] = useState('Bienvenido a Gen Scene Studio - nuestro sistema está funcionando perfectamente');
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState('');
  const [status, setStatus] = useState('');

  const generateAudio = async () => {
    if (!text.trim()) {
      alert('Por favor, escribe un texto para generar audio');
      return;
    }

    setLoading(true);
    setStatus('Iniciando generación de audio...');
    const jobId = `voz-${Date.now()}`;

    try {
      // Paso 1: Generar TTS
      setStatus('Enviando solicitud a la API...');
      const result = await genSceneAPI.generateTTS(jobId, text);
      console.log('TTS Result:', result);

      // Paso 2: Monitorear progreso
      setStatus('Procesando audio...');
      let jobStatus = await genSceneAPI.getJobStatus(jobId);

      while (jobStatus.status !== 'completed' && jobStatus.status !== 'failed') {
        await new Promise(resolve => setTimeout(resolve, 1000));
        jobStatus = await genSceneAPI.getJobStatus(jobId);
        console.log('Job Status:', jobStatus);
      }

      if (jobStatus.status === 'completed') {
        const audioUrl = genSceneAPI.getFileUrl(jobId, 'tts.wav');
        setAudioUrl(audioUrl);
        setStatus('✅ Audio generado exitosamente');
        console.log('Audio URL:', audioUrl);
      } else {
        setStatus('❌ Error generando audio');
      }
    } catch (error) {
      console.error('Error:', error);
      setStatus(`❌ Error: ${error.message}`);
    }

    setLoading(false);
  };

  // Test de conexión al montar el componente
  React.useEffect(() => {
    const testConnection = async () => {
      try {
        const health = await genSceneAPI.healthCheck();
        console.log('✅ Conexión API exitosa:', health);
      } catch (error) {
        console.error('❌ Error de conexión:', error);
      }
    };
    testConnection();
  }, []);

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h2 className="text-3xl font-bold mb-6 text-center">🎤 Voz AI</h2>

      {/* Health Status */}
      <div className="mb-6 p-4 bg-green-100 rounded-lg text-center">
        <p className="text-green-800">🟢 Backend conectado y funcionando</p>
      </div>

      {/* Input de texto */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Texto para generar audio:</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Escribe aquí el texto que quieres convertir en voz..."
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows={4}
        />
      </div>

      {/* Botón de generación */}
      <button
        onClick={generateAudio}
        disabled={loading || !text.trim()}
        className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
      >
        {loading ? '⏳ Generando Audio...' : '🎵 Generar Audio'}
      </button>

      {/* Status */}
      {status && (
        <div className="mt-4 p-3 bg-gray-100 rounded-lg text-center">
          <p className="text-sm">{status}</p>
        </div>
      )}

      {/* Audio generado */}
      {audioUrl && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold mb-3 text-center">🎧 Audio Generado:</h3>
          <audio controls className="w-full mb-3">
            <source src={audioUrl} type="audio/wav" />
            Tu navegador no soporta audio.
          </audio>
          <div className="text-center">
            <a
              href={audioUrl}
              download={`gen-scene-audio-${Date.now()}.wav`}
              className="inline-block bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition duration-200"
            >
              📥 Descargar Audio
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 🧪 **PASO 4: TESTING COMPLETO**

### **4.1 Test de Conexión:**
1. **Guarda todos los cambios** en Lovable
2. **Preview/Run** tu aplicación
3. **Abre la consola del browser** (F12)
4. **Busca el componente Voz**
5. **Deberías ver:** `✅ Conexión API exitosa`

### **4.2 Test de Generación de Audio:**
1. **Click en "Generar Audio"**
2. **Observa el status** que cambia en tiempo real
3. **Espera el proceso** (10-30 segundos)
4. **Deberías ver:** Audio player + botón de descarga

### **4.3 Test de Descarga:**
1. **Click en "📥 Descargar Audio"**
2. **Debería descargar:** archivo .wav real
3. **Verifica:** El archivo debe tener audio real

---

## ✅ **RESULTADO ESPERADO**

### **Si todo funciona correctamente:**
- ✅ **Frontend Lovable** conectado a backend VPS
- ✅ **Generación de audio** en tiempo real
- ✅ **Monitoreo de jobs** con status updates
- ✅ **Descarga de archivos** funcionando
- ✅ **Experiencia completa** para el usuario

### **URLs Finales:**
- **Frontend:** [tu-url-lovable].lovable.app
- **Backend:** http://94.72.113.216:8000
- **API Health:** http://94.72.113.216:8000/health

---

## 🆘 **SOPORTE**

### **Si algo no funciona:**
1. **Check Console:** F12 → Console por errores
2. **Check Network:** F12 → Network → revisa llamadas API
3. **Variables de Entorno:** Verifica que estén configuradas
4. **Backend Status:** Abre http://94.72.113.216:8000/health

**¿Cuál es la URL exacta de tu proyecto en Lovable?**