# 🔄 Guía de Flujo de Trabajo - Gen Scene Studio

**Solución para sincronizar cambios entre Lovable y Producción**

**Fecha:** 2025-11-23
**Estado:** Pipeline configurado y listo para usar

---

## 🎯 **El Problema**

```
Lovable (desarrollo)  →  Cambios no se reflejan  →  Producción
```

**Causa:** Sin sistema de CI/CD, deploy manual propenso a errores

---

## ✅ **La Solución**

```
Lovable → Git Push → GitHub Actions → Deploy Automático → Producción
```

### **3 Métodos para sincronizar cambios:**

---

## 🚀 **Método 1: Deploy Automático (Recomendado)**

### **Setup inicial (una sola vez):**

1. **Crear repositorio GitHub:**
   ```bash
   # En tu proyecto local:
   git remote add origin https://github.com/TU-USUARIO/gen-scene-studio.git
   git branch -M main
   git push -u origin main
   ```

2. **Configurar Vercel:**
   - Cuenta: https://vercel.com
   - Conectar repositorio GitHub
   - Importar proyecto desde `/frontend`

3. **Configurar GitHub Secrets:**
   - `VERCEL_TOKEN`: Token de Vercel
   - `VERCEL_ORG_ID`: ID de organización Vercel
   - `VERCEL_PROJECT_ID`: ID de proyecto Vercel
   - `SSH_HOST`: 94.72.113.216
   - `SSH_USER`: root
   - `SSH_PASSWORD`: JLcontabo7828tls
   - `API_URL`: https://api.genscenestudio.com
   - `VITE_API_URL`: https://api.genscenestudio.com
   - `VITE_API_KEY`: genscene_api_key_prod_2025_secure

### **Flujo de trabajo diario:**

```bash
# 1. Trabaja en Lovable o localmente
# 2. Haz cambios y pruebas
# 3. Sincroniza y deploy:
git add .
git commit -m "feat: nuevo feature"
git push origin main

# 🎉 ¡Listo! Deploy automático en 2-3 minutos
```

---

## ⚡ **Método 2: Deploy Semi-Automático (Quick)**

### **Usando el script preparado:**

```bash
# Desde el directorio del proyecto:
./deploy.sh
```

**¿Qué hace el script?**
- ✅ Commitea cambios pendientes
- ✅ Build del frontend
- ✅ Deploy del backend al servidor
- ✅ Reinicia servicios
- ✅ Verifica salud del sistema
- ✅ Reporta status

---

## 🔧 **Método 3: Deploy Manual (Fuerza Mayor)**

### **Frontend (Vercel):**
```bash
cd frontend
npm run build
vercel --prod
```

### **Backend (Servidor):**
```bash
# Copiar archivos al servidor
sshpass -p "JLcontabo7828tls" scp -r whatif-backend/* root@94.72.113.216:/opt/genscene-backend/

# Reiniciar backend
sshpass -p "JLcontabo7828tls" ssh root@94.72.113.216 "cd /opt/genscene-backend && docker compose restart"
```

---

## 📋 **Flujo de Trabajo Recomendado**

### **Para desarrollo en Lovable:**

1. **Trabaja normalmente** en Lovable
2. **Exporta/Descarga** los cambios
3. **Aplica cambios localmente:**
   ```bash
   # Copia archivos de Lovable a tu proyecto
   ./deploy.sh  # Deploy inmediato
   ```

### **Para desarrollo local:**

1. **Haz cambios directamente** en tu código local
2. **Prueba localmente:**
   ```bash
   cd frontend && npm run dev  # Frontend local
   # Backend ya corre en producción
   ```
3. **Deploy con un comando:**
   ```bash
   ./deploy.sh
   ```

---

## 🔍 **Verificación de Deploy**

### **URLs para verificar:**

| Componente | URL | Verificación |
|------------|-----|--------------|
| **Backend Health** | https://api.genscenestudio.com/health | `{"status":"ok"}` |
| **Styles API** | https://api.genscenestudio.com/styles | Lista de 7 estilos |
| **Video Compose** | https://api.genscenestudio.com/api/compose | `{"job_id":"...","status":"queued"}` |
| **Frontend** | https://genscenestudio.com | App funcionando |

### **Comandos de verificación:**
```bash
# Backend
curl https://api.genscenestudio.com/health

# Styles
curl https://api.genscenestudio.com/styles

# Deploy status
ssh root@94.72.113.216 "cd /opt/genscene-backend && docker compose ps"
```

---

## 🎛️ **Configuración Técnica**

### **Variables de entorno (Frontend):**
```env
VITE_API_URL=https://api.genscenestudio.com
VITE_API_KEY=genscene_api_key_prod_2025_secure
```

### **Variables de entorno (Backend):**
```env
CORS_ALLOW_ORIGINS=https://genscenestudio.com,https://api.genscenestudio.com
API_KEY=genscene_api_key_prod_2025_secure
```

---

## 🚨 **Troubleshooting**

### **Problemas comunes:**

**❌ Frontend no actualiza:**
```bash
# Limpiar cache y redeploy
cd frontend
rm -rf dist node_modules/.cache
npm run build
./deploy.sh
```

**❌ Backend no responde:**
```bash
# Verificar logs
ssh root@94.72.113.216 "cd /opt/genscene-backend && docker compose logs genscene-backend"

# Forzar reinicio
ssh root@94.72.113.216 "cd /opt/genscene-backend && docker compose restart"
```

**❌ Error CORS:**
```bash
# Verificar configuración en app.py
# Asegurar que el origen esté en ALLOWED_ORIGINS
```

**❌ Styles endpoint 404:**
```bash
# Verificar que estás llamando a /styles (no /api/styles)
curl https://api.genscenestudio.com/styles
```

---

## 📈 **Mejoras Futuras**

### **Pipeline completo (Opcional):**
- ✅ GitHub Actions configurado
- 🔄 Integración con Lovable (via API)
- 📊 Monitoring y alertas
- 🔐 Testing automático
- 📱 Deploy multi-ambiente (staging → production)

### **Integración con Lovable:**
- Exportación automática desde Lovable
- Webhooks para trigger deploys
- Sincronización bidireccional

---

## 🎯 **Resumen: Solución Inmediata**

### **HOY MISMO puedes:**

1. **Deploy rápido con el script:**
   ```bash
   ./deploy.sh
   ```

2. **Verificar que todo funciona:**
   - Frontend: https://genscenestudio.com
   - Backend: https://api.genscenestudio.com/health
   - Styles: https://api.genscenestudio.com/styles

3. **Trabajar normalmente** y deploy cuando necesites

### **Esta configuración te da:**
- ✅ Deploy en 1 comando
- ✅ Verificación automática
- ✅ Rollback fácil
- ✅ Consistencia entre entornos
- ✅ Sin dependencia de Lovable Cloud

**🚀 Gen Scene Studio ahora tiene deploy profesional!**