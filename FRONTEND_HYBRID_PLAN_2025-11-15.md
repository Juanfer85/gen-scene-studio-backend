# 📋 FRONTEND HÍBRIDO - PLAN COMPLETO
**Fecha:** 2025-11-15
**Proyecto:** WhatIf Video Generation App
**Estrategia:** Modo Mock + Real API Integration

---

## 🎯 **OBJETIVO PRINCIPAL**

Transformar el frontend Lovable de **Mock AI mode** a **Modo Híbrido** completo:
- ✅ **MANTENER** toda la funcionalidad existente intacta
- ✅ **AGREGAR** integración real con GenScene API
- ✅ **CREAR** sistema dual Mock/Real con toggle

---

## 📱 **FUNCIONALIDADES EXISTENTES A MANTENER (NO ELIMINAR NADA)**

### **✅ Pages con Mock AI (Completar con API real):**

#### **1. Storyboard.tsx**
- ✅ **MANTENER:** Exportación JSON existente
- ✅ **MANTENER:** Generación de curl commands
- ✅ **MANTENER:** UI de prompts y configuración
- ✅ **AGREGAR:** Llamada real a `/api/render-batch`
- ✅ **AGREGAR:** Previsualización en tiempo real
- ✅ **AGREGAR:** Descarga de imágenes generadas

#### **2. Timeline.tsx**
- ✅ **MANTENER:** Visual timeline actual
- ✅ **MANTENER:** Configuración de efectos Ken Burns
- ✅ **MANTENER:** Text overlays y posiciones
- ✅ **AGREGAR:** Composición real vía `/api/compose`
- ✅ **AGREGAR:** Video preview cuando complete
- ✅ **AGREGAR:** Download de video generado

#### **3. Voz.tsx**
- ✅ **MANTENER:** Editor de texto actual
- ✅ **MANTENER:** Configuración de voces y WPM
- ✅ **MANTENER:** Interface de texto completo
- ✅ **AGREGAR:** TTS real vía `/api/tts`
- ✅ **AGREGAR:** Audio player con generated speech
- ✅ **AGREGAR:** Download de archivos de audio

#### **4. Lote.tsx**
- ✅ **MANTENER:** Importación CSV existente
- ✅ **MANTENER:** Exportación JSON existente
- ✅ **MANTENER:** Configuración de batch processing
- ✅ **AGREGAR:** Procesamiento real vía `/api/render-batch`
- ✅ **AGREGAR:** Progress tracking por item
- ✅ **AGREGAR:** Results grid con download links

#### **5. Subtítulos.tsx**
- ✅ **MANTENER:** Generador SRT actual
- ✅ **MANTENER:** Timeline visual de subtítulos
- ✅ **MANTENER:** Configuración de tiempo
- ✅ **AGREGAR:** SRT real para videos generados
- ✅ **AGREGAR:** Preview con video real
- ✅ **AGREGAR:** Timing desde audio real

#### **6. Publicar.tsx**
- ✅ **MANTENER:** Configuración de redes sociales
- ✅ **MANTENER:** Mock variants existentes
- ✅ **MANTENER:** Previsualizaciones actuales
- ✅ **AGREGAR:** Generación real de variantes
- ✅ **AGREGAR:** Múltiples formatos (9:16, 1:1, 16:9)
- ✅ **AGREGAR:** Real preview y download por plataforma

---

### **✅ Pages de Gestión (Mantener y Mejorar):**

#### **Dashboard.tsx**
- ✅ **MANTENER:** Vista de episodios actual
- ✅ **MANTENER:** Navegación existente
- ✅ **AGREGAR:** Estadísticas de jobs en tiempo real
- ✅ **AGREGAR:** Indicadores de sistema

#### **Characters.tsx**
- ✅ **MANTENER:** Gestión de personajes intacta
- ✅ **AGREGAR:** Opcionalmente avatares AI-generados

#### **Styles.tsx**
- ✅ **MANTENER:** Configuración de estilos visual
- ✅ **AGREGAR:** Preview en tiempo real

#### **Episodes.tsx**
- ✅ **MANTENER:** Gestión de episodios
- ✅ **AGREGAR:** Integración con jobs generados
- ✅ **AGREGAR:** Links a resultados

#### **Jobs.tsx**
- ✅ **MANTENER:** Job listings existentes
- ✅ **AGREGAR:** Real-time monitoring dashboard
- ✅ **AGREGAR:** Auto-refresh cada 3 segundos
- ✅ **AGREGAR:** Status indicators (queued, running, done, error)
- ✅ **AGREGAR:** Download de resultados reales

---

## 🔧 **IMPLEMENTACIÓN ESTRATÉGICA MODO HÍBRIDO**

### **Para cada página, implementar sistema dual:**

#### **1. Mock Mode (Existente - MANTENER INTACTO):**
- ✅ Toda funcionalidad actual preservada
- ✅ Exportación JSON/cURL existente
- ✅ UI y configuraciones actuales
- ✅ No cambiar NADA del modo actual

#### **2. Real Mode (Nuevo - AGREGAR):**
- ✅ Llamadas API reales a backend
- ✅ Previsualización de resultados generados
- ✅ Download de archivos reales
- ✅ Real-time job monitoring

#### **3. Toggle entre modos:**
- ✅ Switch "Mock Mode / Real Mode" visible
- ✅ Compatibilidad total mantenida
- ✅ Cambio instantáneo sin perder datos

---

## 🛠️ **REQUISITOS TÉCNICOS**

### **API Integration:**
- **Base URL:** `http://localhost:8000`
- **API Key:** `X41R3R3GCt879dWdP169HNWfwCM20+Nx0N7kvReXTA8=`
- **Headers:** `X-API-Key` + `Content-Type: application/json`

### **Endpoints Disponibles:**
- ✅ `POST /api/tts` → Text-to-Speech
- ✅ `POST /api/compose` → Video Composition
- ✅ `GET /api/status?job_id=XXX` → Job Status
- ✅ `GET /api/compose-result?job_id=XXX` → Video Result
- ✅ `GET /files/{job_id}/{filename}` → Download Files

### **Componentes UI a Agregar:**
- ✅ **Toggle Switch** para Mock/Real mode
- ✅ **Progress Bars** para operaciones largas
- ✅ **Status Indicators** (queued, running, done, error)
- ✅ **Download Buttons** para contenido generado
- ✅ **Refresh Buttons** para actualizaciones en tiempo real

### **State Management:**
- ✅ React hooks para estado local
- ✅ Store de job IDs para tracking
- ✅ Separación Mock vs Real data
- ✅ localStorage para persistencia

### **Error Handling:**
- ✅ Mensajes user-friendly
- ✅ Retry buttons para operaciones fallidas
- ✅ Graceful fallback a Mock mode
- ✅ Connection status indicators

---

## 🎨 **REQUISITOS DE DISEÑO**

### **UI/UX Principles:**
- ✅ Mantener diseño actual intacto
- ✅ Agregar indicadores visuales Mock vs Real
- ✅ Estilizado consistente para nuevos componentes
- ✅ Responsive design en todos los dispositivos
- ✅ Loading states y progress animations

### **Visual Indicators:**
- **Mock Mode:** Icono 🎭 o etiqueta gris
- **Real Mode:** Icono ⚡ o etiqueta verde
- **Status Colors:**
  - Queued: Gris
  - Running: Azul
  - Done: Verde
  - Error: Rojo

---

## 📊 **EJEMPLOS DE TRANSFORMACIÓN**

### **Storyboard.tsx - ANTES (Solo Mock):**
```typescript
// Solo existe esto:
const generateCurl = () => { /* generate curl command */ }
const exportJSON = () => { /* export mock data */ }
```

### **Storyboard.tsx - DESPUÉS (Modo Híbrido):**
```typescript
// MANTENER existente:
const generateCurl = () => { /* generate curl command */ }
const exportJSON = () => { /* export mock data */ }

// AGREGAR nuevo:
const [isRealMode, setIsRealMode] = useState(false)
const generateRealImages = async () => { /* call /api/render-batch */ }
const monitorJob = async (jobId) => { /* call /api/status */ }
```

---

## 🚀 **PLAN DE IMPLEMENTACIÓN**

### **Fase 1: Configuración Base**
- ✅ Variables de entorno seguras
- ✅ API client setup
- ✅ Toggle component universal

### **Fase 2: Pages Principales**
- ✅ Storyboard.tsx → Mock + Real
- ✅ Timeline.tsx → Mock + Real
- ✅ Voz.tsx → Mock + Real

### **Fase 3: Pages Adicionales**
- ✅ Lote.tsx → Mock + Real
- ✅ Subtítulos.tsx → Mock + Real
- ✅ Publicar.tsx → Mock + Real

### **Fase 4: Dashboard y Monitoring**
- ✅ Jobs.tsx → Real-time dashboard
- ✅ Dashboard.tsx → Enhanced con stats
- ✅ Global job monitoring

---

## 🎯 **MÉTRICAS DE ÉXITO**

### **Funcionalidad:**
- ✅ 100% de funcionalidad mock existente preservada
- ✅ 100% de endpoints API integrados
- ✅ Toggle instantáneo entre modos
- ✅ Sin pérdida de datos al cambiar modos

### **Performance:**
- ✅ Mock mode: Sin latencia (actual)
- ✅ Real mode: Con job monitoring
- ✅ Estado persistente en localStorage
- ✅ Auto-refresh configurable

### **UX:**
- ✅ Feedback visual claro en cada operación
- ✅ Progress indicators en tiempo real
- ✅ Error handling amigable
- ✅ Download functionality intuitiva

---

## 📝 **NOTAS IMPORTANTES**

### **Reglas de Oro:**
1. **NO ELIMINAR** ninguna funcionalidad existente
2. **NO CAMBIAR** el diseño actual del modo mock
3. **SIEMPRE AGREGAR** encima, nunca reemplazar
4. **MANTENER** compatibilidad backward total
5. **ASEGURAR** que ambos modos funcionen independientemente

### **Testing Strategy:**
- ✅ Test cada página en Mock mode (debe funcionar igual)
- ✅ Test cada página en Real mode (nueva funcionalidad)
- ✅ Test toggle switching (no pérdida de datos)
- ✅ Test error handling y fallbacks
- ✅ Test real API calls con backend running

---

## 🎉 **RESULTADO FINAL ESPERADO**

Una aplicación **completamente híbrida** que ofrece:

### **Para Usuarios Mock:**
- ✅ Toda la funcionalidad actual sin cambios
- ✅ Exportación JSON/cURL como antes
- ✅ Mismo flujo de trabajo conocido

### **Para Usuarios Reales:**
- ✅ Generación real de contenido
- ✅ Previsualización en tiempo real
- ✅ Download de archivos reales
- ✅ Job tracking automático

### **Para la Aplicación:**
- ✅ Flexibilidad máxima para usuarios
- ✅ MVP funcional + Producción ready
- ✅ Compatibilidad total
- ✅ Escalabilidad futura

---

**📅 Documento creado:** 2025-11-15
**🔄 Última actualización:** 2025-11-15
**📌 Estado:** Ready for Implementation