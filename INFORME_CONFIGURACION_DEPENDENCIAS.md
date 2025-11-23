# Informe de Análisis de Configuración y Dependencias
## Proyecto: Gen Scene Studio Backend

**Fecha:** 15 de noviembre de 2025
**Versión Python:** 3.12.3
**Tipo:** Backend FastAPI con Docker

---

## 🚨 PROBLEMAS CRÍTICOS ENCONTRADOS

### 1. **DEPENDENCIAS FALTANTES EN requirements.txt**
**Severidad:** CRÍTICA

El archivo `requirements.txt` está incompleto y no incluye varias dependencias que son utilizadas en el código:

```python
# requirements.txt actual (INCOMPLETO)
fastapi==0.115.0
uvicorn[standard]==0.30.6
httpx==0.27.2
pydantic==2.9.2
pydantic-settings==2.6.1
python-multipart==0.0.9
tenacity==9.0.0
aiohttp==3.11.10
```

**Dependencias faltantes detectadas en el código:**
- `sqlite3` (viene con Python pero necesita confirmación)
- `ffmpeg-python` o `python-ffmpeg` (para procesamiento de video)
- `Pillow` o `PIL` (para procesamiento de imágenes)
- `numpy` (probablemente necesario para procesamiento)
- `asyncio` (viene con Python)
- `pathlib` (viene con Python)

**Impacto:** La aplicación fallará al iniciar en un entorno limpio.

**Solución:**
```txt
# requirements.txt COMPLETO CORREGIDO
fastapi==0.115.0
uvicorn[standard]==0.30.6
httpx==0.27.2
pydantic==2.9.2
pydantic-settings==2.6.1
python-multipart==0.0.9
tenacity==9.0.0
aiohttp==3.11.10
ffmpeg-python==0.2.0
Pillow==10.2.0
numpy==1.26.2
python-dotenv==1.0.0
```

### 2. **DUPLICACIÓN Y CONFLICTOS EN VARIABLES DE ENTORNO**
**Severidad:** ALTA

El archivo `.env` tiene serios problemas:

**Problemas detectados:**
- Variables duplicadas (ej. `ALLOW_DEBUG=1` aparece 2 veces)
- `NOTIFY_SECRET` tiene valores inconsistentes
- `MEDIA_DIR` definido 3 veces con diferentes valores
- Comentarios que no corresponden con la configuración real

**Ejemplo del problema:**
```bash
# Archivo .env actual con problemas
ALLOW_DEBUG=1
ALLOW_DEBUG=1  # DUPLICADO
NOTIFY_SECRET=change-me
NOTIFY_SECRET=puente_whatif_lovable_jF_77xYz!_2025  # INCONSISTENTE
MEDIA_DIR=./media
MEDIA_DIR=/mnt/c/Users/user/proyectos_globales/proyecto_videos_what_if/whatif-backend/media  # RUTA ABSOLUTA
```

**Impacto:** Comportamiento impredecible, valores sobrescritos, configuración incorrecta.

**Solución:** Limpiar el archivo eliminando duplicados y estandarizar valores.

### 3. **VULNERABILIDADES DE SEGURIDAD**
**Severidad:** ALTA

**Problemas de seguridad detectados:**

#### a) Claves API expuestas en archivos de configuración:
```bash
# .env y .env.prod contienen:
KIE_API_KEY=cec334b20b0c57881abd7a85524da41b  # CLAVE REAL EXPUESTA
```

#### b) Tokens de webhook débiles:
```bash
NOTIFY_SECRET=change-me  # TOKEN INSEGURO POR DEFECTO
```

#### c) Claves de API por defecto:
```bash
BACKEND_API_KEY=whatif_api_key_dev_2025_abc123  # FÁCIL DE ADIVINAR
```

**Solución:**
- Usar variables de entorno reales en producción
- Rotar todas las claves expuestas
- Implementar gestión de secretos (Docker Secrets, AWS Secrets Manager, etc.)

### 4. **PROBLEMAS EN CONFIGURACIÓN DOCKER**
**Severidad:** MEDIA

#### a) **Volumen de base de datos mal configurado:**
```yaml
# docker-compose.yml - PROBLEMÁTICO
volumes:
  - genscene_data:/app/whatif.db  # Mapea directorio, no archivo
```

**Problema:** SQLite necesita acceso al archivo `.db`, no al directorio.

**Solución:**
```yaml
volumes:
  - ./data:/app/data  # Directorio para el archivo .db
environment:
  - DATABASE_URL=sqlite:///./data/whatif.db
```

#### b) **Download de modelos TTS sin verificación:**
```dockerfile
# Sin verificación de integridad
RUN wget -qO /app/models/es_ES-carlfm-high.onnx https://...
```

**Riesgo:** Descarga de archivos corruptos o maliciosos.

**Solución:** Agregar verificación de hashes SHA256.

### 5. **INCONSISTENCIAS ENTRE ENTORNOS**
**Severidad:** MEDIA

**Problemas detectados:**

| Variable | .env.example | .env (dev) | .env.prod |
|----------|-------------|------------|-----------|
| TTS_PROVIDER | mock | mock | piper |
| ALLOW_DEBUG | 0 | 1 | 1 |
| SAFE_COMPOSE | 0 | 1 | 1 |
| CORS_ORIGINS | localhost | lovable.app | localhost |

**Impacto:** Comportamiento diferente entre entornos, posibles fallos en producción.

---

## 📋 ARCHIVOS DE CONFIGURACIÓN FALTANTES

### 1. **pyproject.toml** (Recomendado)
```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "genscene-backend"
version = "0.2.0"
description = "Gen Scene Studio Backend"
authors = [{name = "Your Name", email = "your.email@example.com"}]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.6",
    # ... otras dependencias
]

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I"]
```

### 2. **.dockerignore** (Existe pero puede mejorarse)
```dockerignore
# Existentes OK:
.git
.venv
venv
__pycache__
*.pyc

# Agregar:
.env
.env.prod
.gitignore
README.md
docs/
tests/
*.log
.DS_Store
```

### 3. **nginx.conf** (Si se necesita proxy reverso)
```nginx
server {
    listen 80;
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /files/ {
        alias /app/media/;
    }
}
```

### 4. **.gitignore** (Revisar si está completo)
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# Environment
.env
.env.prod
.env.local

# Database
*.db
*.sqlite
*.sqlite3

# Media
media/
!media/.gitkeep

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
```

---

## 🔧 SCRIPTS DE DEPLOYMENT - PROBLEMAS Y MEJORAS

### 1. **deploy.sh** - Problemas detectados:

#### a) **Sin manejo de errores robusto:**
```bash
# Actual: Sin verificación de éxito real
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Health check OK"
else
    echo "❌ Health check FAILED"
    docker logs whatif-backend-test  # Nombre incorrecto de contenedor
    exit 1
fi
```

#### b) **Sin limpieza de recursos antiguos:**
```bash
# Problema: No elimina imágenes Docker antiguas
# Solución: Agregar
docker system prune -f
docker image prune -f
```

### 2. **QUICK_DEPLOY.sh** - Problemas detectados:

#### a) **Hardcodeado para desarrollo:**
```bash
# Problema: IP del VPS debe ser configurada manualmente
VPS_IP="TU_VPS_IP_AQUI"
```

#### b) **Sin verificación de requisitos previos:**
```bash
# Faltan verificaciones de:
# - Conectividad SSH
# - Docker instalado en VPS
# - Permisos adecuados
# - Espacio en disco
```

### 3. **Makefile** - Incompleto:

```makefile
# Makefile mejorado
.PHONY: dev run fmt setup-wsl venv health test clean build docker-build docker-run docker-stop

dev:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	uvicorn app:app --host 0.0.0.0 --port 8000 --reload

fmt:
	python -m pip install ruff && ruff check --fix .
	ruff format .

test:
	python -m pytest tests/ -v

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/

venv:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

health:
	@curl -s http://localhost:8000/health || echo "Server no responde. ¿Está corriendo?"

docker-build:
	docker build -t genscene-backend .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f
```

---

## 🚀 PLAN DE CORRECCIÓN PRIORITARIO

### **Fase 1: Crítico (Ejecutar inmediatamente)**
1. **Corregir requirements.txt** con todas las dependencias faltantes
2. **Limpiar archivos .env** eliminando duplicados y claves expuestas
3. **Rotar todas las claves API** expuestas
4. **Verificar configuración de volúmenes Docker** para SQLite

### **Fase 2: Importante (Esta semana)**
1. **Crear .gitignore completo** si no existe
2. **Mejorar scripts de deployment** con manejo de errores
3. **Agregar verificación de hashes** para descargas de modelos TTS
4. **Estandarizar configuración** entre entornos

### **Fase 3: Mejoras (Próximo sprint)**
1. **Implementar gestión de secretos** (Docker Secrets o similar)
2. **Agregar tests automatizados** para configuración
3. **Crear pyproject.toml** para mejor gestión de dependencias
4. **Configurar CI/CD** con validación de configuración

---

## 📊 RESUMEN DE ESTADO ACTUAL

| Categoría | Estado | Severidad | Acción Inmediata |
|-----------|--------|-----------|------------------|
| Dependencias | ❌ Incompleto | Crítica | Sí |
| Variables de Entorno | ❌ Conflictos | Alta | Sí |
| Seguridad | ❌ Vulnerabilidades | Alta | Sí |
| Docker | ⚠️ Problemas | Media | No (urgente) |
| Scripts | ⚠️ Mejorable | Media | No |
| Documentación | ✅ Adecuado | Baja | No |

**Estado General:** 🔴 **CRÍTICO** - Requiere intervención inmediata antes de deployment a producción.

---

## 🎯 RECOMENDACIONES ADICIONALES

### 1. **Monitoreo y Logging**
```python
# Agregar al requirements.txt
structlog==23.2.0
prometheus-client==0.19.0
```

### 2. **Testing**
```python
# Agregar al requirements.txt (dev)
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.27.2  # Ya incluido, bueno para testing
```

### 3. **Quality Assurance**
```python
# Herramientas de calidad
ruff==0.1.6  # Linter y formatter
mypy==1.7.1  # Type checking
black==23.11.0  # Formatter (alternativa a ruff)
```

### 4. **Seguridad Adicional**
- Implementar rate limiting robusto
- Agregar headers de seguridad HTTP
- Configurar HTTPS/TLS
- Implementar auditoría de logs

---

## ⚠️ ADVERTENCIA FINAL

**No se debe realizar deployment a producción hasta resolver:**
1. Dependencias faltantes en requirements.txt
2. Claves API expuestas en archivos de configuración
3. Configuración de volúmenes Docker para SQLite
4. Limpieza de variables de entorno duplicadas

La aplicación actual fallará en un entorno limpio debido a las dependencias faltantes y presenta riesgos de seguridad significativos.