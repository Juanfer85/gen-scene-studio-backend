#!/bin/bash

# 🚀 Gen Scene Studio - Deploy Script
# Sincroniza cambios de desarrollo a producción

set -e  # Detener en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
SSH_HOST="94.72.113.216"
SSH_USER="root"
SSH_PASSWORD="JLcontabo7828tls"
API_URL="https://api.genscenestudio.com"

echo -e "${BLUE}🚀 Gen Scene Studio - Deploy Script${NC}"
echo -e "${YELLOW}Iniciando despliegue a producción...${NC}"
echo

# 1. Verificar que tenemos Git limpio
echo -e "${BLUE}1️⃣ Verificando estado de Git...${NC}"
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${YELLOW}⚠️  Hay cambios sin commitear. Creando commit automático...${NC}"
    git add .
    git commit -m "Auto deploy - $(date '+%Y-%m-%d %H:%M:%S')

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
else
    echo -e "${GREEN}✅ Git está limpio${NC}"
fi

# 2. Build del frontend
echo -e "${BLUE}2️⃣ Build del frontend...${NC}"
cd frontend
npm ci
npm run build
echo -e "${GREEN}✅ Frontend build completado${NC}"

# 3. Deploy backend
echo -e "${BLUE}3️⃣ Deploy del backend...${NC}"
cd ..

# Copiar archivos del backend
echo "📦 Copiando archivos del backend..."
sshpass -p "$SSH_PASSWORD" scp -o StrictHostKeyChecking=no -r whatif-backend/* $SSH_USER@$SSH_HOST:/opt/genscene-backend/

# Reiniciar contenedor del backend
echo "🔄 Reiniciando backend..."
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SSH_USER@$SSH_HOST "cd /opt/genscene-backend && docker compose restart genscene-backend"

# 4. Health check
echo -e "${BLUE}4️⃣ Verificando salud del sistema...${NC}"
sleep 10

# Backend health
echo "🏥 Chequeando backend health..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
if [ "$BACKEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Backend saludable (${BACKEND_STATUS})${NC}"
else
    echo -e "${RED}❌ Backend no responde (${BACKEND_STATUS})${NC}"
    exit 1
fi

# Styles endpoint
echo "🎨 Chequeando endpoint de estilos..."
STYLES_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/styles")
if [ "$STYLES_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Endpoint de estilos funcionando (${STYLES_STATUS})${NC}"
else
    echo -e "${RED}❌ Endpoint de estilos no responde (${STYLES_STATUS})${NC}"
fi

# 5. Success
echo
echo -e "${GREEN}🎉 DESPLIEGUE COMPLETADO CON ÉXITO${NC}"
echo -e "${BLUE}📊 URLs de producción:${NC}"
echo -e "   🏥 Backend Health: ${GREEN}$API_URL/health${NC}"
echo -e "   🎨 Styles API:   ${GREEN}$API_URL/styles${NC}"
echo -e "   🎬 Video Compose:${GREEN}$API_URL/api/compose${NC}"
echo
echo -e "${YELLOW}⚠️  Nota: Para deploy automático completo, configura:${NC}"
echo -e "   • Repositorio en GitHub"
echo -e "   • Vercel para frontend"
echo -e "   • GitHub Actions para CI/CD"
echo
echo -e "${GREEN}✨ Gen Scene Studio está listo para producción!${NC}"