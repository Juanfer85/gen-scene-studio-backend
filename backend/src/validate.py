#!/usr/bin/env python3

"""
Gen Scene Studio Backend Validation Script
Phase 1: Validate that all essential functionality is preserved after refactoring
"""

import subprocess
import sys
import os
import json
import requests
import time
from pathlib import Path

class BackendValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.backend_dir = self.project_root / "backend" / "src"
        self.results = {
            "structure": [],
            "imports": [],
            "endpoints": [],
            "database": []
        }
    
    def validate_structure(self):
        """Validate new backend directory structure"""
        print("🔍 Validating backend structure...")
        
        required_dirs = [
            "core",
            "models", 
            "utils",
            "api",
            "worker"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.backend_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self.results["structure"].append(f"✅ {dir_name}/ exists")
            else:
                self.results["structure"].append(f"❌ {dir_name}/ missing")
        
        # Check essential files
        essential_files = [
            "main.py",
            "core/config.py",
            "models/dao.py",
            "core/db.py",
            "core/logging.py"
        ]
        
        for file_name in essential_files:
            file_path = self.backend_dir / file_name
            if file_path.exists() and file_path.is_file():
                self.results["structure"].append(f"✅ {file_name} exists")
            else:
                self.results["structure"].append(f"❌ {file_name} missing")
    
    def validate_imports(self):
        """Validate that imports work correctly"""
        print("🔍 Validating imports...")
        
        try:
            # Add backend src to Python path
            sys.path.insert(0, str(self.backend_dir))
            
            # Test core imports
            from core.config import settings
            self.results["imports"].append("✅ core.config imports successfully")
            
            from models.dao import init_db
            self.results["imports"].append("✅ models.dao imports successfully")
            
            from core.db import get_conn
            self.results["imports"].append("✅ core.db imports successfully")
            
        except Exception as e:
            self.results["imports"].append(f"❌ Import error: {str(e)}")
    
    def validate_endpoints(self):
        """Validate that essential API endpoints are defined"""
        print("🔍 Validating API endpoints...")
        
        try:
            sys.path.insert(0, str(self.backend_dir))
            
            # Read main.py and check for essential endpoints
            main_py = self.backend_dir / "main.py"
            if main_py.exists():
                content = main_py.read_text()
                
                essential_endpoints = [
                    "/health",
                    "/api/quick-create-full-universe", 
                    "/api/compose",
                    "/api/jobs",
                    "/api/jobs/{job_id}",
                    "/api/tts",
                    "/api/delete-job"
                ]
                
                for endpoint in essential_endpoints:
                    if endpoint in content:
                        self.results["endpoints"].append(f"✅ {endpoint} found")
                    else:
                        self.results["endpoints"].append(f"❌ {endpoint} missing")
            else:
                self.results["endpoints"].append("❌ main.py not found")
                
        except Exception as e:
            self.results["endpoints"].append(f"❌ Endpoint validation error: {str(e)}")
    
    def validate_database(self):
        """Validate database connectivity and schema"""
        print("🔍 Validating database...")
        
        try:
            sys.path.insert(0, str(self.backend_dir))
            
            from core.db import get_conn
            from models.dao import init_db
            
            # Test database connection
            conn = get_conn()
            if conn:
                self.results["database"].append("✅ Database connection successful")
                
                # Test database initialization
                init_db(conn)
                self.results["database"].append("✅ Database schema initialization successful")
                
                conn.close()
            else:
                self.results["database"].append("❌ Database connection failed")
                
        except Exception as e:
            self.results["database"].append(f"❌ Database validation error: {str(e)}")
    
    def run_validation(self):
        """Run all validation checks"""
        print("🚀 Starting Gen Scene Studio Backend Validation")
        print("=" * 50)
        
        self.validate_structure()
        self.validate_imports()
        self.validate_endpoints()
        self.validate_database()
        
        print("\n📊 VALIDATION RESULTS")
        print("=" * 50)
        
        total_checks = 0
        passed_checks = 0
        
        for category, checks in self.results.items():
            print(f"\n{category.upper()}:")
            for check in checks:
                print(f"  {check}")
                total_checks += 1
                if "✅" in check:
                    passed_checks += 1
        
        print(f"\n📈 SUMMARY: {passed_checks}/{total_checks} checks passed")
        
        if passed_checks == total_checks:
            print("🎉 ALL VALIDATION CHECKS PASSED!")
            return True
        else:
            print("⚠️  Some validation checks failed. Review above results.")
            return False

if __name__ == "__main__":
    validator = BackendValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)
