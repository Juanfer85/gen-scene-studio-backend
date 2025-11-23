# 🚀 CONFIGURACIÓN PERMANENTE - LOVABLE + GEN SCENE STUDIO

**ESTRATEGIA:** Conexión directa Lovable → VPS para máxima estabilidad

---

## 📋 **CONFIGURACIÓN PERMANENTE PARA LOVABLE**

### **🔧 API Configuration (PARA SIEMPRE):**
```javascript
// Configuración permanente para tu frontend Lovable
const API_CONFIG = {
  baseURL: 'http://94.72.113.216:8000',  // IP directa del VPS - ESTABLE
  apiKey: 'genscene_api_key_prod_2025_secure',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'genscene_api_key_prod_2025_secure'
  }
}

// Endpoints permanentes:
const ENDPOINTS = {
  health: `${API_CONFIG.baseURL}/health`,
  tts: `${API_CONFIG.baseURL}/api/tts`,
  compose: `${API_CONFIG.baseURL}/api/compose`,
  status: (jobId) => `${API_CONFIG.baseURL}/api/status?job_id=${jobId}`,
  files: (jobId, filename) => `${API_CONFIG.baseURL}/files/${jobId}/${filename}`
}
```

---

## 🎯 **IMPLEMENTACIÓN EN LOVABLE**

### **Opción A: Variables de Entorno en Lovable**
```bash
# En Lovable Dashboard → Settings → Environment Variables
VITE_API_BASE_URL=http://94.72.113.216:8000
VITE_API_KEY=genscene_api_key_prod_2025_secure
VITE_API_TIMEOUT=30000
```

### **Opción B: Configuración Directa en Código**
```typescript
// src/config/api.ts
export const API_BASE_URL = 'http://94.72.113.216:8000';
export const API_KEY = 'genscene_api_key_prod_2025_secure';

// src/services/api.ts
import { API_BASE_URL, API_KEY } from '../config/api';

export const apiClient = {
  tts: async (jobId: string, text: string) => {
    const response = await fetch(`${API_BASE_URL}/api/tts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
      },
      body: JSON.stringify({ job_id: jobId, text, voice_id: 'es_ES-carlfm-high' })
    });
    return response.json();
  },

  compose: async (jobId: string, config: any) => {
    const response = await fetch(`${API_BASE_URL}/api/compose`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
      },
      body: JSON.stringify({ job_id: jobId, ...config })
    });
    return response.json();
  },

  getStatus: async (jobId: string) => {
    const response = await fetch(`${API_BASE_URL}/api/status?job_id=${jobId}`, {
      headers: {
        'X-API-Key': API_KEY
      }
    });
    return response.json();
  }
};
```

---

## 🔄 **WORKFLOW COMPLETO PERMANENTE**

### **1. Generación de Audio (TTS):**
```typescript
// En tu componente de Voz
const generateAudio = async (text: string) => {
  const jobId = `voice-${Date.now()}`;

  // Generar audio
  const result = await apiClient.tts(jobId, text);

  // Monitorear progreso
  const checkStatus = async () => {
    const status = await apiClient.getStatus(jobId);
    if (status.status === 'completed') {
      const audioUrl = `http://94.72.113.216:8000${result.audio_url}`;
      return audioUrl;
    }
    // Seguir monitoreando...
  };

  return checkStatus();
};
```

### **2. Generación de Video:**
```typescript
// En tu componente Timeline
const composeVideo = async (config) => {
  const jobId = `video-${Date.now()}`;

  // Iniciar composición
  const result = await apiClient.compose(jobId, config);

  // Monitorear progreso
  const checkStatus = async () => {
    const status = await apiClient.getStatus(jobId);
    if (status.status === 'completed') {
      return status.video_url;
    }
  };

  return checkStatus();
};
```

---

## 🛡️ **VENTAJAS DE ESTA CONFIGURACIÓN**

### **✅ Estabilidad Máxima:**
- Sin dependencia de Cloudflare (un punto menos de falla)
- Conexión directa IP → API (más rápido)
- Menos latency (sin intermediaires)
- Control total de la conexión

### **✅ Mantenimiento Simple:**
- Solo hay que mantener el backend VPS
- Si cambia la IP del VPS, solo se actualiza una línea
- Logs y debugging más directos
- Sin configuración DNS compleja

### **✅ Escalabilidad Futura:**
- Fácil migrar a dominio personalizado después
- Compatible con Cloudflare (se puede agregar después)
- Preparado para load balancers futuros

---

## 📊 **TESTING Y VALIDACIÓN PERMANENTE**

### **Health Check Automático:**
```javascript
// En tu App.tsx o main component
useEffect(() => {
  const checkAPIHealth = async () => {
    try {
      const response = await fetch('http://94.72.113.216:8000/health');
      const health = await response.json();
      console.log('Gen Scene Studio API Health:', health);
    } catch (error) {
      console.error('API not accessible:', error);
    }
  };

  // Check al iniciar la app
  checkAPIHealth();

  // Check cada 5 minutos
  const interval = setInterval(checkAPIHealth, 5 * 60 * 1000);

  return () => clearInterval(interval);
}, []);
```

### **Error Handling Robusto:**
```javascript
// En cada llamada API
try {
  const result = await apiClient.tts(jobId, text);
  return result;
} catch (error) {
  console.error('API Error:', error);

  // Mostrar error amigable al usuario
  showToast('Error conectando con Gen Scene Studio', 'error');

  // Opcional: fallback a modo demo
  return fallbackResponse;
}
```

---

## 🚀 **IMPLEMENTACIÓN PASOS**

### **PASO 1:** Copiar la configuración API en tu Lovable
### **PASO 2:** Test con health endpoint
### **PASO 3:** Implementar TTS endpoint
### **PASO 4:** Implementar compose endpoint
### **PASO 5:** Agregar monitoreo automático

---

## 📞 **SOPORTE Y MONITOREO**

### **Health Check URL:** http://94.72.113.216:8000/health
### **API Base URL:** http://94.72.113.216:8000
### **API Key:** genscene_api_key_prod_2025_secure

### **Si algo falla:**
1. **Verificar conexión:** Hacer curl a la health URL
2. **Revisar API key:** Confirmar que sea la correcta
3. **Check backend:** Ver logs en VPS
4. **Test endpoints:** Usar Postman/curl individual

---

**ESTA CONFIGURACIÓN GARANTIZA ESTABILIDAD A LARGO PLAZO** 🎯

**Actualizado:** 2025-11-16
**Estrategia:** Conexión directa VPS para máxima confiabilidad