# 🌐 Guía Completa - Configurar DNS Cloudflare para Gen Scene Studio

**VPS IP:** 94.72.113.216
**Dominio:** genscenestudio.com
**Backend Status:** ✅ Ready for Cloudflare

---

## 🔧 **PASO A PASO - CONFIGURACIÓN DNS COMPLETA**

### **1. ACCESO A CLOUDFLARE**

#### **1.1 Login:**
1. Ve a [https://cloudflare.com](https://cloudflare.com)
2. Haz clic en "**Log in**" (esquina superior derecha)
3. Ingresa tu email y contraseña
4. Haz clic en "**Log in**"

#### **1.2 Seleccionar Dominio:**
- En tu dashboard verás una lista de dominios
- Busca: `genscenestudio.com`
- Haz clic sobre el nombre del dominio

---

### **2. NAVEGACIÓN A DNS RECORDS**

#### **2.1 Menú Izquierdo:**
```
🏠 Overview
📊 Analytics & Logs
💰 Billing
🔧 DNS  ← HACER CLIC AQUÍ
   ↳ DNS Management ← ESTA PÁGINA
   ↳ Custom DNS
🛡️ Security
⚡ Caching
🌐 Rules
🔒 SSL/TLS ← LUEGO VAMOS ACÁ
```

#### **2.2 Vista DNS Records:**
Verás algo como:
```
DNS Management                     [Add record] 🔘
┌─────────────────────────────────────────────┐
│ Type  Name    Content            Proxy       │
│ (Tus registros existentes aquí)             │
└─────────────────────────────────────────────┘
```

---

### **3. AÑADIR LOS 3 REGISTROS DNS A**

#### **3.1 Registro 1 - Dominio Principal (@):**
1. Haz clic en "**[Add record]**"
2. Configura así:
   ```
   ┌─────────────────────────────────┐
   │ Add a DNS record                │
   │                                 │
   │ Type:           [A ▼]           │
   │ Name:           [@]             │
   │ IPv4 address:   [94.72.113.216] │
   │ Proxy status:   [☁️ Proxied]    │
   │ TTL:            Auto            │
   │                                 │
   │              [Save] [Cancel]    │
   └─────────────────────────────────┘
   ```
3. Haz clic en "**Save**"

#### **3.2 Registro 2 - Subdominio WWW:**
1. Haz clic en "**[Add record]**" otra vez
2. Configura así:
   ```
   ┌─────────────────────────────────┐
   │ Add a DNS record                │
   │                                 │
   │ Type:           [A ▼]           │
   │ Name:           [www]           │
   │ IPv4 address:   [94.72.113.216] │
   │ Proxy status:   [☁️ Proxied]    │
   │ TTL:            Auto            │
   │                                 │
   │              [Save] [Cancel]    │
   └─────────────────────────────────┘
   ```
3. Haz clic en "**Save**"

#### **3.3 Registro 3 - Subdominio API:**
1. Haz clic en "**[Add record]**" otra vez
2. Configura así:
   ```
   ┌─────────────────────────────────┐
   │ Add a DNS record                │
   │                                 │
   │ Type:           [A ▼]           │
   │ Name:           [api]           │
   │ IPv4 address:   [94.72.113.216] │
   │ Proxy status:   [☁️ Proxied]    │
   │ TTL:            Auto            │
   │                                 │
   │              [Save] [Cancel]    │
   └─────────────────────────────────┘
   ```
3. Haz clic en "**Save**"

#### **3.4 Vista Final - DNS Completado:**
Deberías ver esto:
```
DNS Management                     [Add record] 🔘
┌────────────────────────────────────────────────────┐
│ Type  Name    Content               Proxy         │
│ A     @      94.72.113.216         ☁️ Proxied    │
│ A     www    94.72.113.216         ☁️ Proxied    │
│ A     api    94.72.113.216         ☁️ Proxied    │
│ (Tus otros registros existentes)                 │
└────────────────────────────────────────────────────┘
```

---

### **4. CONFIGURACIÓN SSL/TLS**

#### **4.1 Navegar a SSL/TLS:**
- En el menú izquierdo, haz clic en "**SSL/TLS**"
- Luego en "**Overview**"

#### **4.2 Configurar Modo de Encriptación:**
Verás esto:
```
┌─────────────────────────────────┐
│ Choose SSL/TLS encryption mode  │
│                                 │
│ ○ Off                           │
│ ○ Flexible                      │
│ ○ Full                          │
│ ● Full (strict) ← SELECCIONAR   │
│                                 │
│  [Install Certificate]           │
└─────────────────────────────────┘
```

1. Selecciona "**Full (strict)**"
2. Haz clic en "**Install Certificate**"

#### **4.3 Configuración Adicional SSL/TLS:**
Ve a **SSL/TLS → Edge Certificates** y activa:
```
☑️ Always Use HTTPS
☑️ HTTP Strict Transport Security (HSTS)
☑️ Minimum TLS Version: 1.2
```

---

### **5. VERIFICACIÓN Y ESPERA**

#### **5.1 Tiempo de Propagación:**
- **DNS Propagation:** 5-15 minutos generalmente
- **SSL Certificate:** 5-10 minutos
- **Global CDN:** 10-15 minutos

#### **5.2 Verificación (paso opcional):**
Puedes verificar con estos comandos desde tu terminal local:
```bash
# Ver DNS
dig genscenestudio.com A
nslookup genscenestudio.com

# Ver SSL (después de 5 minutos)
curl -I https://genscenestudio.com/health
```

---

### **6. URLs FINALES DE PRODUCCIÓN**

Una vez completado, estas URLs estarán disponibles:

```
✅ API Principal: https://genscenestudio.com
✅ Subdominio:    https://www.genscenestudio.com
✅ API Endpoint:  https://api.genscenestudio.com
✅ Health Check:  https://genscenestudio.com/health
✅ TTS API:       https://genscenestudio.com/api/tts
✅ Compose API:   https://genscenestudio.com/api/compose
```

---

## 🎯 **ENDPOINTS QUE USARÁ EL FRONTEND**

### **Configuración para Lovable/Frontend:**
```javascript
API_BASE_URL: "https://genscenestudio.com"
API_KEY: "genscene_api_key_prod_2025_secure"

// Endpoints disponibles:
GET  https://genscenestudio.com/health
POST https://genscenestudio.com/api/tts
POST https://genscenestudio.com/api/compose
GET  https://genscenestudio.com/api/status?job_id=XXXX
GET  https://genscenestudio.com/files/{job_id}/{filename}
```

---

## ⚠️ **NOTAS IMPORTANTES**

### **Sobre Proxy Status (☁️ Proxied):**
- **☁️ Proxied (Naranja):** Activa Cloudflare CDN, caché y seguridad
- **🌐 DNS Only (Gris):** Solo DNS, sin protección Cloudflare
- **USAR SIEMPRE Proxied (Naranja)**

### **Sobre SSL/TLS Full (strict):**
- **Requiere:** Certificado SSL válido en el servidor origen
- **Nuestro backend:** ✅ Ya está configurado para esto
- **Resultado:** Conexión HTTPS cifrada de extremo a extremo

### **Errores Comunes:**
```
❌ Error 525: SSL handshake failed
   → Solución: Esperar 5-10 minutos por certificado

❌ Error 524: Timeout occurred
   → Solución: Verificar que backend esté corriendo

❌ DNS still propagating
   → Solución: Esperar 5-15 minutos
```

---

## 🎉 **RESULTADO FINAL**

Cuando termines:
- ✅ Dominio funcional con HTTPS
- ✅ CDN global (Cloudflare)
- ✅ Protección DDoS automática
- ✅ Caché automática de contenido
- ✅ Certificado SSL/TLS válido
- ✅ Backend accesible globalmente
- ✅ Frontend Lovable conectado

**¡Gen Scene Studio estará listo para producción global!** 🚀

---

## 🆘 **AYUDA RÁPIDA**

### **Si algo no funciona:**
1. **Verifica los 3 registros A** están exactamente como se muestra
2. **Confirma Proxy status** es ☁️ Proxied (naranja)
3. **Espera 10-15 minutos** por propagación DNS
4. **Revisa SSL/TLS** está en "Full (strict)"

### **Comandos de testing (después de 10 min):**
```bash
# Test básico
curl -I https://genscenestudio.com/health

# Test con API key
curl -X POST "https://genscenestudio.com/api/tts" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: genscene_api_key_prod_2025_secure" \
  -d '{"job_id":"test","text":"Funciona!"}'
```

---

**Archivo creado:** 2025-11-04
**Última actualización:** Configuración completa paso a paso
**Estado:** Listo para ejecutar manualmente