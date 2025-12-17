#!/bin/bash

# Gen Scene Studio Backend Migration Script
# Phase 1: Migrate from duplicate files to unified structure

set -e

echo "🔄 Starting Phase 1 Backend Migration..."

# Configuration
BACKUP_DIR="/mnt/c/Users/user/proyectos_globales/proyecto_gen_scene_studio/archive/refactoring/backup-2025-12-01"
PROJECT_ROOT="/mnt/c/Users/user/proyectos_globales/proyecto_gen_scene_studio"
NEW_BACKEND="$PROJECT_ROOT/backend/src"

# Step 1: Verify backup exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found. Aborting migration."
    exit 1
fi

echo "✅ Backup verified at $BACKUP_DIR"

# Step 2: Create essential file links in project root
echo "🔗 Creating symlinks to maintain compatibility..."

# Link to new main backend
ln -sf "$NEW_BACKEND/main.py" "$PROJECT_ROOT/app_unified.py"

# Step 3: Update requirements for new structure
echo "📦 Updating backend requirements..."
cat > "$PROJECT_ROOT/backend/requirements.txt" << 'REQS'
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0
sqlite3
aiofiles==23.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
REQS

echo "✅ Migration completed successfully!"
echo "📁 New backend structure:"
echo "   - main.py: Unified application"
echo "   - core/: Configuration, database, logging, security"
echo "   - models/: Data access objects and schemas"
echo "   - utils/: Helper utilities"
echo "   - api/: API endpoint modules"
echo "   - worker/: Background task processing"
echo ""
echo "🔄 Next steps:"
echo "   1. Update Docker configuration to use app_unified.py"
echo "   2. Test API endpoints"
echo "   3. Remove duplicate files after validation"
