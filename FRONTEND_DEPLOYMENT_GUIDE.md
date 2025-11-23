# 🚀 Frontend Deployment Guide
**Gen Scene Studio - Production Deployment**

**Fecha:** 2025-11-23
**Estado:** Ready for Production
**Backend:** ✅ `https://api.genscenestudio.com`

---

## 📊 **Estado Actual del Frontend**

### **✅ Frontend Local (Development):**
- **URL**: `http://localhost:3000`
- **Status**: ✅ Fully functional
- **API Integration**: ✅ Connected to production backend
- **Components**: ✅ All features working in real mode

### **✅ Backend Production:**
- **URL**: `https://api.genscenestudio.com`
- **Status**: ✅ Fully operational via Cloudflare
- **Services**: ✅ TTS, Image Generation, Video Composition
- **Authentication**: ✅ API key protected

---

## 🌐 **Deployment Options for Frontend**

### **Option 1: Vercel (Recomendado)**
```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Login en Vercel
vercel login

# 3. Build para producción
cd /mnt/c/Users/user/proyectos_globales/proyecto_gen_scene_studio/frontend
npm run build

# 4. Deploy
vercel --prod
```

**Ventajas:**
- ✅ HTTPS automático
- ✅ CDN global
- ✅ Despliegue instantáneo
- ✅ Preview deployments
- ✅ Integración con GitHub

### **Option 2: Netlify**
```bash
# 1. Install Netlify CLI
npm i -g netlify-cli

# 2. Login en Netlify
netlify login

# 3. Build
npm run build

# 4. Deploy
netlify deploy --prod --dir=dist
```

### **Option 3: Cloudflare Pages**
```bash
# 1. Install Wrangler
npm i -g wrangler

# 2. Build
npm run build

# 3. Deploy a Cloudflare Pages
wrangler pages publish dist --project-name=genscene-frontend
```

### **Option 4: Firebase Hosting**
```bash
# 1. Install Firebase CLI
npm i -g firebase-tools

# 2. Login
firebase login

# 3. Inicializar proyecto
firebase init hosting

# 4. Deploy
firebase deploy --only hosting
```

---

## 🔧 **Configuración para Producción**

### **Variables de Entorno (.env.production):**
```bash
# Production API Configuration
VITE_API_URL=https://api.genscenestudio.com
VITE_API_KEY=genscene_api_key_prod_2025_secure

# Production timeouts
VITE_API_TIMEOUT=60000

# Debug disabled in production
VITE_DEBUG=false

# Performance optimizations
VITE_DEFAULT_POLLING_INTERVAL=2000
VITE_MAX_ACTIVE_JOBS=20
```

### **Build Commands:**
```bash
# Development build
npm run build

# Type checking
npm run type-check

# Linting
npm run lint

# Production preview
npm run preview
```

---

## 🎯 **Configuración del Dominio**

### **DNS Configuration:**
```bash
# Frontend Domain Options:
Option A: app.genscenestudio.com  → Frontend
Option B: genscenestudio.com      → Frontend
Option C: www.genscenestudio.com  → Frontend

# API ya configurado:
api.genscenestudio.com → Backend (Cloudflare)
```

### **SSL/TLS:**
- ✅ Automático en Vercel/Netlify
- ✅ Managed por Cloudflare
- ✅ HSTS enabled
- ✅ redirects HTTP → HTTPS

---

## 📱 **Testing en Producción**

### **Test Checklist:**
```bash
□ Health check API responde
□ TTS genera archivos WAV descargables
□ Image generation crea JPG/PNG reales
□ Video composition funciona con timeline
□ File downloads completan exitosamente
□ UI responsive en mobile/desktop
□ Rate limiting funciona correctamente
□ Error handling amigable para usuarios
□ Loading states claros
□ Progress bars precisos
```

### **Manual Testing Steps:**
1. **Storyboard Test**:
   - Generar 3 imágenes con prompts distintos
   - Verificar descarga individual y batch
   - Confirmar previews reales

2. **Voz Test**:
   - Convertir texto a voz
   - Reproducir audio en browser
   - Descargar archivo WAV

3. **Timeline Test**:
   - Crear timeline con 3 clips
   - Agregar texto y efectos
   - Generar video MP4 completo

---

## 🔒 **Security Considerations**

### **CORS Configuration (Backend):**
```typescript
// Already configured in production backend
allowed_origins: [
  "https://genscenestudio.com",
  "https://www.genscenestudio.com",
  "https://app.genscenestudio.com"
]
```

### **Rate Limiting:**
```bash
Production limits:
- 60 requests/minute por IP
- 10 concurrent jobs por usuario
- File size limits: 50MB
- Video duration: 5 minutos máximo
```

### **API Security:**
```bash
✅ API Key authentication
✅ HTTPS obligatorio
✅ Input validation
✅ File upload restrictions
✅ SQL injection protection
```

---

## 📊 **Performance Optimizations**

### **Frontend Optimizations:**
```bash
✅ React.memo() para componentes pesados
✅ useCallback() para event handlers
✅ Virtual scrolling para timelines largos
✅ Lazy loading para imágenes
✅ Code splitting por routes
✅ Pre-caching de API responses
```

### **Backend Optimizations:**
```bash
✅ Connection pooling SQLite
✅ FFmpeg optimizado para 1080x1920
✅ Image cache en KIE API
✅ Distributed rate limiting
✅ Async job processing
```

---

## 🚀 **Deploy Commands (Resumen)**

### **Vercel (Recomendado):**
```bash
cd frontend
npm run build
vercel --prod
# Result: https://genscene-frontend.vercel.app
```

### **Custom Domain (Vercel):**
```bash
vercel domains add genscenestudio.com
# DNS: CNAME -> cname.vercel-dns.com
```

### **Environment Variables in Vercel:**
```bash
vercel env add VITE_API_URL production
# Value: https://api.genscenestudio.com

vercel env add VITE_API_KEY production
# Value: genscene_api_key_prod_2025_secure
```

---

## 🎯 **Expected URLs Post-Deploy**

### **Final Architecture:**
```bash
Frontend: https://genscenestudio.com
API:     https://api.genscenestudio.com
Files:   https://api.genscenestudio.com/files/{job_id}/{filename}
Health:  https://api.genscenestudio.com/health
```

### **User Experience Flow:**
1. **User访问**: `https://genscenestudio.com`
2. **Register/Login** (future feature)
3. **Create Project** → Storyboard → Voz → Timeline
4. **Generate Content** → Real AI processing
5. **Download Results** → Professional MP4/WAV/JPG

---

## ⚡ **Performance Targets**

### **Post-Deploy Goals:**
```bash
Page Load:           <2s (Lighthouse)
Time to Interactive: <3s
API Response:        <500ms (p95)
Image Generation:    <30s
Video Composition:   <60s
Uptime:              99.9%
```

---

## 🔄 **CI/CD Pipeline (Opcional)**

### **GitHub Actions:**
```yaml
name: Deploy Frontend
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm run build
      - uses: vercel/action@v1
```

---

## 📝 **Post-Deploy Checklist**

### **Inmediatamente después del deploy:**
```bash
□ Frontend accesible en dominio
□ API calls funcionan con CORS
□ Todos los endpoints responden
□ File downloads funcionan
□ Mobile responsive OK
□ Error logging configurado
□ Analytics configurados
□ Performance monitoring activo
```

---

## 🎉 **¡Listo para Producción!**

### **Resumen Final:**
- ✅ **Backend**: Production-ready via Cloudflare
- ✅ **Frontend**: Development-ready, necesita deploy
- ✅ **API**: 100% funcional y probada
- ✅ **Security**: Enterprise-grade
- ✅ **Performance**: Optimizada
- ✅ **Scalability**: Lista para crecimiento

### **Próximo Paso:**
Elegir plataforma de deploy (Vercel recomendado) y deploy en producción.

---

**📅 Creado:** 2025-11-23
**🔄 Status:** Ready for Production Deploy
**🎯 Next:** Deploy frontend a Vercel/Netlify