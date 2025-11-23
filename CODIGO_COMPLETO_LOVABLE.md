# 📋 CÓDIGO COMPLETO PARA LOVABLE - GEN SCENE STUDIO

**Lista para copiar y pegar en Lovable cuando los pida**

---

## 📋 **PASO 1: VARIABLES DE ENTORNE (LOVABLE YA SUGIRIÓ)**

```
VITE_API_BASE_URL=http://94.72.113.216:8000
```

---

## 📋 **PASO 2: apiClient.ts**

```
// src/lib/apiClient.ts
import { apiUrl } from "@/lib/apiConfig";

// Identificador público opcional
const PUBLIC_API_TOKEN = process.env.VITE_API_TOKEN || "public-demo-token";

const defaultHeaders: HeadersInit = {
  "Content-Type": "application/json",
  "X-Client-Id": PUBLIC_API_TOKEN,
};

export const apiClient = {
  async get(path: string) {
    const response = await fetch(apiUrl(path), {
      method: "GET",
      headers: defaultHeaders,
    });

    if (!response.ok) {
      throw new Error(`GET ${path} failed with ${response.status}`);
    }

    return response.json();
  },

  async post(path: string, data: any) {
    const response = await fetch(apiUrl(path), {
      method: "POST",
      headers: defaultHeaders,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`POST ${path} failed with ${response.status}`);
    }

    return response.json();
  },
};

export const api = {
  health: () => apiClient.get("/health"),
  tts: (data: any) => apiClient.post("/api/tts", data),
  compose: (data: any) => apiClient.post("/api/compose", data),
  status: (jobId: string) => apiClient.get(`/api/status?job_id=${jobId}`),
  files: (jobId: string, filename: string) =>
    apiUrl(`/files/${jobId}/${filename}`),
};
```

---

## 📋 **PASO 3: useGenSceneAPI.ts**

```
// src/hooks/useGenSceneAPI.ts
import { useState, useCallback } from 'react';
import { api } from '@/lib/apiClient';

export const useGenSceneAPI = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateTTS = useCallback(async (
    jobId: string,
    text: string,
    voiceId: string = 'es_ES-carlfm-high'
  ) => {
    setLoading(true);
    setError(null);

    try {
      const result = await api.tts({
        job_id: jobId,
        text,
        voice_id: voiceId
      });
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error generating TTS');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getJobStatus = useCallback(async (jobId: string) => {
    try {
      return await api.status(jobId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error getting job status');
      throw err;
    }
  }, []);

  return { generateTTS, getJobStatus, loading, error };
};
```

---

## 📋 **PASO 4: Voz.tsx**

```
// src/components/Voz.tsx
import React, { useState, useEffect } from "react";
import { useGenSceneAPI } from "@/hooks/useGenSceneAPI";
import { api } from "@/lib/apiClient";
import { API_BASE_URL } from "@/lib/apiConfig";

export default function Voz() {
  const [text, setText] = useState(
    "Bienvenido a Gen Scene Studio - nuestro sistema está funcionando perfectamente"
  );
  const [audioUrl, setAudioUrl] = useState("");
  const [status, setStatus] = useState("");

  const { generateTTS, getJobStatus, loading, error } = useGenSceneAPI();

  const generateAudio = async () => {
    if (!text.trim()) {
      alert("Por favor, escribe un texto para generar audio");
      return;
    }

    const jobId = `voz-${Date.now()}`;
    setStatus("🎵 Iniciando generación de audio...");

    try {
      setStatus("⏳ Enviando solicitud a la API...");
      const result = await generateTTS(jobId, text);
      console.log("TTS Result:", result);

      setStatus("🔄 Procesando audio...");
      let jobStatus = await getJobStatus(jobId);

      while (
        jobStatus.status !== "completed" &&
        jobStatus.status !== "failed"
      ) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        jobStatus = await getJobStatus(jobId);
        console.log("Job Status:", jobStatus);
      }

      if (jobStatus.status === "completed") {
        const audioUrl = api.files(jobId, "tts.wav");
        setAudioUrl(audioUrl);
        setStatus("✅ Audio generado exitosamente");
        console.log("Audio URL:", audioUrl);
      } else {
        setStatus("❌ Error generando audio");
      }
    } catch (err) {
      console.error("Error:", err);
      setStatus(`❌ Error: ${error || "Unknown error"}`);
    }
  };

  useEffect(() => {
    const testConnection = async () => {
      try {
        const health = await api.health();
        console.log("✅ Conexión API exitosa:", health);
      } catch (err) {
        console.error("❌ Error de conexión:", err);
      }
    };
    testConnection();
  }, []);

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h2 className="text-3xl font-bold mb-6 text-center">🎤 Voz AI</h2>

      <div className="mb-6 p-4 bg-green-100 rounded-lg text-center">
        <p className="text-green-800">🟢 Backend VPS conectado</p>
        <p className="text-sm text-green-600">{API_BASE_URL}</p>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">
          Texto para generar audio:
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Escribe aquí el texto que quieres convertir en voz..."
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows={4}
        />
      </div>

      <button
        onClick={generateAudio}
        disabled={loading || !text.trim()}
        className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
      >
        {loading ? "⏳ Generando Audio..." : "🎵 Generar Audio"}
      </button>

      {status && (
        <div className="mt-4 p-3 bg-gray-100 rounded-lg text-center">
          <p className="text-sm">{status}</p>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-100 rounded-lg text-center">
          <p className="text-sm text-red-800">❌ {error}</p>
        </div>
      )}

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

## 🎯 **IMPORTANTE - CUANDO LOVABLE PIDO CADA PASO:**

### **Para PASO 2 (apiClient.ts):**
- Copia y pega el código exacto
- Asegúrate de que mantenga las importaciones correctas

### **Para PASO 3 (useGenSceneAPI.ts):**
- Pega el código completo del hook
- Verifica que las importaciones coincidan

### **Para PASO 4 (Voz.tsx):**
- Pega todo el componente completo
- Asegúrate de incluir las importaciones al principio

### **Para test final:**
- Pide a Lovable que haga preview
- Testea el componente Voz
- Genera tu primer audio real

---

## 🧪 **RESULTADO ESPERADO:**

✅ **Conexión API exitosa** en consola
✅ **Status verde** mostrando URL del backend
✅ **Botón funcional** para generar audio
✅ **Audio player** después de procesamiento
✅ **Descarga .wav** funcional

**¡Listo para implementar!** 🚀