#!/usr/bin/env python3

"""
Gen Scene Studio Backend Cleanup Script
Phase 1: Safely remove duplicate backend files after migration validation
"""

import os
import shutil
from pathlib import Path

class DuplicateCleaner:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.backup_dir = self.project_root / "archive" / "refactoring" / "backup-2025-12-01"
        
        # Essential files to preserve (in project root)
        self.preserve_files = {
            "app_complete_final.py",      # Production backend
            "simple_working_app.py",      # Reference implementation  
            "app_worker_polling.py",      # Latest worker implementation
        }
        
        # Files to remove (categorized by priority)
        self.remove_high_priority = {
            "app_with_manual_worker.py",
            "app_fixed_worker.py", 
            "app_working_current.py",
        }
        
        self.remove_medium_priority = {
            "app_definitivo_worker.py",
            "app_final_robusto.py",
            "app_minimal_corrected.py",
            "app_minimal_with_endpoint.py",
        }
        
        self.remove_low_priority = {
            "app_complete.py",
            "app_with_lifespan.py", 
            "app_worker_fixed.py",
        }
        
        # Jobs hub series (all duplicates)
        self.remove_jobs_hub = {
            "app_with_jobs_hub_endpoint.py",
            "app_with_jobs_hub_endpoint_date_fixed.py",
            "app_with_jobs_hub_endpoint_fixed.py", 
            "app_with_jobs_hub_endpoint_robust.py",
            "app_with_jobs_hub_endpoint_simple.py",
            "app_complete_final_with_hub.py",
        }
        
        # Utility files
        self.remove_utilities = {
            "quickcreate_fix.py",
            "test_logo_scale_fix.py",
        }
        
        self.all_removals = (self.remove_high_priority | self.remove_medium_priority | 
                           self.remove_low_priority | self.remove_jobs_hub | self.remove_utilities)
    
    def verify_backup(self):
        """Verify that all files exist in backup before removal"""
        print("🔍 Verifying backup integrity...")
        
        missing_in_backup = []
        for filename in self.all_removals:
            backup_file = self.backup_dir / filename
            if not backup_file.exists():
                missing_in_backup.append(filename)
        
        if missing_in_backup:
            print(f"❌ Files missing from backup: {missing_in_backup}")
            return False
        
        print("✅ All files verified in backup")
        return True
    
    def categorize_existing_files(self):
        """Check which duplicate files actually exist in project root"""
        print("📂 Categorizing existing duplicate files...")
        
        existing_files = {
            "high": [],
            "medium": [], 
            "low": [],
            "jobs_hub": [],
            "utilities": [],
            "preserve": []
        }
        
        for file in self.project_root.glob("*.py"):
            if file.name in self.remove_high_priority:
                existing_files["high"].append(file.name)
            elif file.name in self.remove_medium_priority:
                existing_files["medium"].append(file.name)
            elif file.name in self.remove_low_priority:
                existing_files["low"].append(file.name)
            elif file.name in self.remove_jobs_hub:
                existing_files["jobs_hub"].append(file.name)
            elif file.name in self.remove_utilities:
                existing_files["utilities"].append(file.name)
            elif file.name in self.preserve_files:
                existing_files["preserve"].append(file.name)
        
        return existing_files
    
    def show_removal_plan(self, existing_files):
        """Display what will be removed and preserved"""
        print("\n📋 CLEANUP PLAN")
        print("=" * 50)
        
        print("\n📂 FILES TO PRESERVE:")
        for filename in existing_files["preserve"]:
            print(f"  ✅ {filename}")
        
        total_to_remove = 0
        for category, files in existing_files.items():
            if category != "preserve" and files:
                print(f"\n🗑️  {category.upper()} PRIORITY ({len(files)} files):")
                for filename in files:
                    print(f"  ❌ {filename}")
                total_to_remove += len(files)
        
        print(f"\n📊 SUMMARY: {total_to_remove} files to remove, {len(existing_files['preserve'])} files to preserve")
    
    def remove_duplicates(self, existing_files, dry_run=True):
        """Remove the duplicate files"""
        if dry_run:
            print("\n🔍 DRY RUN - No files will be removed")
            return True
        
        print("\n🗑️  Removing duplicate files...")
        
        removed_count = 0
        errors = []
        
        for category, files in existing_files.items():
            if category == "preserve":
                continue
                
            for filename in files:
                try:
                    file_path = self.project_root / filename
                    file_path.unlink()
                    print(f"  ✅ Removed {filename}")
                    removed_count += 1
                except Exception as e:
                    errors.append(f"❌ Failed to remove {filename}: {e}")
        
        if errors:
            print("\n⚠️  ERRORS:")
            for error in errors:
                print(f"  {error}")
        
        print(f"\n🎉 Successfully removed {removed_count} duplicate files")
        return len(errors) == 0
    
    def run_cleanup(self, dry_run=True):
        """Execute the cleanup process"""
        print("🚀 Starting Gen Scene Studio Backend Cleanup")
        print("=" * 50)
        
        # Step 1: Verify backup
        if not self.verify_backup():
            print("❌ Backup verification failed. Aborting cleanup.")
            return False
        
        # Step 2: Categorize existing files
        existing_files = self.categorize_existing_files()
        
        # Step 3: Show removal plan
        self.show_removal_plan(existing_files)
        
        # Step 4: Confirm and execute
        if dry_run:
            print("\n💡 This is a DRY RUN. No files were removed.")
            print("   Run with dry_run=False to execute actual removal.")
            return True
        
        response = input("\n❓ Do you want to proceed with file removal? (yes/N): ")
        if response.lower() not in ["yes", "y"]:
            print("❌ Cleanup cancelled by user.")
            return False
        
        # Step 5: Remove duplicates
        return self.remove_duplicates(existing_files, dry_run=False)

if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    dry_run = "--execute" not in sys.argv
    
    cleaner = DuplicateCleaner()
    success = cleaner.run_cleanup(dry_run=dry_run)
    
    if success:
        if dry_run:
            print("\n🎯 DRY RUN COMPLETED SUCCESSFULLY")
            print("   Run 'python cleanup_duplicates.py --execute' to remove files")
        else:
            print("\n🎉 CLEANUP COMPLETED SUCCESSFULLY")
            print("   Duplicate files have been removed from project root")
    
    sys.exit(0 if success else 1)
