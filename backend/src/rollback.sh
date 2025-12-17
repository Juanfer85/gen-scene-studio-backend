#!/bin/bash

# Gen Scene Studio Backend Rollback Script
# Phase 1: Rollback from unified structure to original files

set -e

echo "🔄 Starting Phase 1 Backend Rollback..."

# Configuration
BACKUP_DIR="/mnt/c/Users/user/proyectos_globales/proyecto_gen_scene_studio/archive/refactoring/backup-2025-12-01"
PROJECT_ROOT="/mnt/c/Users/user/proyectos_globales/proyecto_gen_scene_studio"

# Step 1: Verify backup exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found. Cannot rollback."
    exit 1
fi

echo "✅ Backup found at $BACKUP_DIR"

# Step 2: Restore original files
echo "📂 Restoring original Python files..."
cp "$BACKUP_DIR"/*.py "$PROJECT_ROOT/"

# Step 3: Remove unified backend
echo "🗑️ Removing unified backend structure..."
rm -rf "$PROJECT_ROOT/backend/"
rm -f "$PROJECT_ROOT/app_unified.py"

echo "✅ Rollback completed successfully!"
echo "📁 Original backend files restored to project root"
echo "🔄 System is back to pre-migration state"
