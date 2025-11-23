# 🌐 Cloudflare Setup Guide - Gen Scene Studio

**VPS IP:** 94.72.113.216
**Dominio:** genscenestudio.com
**Estado:** Backend listo para configuración Cloudflare

## 🔧 **Configuración DNS en Cloudflare Dashboard:**

### **1. Acceder a Cloudflare:**
1. Inicia sesión en [cloudflare.com](https://cloudflare.com)
2. Selecciona el dominio `genscenestudio.com`

### **2. Configurar Registros DNS:**

#### **Registros A Principales:**
```
Type: A     Name: @         Content: 94.72.113.216    Proxy: Enabled (☁️ naranja)
Type: A     Name: www       Content: 94.72.113.216    Proxy: Enabled (☁️ naranja)
Type: A     Name: api       Content: 94.72.113.216    Proxy: Enabled (☁️ naranja)
```

#### **Registros CNAME (si usas subdominios adicionales):**
```
Type: CNAME Name: app       Content: genscenestudio.com    Proxy: Enabled
Type: CNAME Name: dashboard  Content: genscenestudio.com    Proxy: Enabled
```

### **3. Configuración SSL/TLS:**

#### **SSL/TLS → Overview:**
- **Encryption Mode:** `Full (strict)`
- **Always Use HTTPS:** `On`
- **HTTP Strict Transport Security (HSTS):** `Enable`

#### **Edge Certificates:**
- ✅ `Always Use HTTPS`
- ✅ `HTTP Strict Transport Security (HSTS)`
- ✅ `Minimum TLS Version`: `1.2`

### **4. Configuración de Seguridad:**

#### **Firewall Rules:**
```
Rule Name: Rate Limiting
Action: Rate Limit
Rate: 60 requests per minute
```

#### **Bot Fight Mode:**
- **Status:** `On`

#### **Web Application Firewall (WAF):**
- **Security Level:** `Medium`
- **OWASP Core Ruleset:** `Enable`

### **5. Configuración de Performance:**

#### **Caching:**
```
Caching Level: Standard
Browser Cache TTL: 4 hours
Edge Cache TTL: 2 hours
```

#### **Page Rules:**
```
URL Pattern: genscenestudio.com/*
Settings: Cache Level: Cache Everything
Edge Cache TTL: 1 hour
Browser Cache TTL: 4 hours
```

## 🚀 **Configuración en el VPS:**

### **Backend Configuration (✅ Completado):**
```bash
# Variables de entorno actualizadas
BACKEND_BASE_URL=https://genscenestudio.com
PUBLIC_BASE_URL=https://genscenestudio.com
CORS_ALLOW_ORIGINS=https://genscenestudio.com,https://www.genscenestudio.com,https://api.genscenestudio.com
```

### **Firewall UFW:**
```bash
# Puertos permitidos
Port 22 (SSH)   - Permitido
Port 8000 (HTTP) - Permitido para health checks
```

## 🧪 **Testing y Verificación:**

### **1. Verificar DNS Propagation:**
```bash
# Desde tu máquina local
dig genscenestudio.com A
nslookup genscenestudio.com
ping genscenestudio.com
```

### **2. Verificar Certificado SSL:**
```bash
# Verificar certificado
openssl s_client -connect genscenestudio.com:443 -servername genscenestudio.com
```

### **3. Test Endpoints a través de Cloudflare:**
```bash
# Health check con HTTPS
curl -X GET "https://genscenestudio.com/health"

# TTS con HTTPS y dominio
curl -X POST "https://genscenestudio.com/api/tts" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: genscene_api_key_prod_2025_secure" \
  -d '{"job_id":"test-cloudflare-001","text":"Gen Scene Studio con Cloudflare","voice_id":"es_ES-carlfm-high"}'
```

## 🎯 **Endpoints Finales:**

### ** URLs de Producción:**
- **API Principal:** https://genscenestudio.com
- **API Subdominio:** https://api.genscenestudio.com
- **WWW:** https://www.genscenestudio.com

### **Endpoints API:**
```bash
# Health Check
GET https://genscenestudio.com/health

# TTS Synthesis
POST https://genscenestudio.com/api/tts

# Video Composition
POST https://genscenestudio.com/api/compose

# Job Status
GET https://genscenestudio.com/api/status?job_id=XXXX

# File Download
GET https://genscenestudio.com/files/{job_id}/{filename}
```

## 🔒 **Configuración de Seguridad Adicional:**

### **API Authentication:**
- ✅ API Key: `genscene_api_key_prod_2025_secure`
- ✅ Rate Limiting: 60 requests/min
- ✅ CORS configurado para dominios Cloudflare

### **Cloudflare Security Features:**
- ✅ DDoS Protection
- ✅ Bot Management
- ✅ WAF Rules
- ✅ SSL/TLS encryption
- ✅ HTTP/3 support

## 📊 **Monitoreo y Analytics:**

### **Cloudflare Analytics:**
- Trafico y solicitudes
- Seguridad y threats bloqueados
- Performance metrics
- Cache hit ratio

### **Backend Health:**
```bash
# Health check automatizado
curl -f https://genscenestudio.com/health || echo "ALERT: Backend down"
```

## 🔄 **Proximos Pasos:**

1. **✅ Configurar DNS en Cloudflare** - Realizar manualmente
2. **✅ Verificar propagación DNS** - 5-15 minutos
3. **✅ Test HTTPS endpoints** - Inmediatamente después
4. **🔄 Configurar dominio personalizado** - Si se requiere
5. **🔄 Set up monitoring** - Alertas y notificaciones
6. **🔄 Backup automation** - Para base de datos y media

## 🎉 **Resultado Final:**

**Gen Scene Studio estará accesible en:**
- 🌐 **https://genscenestudio.com** (SSL + CDN + Security)
- 🔒 **Seguridad enterprise-grade** (Cloudflare WAF)
- ⚡ **Performance global** (CDN edge caching)
- 🛡️ **DDoS protection** automática
- 📊 **Analytics y monitoring** integrados

**¡Listo para producción con Cloudflare!** 🚀