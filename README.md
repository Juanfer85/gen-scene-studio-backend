# GenScene Frontend

Frontend completo para la plataforma GenScene Studio con integración total a la API backend.

## Características

### 🎤 Voz (Text-to-Speech)
- Convierte texto a audio de alta calidad
- Múltiples voces y configuraciones
- Reproducción y descarga de audio
- Control de velocidad (WPM)

### 🎬 Timeline de Video
- Editor visual de videos
- Composición de imágenes y audio
- Efectos Ken Burns
- Textos overlay con posiciones personalizables
- Límite de duración de 59 segundos

### 🎨 Storyboard con IA
- Generación de imágenes con prompts de texto
- Soporte para múltiples modelos (Kolors, Stable Diffusion, DALL-E)
- Control de calidad (draft/upscale)
- Generación por lotes
- Previsualización y descarga de resultados

### 📦 Procesamiento por Lotes
- Importación de datos desde CSV
- Procesamiento masivo de imágenes
- Monitoreo en tiempo real
- Exportación de resultados

### 📊 Monitor de Trabajos
- Panel centralizado de todos los trabajos
- Auto-refresh configurable
- Filtros por estado y tipo
- Visualización de progreso

### ⚙️ Nuevo Trabajo Automatizado
- Plantillas predefinidas
- Flujos de trabajo personalizados
- Ejecución secuencial de pasos
- Compartición de datos entre pasos

## Instalación

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd proyecto_videos_what_if
```

2. Instalar dependencias:
```bash
npm install
```

3. Configurar variables de entorno:
```bash
cp .env.local.example .env.local
```

Editar `.env.local` con tu configuración:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=tu_api_key_aqui
```

4. Iniciar el servidor de desarrollo:
```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`

## Arquitectura

### Estructura de Archivos

```
src/
├── components/
│   └── ui/               # Componentes de UI reutilizables
├── hooks/                # Hooks personalizados (useApiCall, usePolling)
├── lib/                  # Utilidades y cliente API
├── pages/                # Páginas de la aplicación
│   ├── Voz.tsx          # Generador de voz
│   ├── Timeline.tsx     # Editor de timeline
│   ├── Storyboard.tsx   # Generador de storyboard
│   ├── Lote.tsx         # Procesamiento por lotes
│   ├── Jobs.tsx         # Monitor de trabajos
│   ├── NewJob.tsx       # Nuevo trabajo automatizado
│   └── index.tsx        # Página principal
├── styles/               # Estilos globales
└── types/                # Definiciones de TypeScript
```

### Integración con la API

El frontend se integra completamente con los endpoints del backend:

- **POST /api/tts** → Text-to-Speech
- **POST /api/compose** → Video composition
- **GET /api/status?job_id=XXX** → Job status
- **GET /api/compose-result?job_id=XXX** → Video result
- **POST /api/render-batch** → Batch image generation
- **GET /files/{job_id}/{filename}** → Download files

### Características Técnicas

- **React 18** con TypeScript
- **Next.js 14** para routing y SSR
- **Tailwind CSS** para estilos
- **Lucide React** para iconos
- **Axios** para llamadas API con retry automático
- **Polling inteligente** para actualizaciones en tiempo real
- **LocalStorage** para persistencia de datos
- **Manejo de errores** robusto con feedback visual
- **Indicadores de carga** en todas las operaciones

## Uso

### 1. Voz (TTS)
1. Ingresa el texto a convertir
2. Configura voz opcional y velocidad
3. Haz clic en "Generar Voz"
4. Reproduce o descarga el audio

### 2. Timeline
1. Agrega elementos a la timeline
2. Configura URL, duración y efectos
3. Agrega audio y texto SRT opcional
4. Compose el video

### 3. Storyboard
1. Crea prompts para cada escena
2. Configura calidad y semillas
3. Genera el lote de imágenes
4. Descarga los resultados

### 4. Lotes
1. Crea un nuevo lote
2. Importa datos CSV o agrega manualmente
3. Configura modelo y aspect ratio
4. Inicia el procesamiento

### 5. Jobs
1. Visualiza todos los trabajos activos
2. Filtra por estado o tipo
3. Activa auto-refresh
4. Descarga resultados

### 6. Nuevo Job
1. Selecciona una plantilla o crea personalizada
2. Configura los pasos del flujo
3. Ejecuta el trabajo automatizado
4. Monitorea el progreso

## Variables de Entorno

- `NEXT_PUBLIC_API_URL`: URL del backend API
- `NEXT_PUBLIC_API_KEY`: Clave API para autenticación
- `NODE_ENV`: Entorno (development/production)

## Dependencias Principales

- **next**: 14.0.0
- **react**: ^18.2.0
- **typescript**: ^5.2.0
- **axios**: ^1.6.0
- **tailwindcss**: ^3.3.0
- **lucide-react**: ^0.292.0

## Desarrollo

### Scripts Disponibles

- `npm run dev`: Servidor de desarrollo
- `npm run build`: Build para producción
- `npm run start`: Servidor de producción
- `npm run lint`: Linter de código

### Buenas Prácticas

1. **Tipado estricto**: Todo el código está tipado con TypeScript
2. **Manejo de errores**: Todas las llamadas API tienen manejo de errores
3. **Feedback visual**: Indicadores de carga y progreso
4. **Responsive design**: Adaptable a diferentes tamaños de pantalla
5. **Accessibility**: Estructura semántica y navegación por teclado

## Despliegue

Para desplegar en producción:

1. Build del proyecto:
```bash
npm run build
```

2. Variables de entorno de producción:
```
NEXT_PUBLIC_API_URL=https://tu-backend.com
NEXT_PUBLIC_API_KEY=tu-production-key
```

3. Start del servidor:
```bash
npm start
```

## Contribuciones

1. Fork del repositorio
2. Crear rama de características
3. Commit con cambios descriptivos
4. Pull request al main

## Licencia

MIT License - ver archivo LICENSE para detalles