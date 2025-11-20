#!/usr/bin/env python3
"""
Purpose: Test suite for PRD validation and structure verification
Created: 2025-11-19 20:18:23
Agent: PRD Agent
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

# Base directory
BASE_DIR = Path(__file__).parent.parent

class PRDValidator:
    """Validates PRD structure and content"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def test_directory_structure(self):
        """Test Phase 1: Directory structure exists"""
        required_dirs = [
            BASE_DIR / '.cursor' / 'docs',
            BASE_DIR / '.agents',
            BASE_DIR / '.agents' / 'contexts',
            BASE_DIR / '.agents' / 'logs',
            BASE_DIR / '.agents' / 'prd_steps',
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                self.errors.append(f"Missing directory: {dir_path}")
            elif not dir_path.is_dir():
                self.errors.append(f"Not a directory: {dir_path}")
                
        return len(self.errors) == 0
    
    def test_prd_file_exists(self):
        """Test Phase 2: PRD.md file exists"""
        prd_path = BASE_DIR / '.cursor' / 'docs' / 'PRD.md'
        if not prd_path.exists():
            self.errors.append(f"PRD.md not found at {prd_path}")
            return False
        return True
    
    def test_prd_sections(self):
        """Test Phase 2: PRD contains required sections"""
        prd_path = BASE_DIR / '.cursor' / 'docs' / 'PRD.md'
        if not prd_path.exists():
            return False
            
        content = prd_path.read_text()
        
        required_sections = [
            'Executive Summary',
            'Platform Architecture',
            'Workflow System',
            'Agent System',
            'Data Management',
            'Configuration Management',
            'Error Handling',
            'Development Workflow',
            'Change Management Process',
            'Future Roadmap'
        ]
        
        for section in required_sections:
            if section not in content:
                self.errors.append(f"Missing section: {section}")
                
        return len(self.errors) == 0
    
    def test_change_log_exists(self):
        """Test Phase 3: Change log file exists"""
        change_log_path = BASE_DIR / '.agents' / 'PRD.md'
        if not change_log_path.exists():
            self.errors.append(f"Change log not found at {change_log_path}")
            return False
        return True
    
    def test_change_log_structure(self):
        """Test Phase 3: Change log has proper structure"""
        change_log_path = BASE_DIR / '.agents' / 'PRD.md'
        if not change_log_path.exists():
            return False
            
        content = change_log_path.read_text()
        
        # Check for required fields in change log
        required_fields = ['timestamp', 'agent', 'change description']
        for field in required_fields:
            if field.lower() not in content.lower():
                self.warnings.append(f"Change log may be missing field: {field}")
                
        return True
    
    def test_phase_step_files(self):
        """Test: Phase step files exist"""
        prd_steps_dir = BASE_DIR / '.agents' / 'prd_steps'
        if not prd_steps_dir.exists():
            return False
            
        # Check for at least phase1 file
        phase1_file = prd_steps_dir / 'phase1-directory-structure.md'
        if not phase1_file.exists():
            self.errors.append("Phase 1 step file not found")
            return False
            
        return True
    
    def run_all_tests(self):
        """Run all tests"""
        print("Running PRD Validation Tests...")
        print("=" * 50)
        
        # Phase 1 tests
        print("\n[Phase 1] Testing directory structure...")
        self.test_directory_structure()
        self.test_phase_step_files()
        
        # Phase 2 tests (if PRD exists)
        if (BASE_DIR / '.cursor' / 'docs' / 'PRD.md').exists():
            print("\n[Phase 2] Testing PRD file...")
            self.test_prd_file_exists()
            self.test_prd_sections()
        
        # Phase 3 tests (if change log exists)
        if (BASE_DIR / '.agents' / 'PRD.md').exists():
            print("\n[Phase 3] Testing change log...")
            self.test_change_log_exists()
            self.test_change_log_structure()
        
        # Report results
        print("\n" + "=" * 50)
        if self.errors:
            print(f"❌ ERRORS: {len(self.errors)}")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("✅ No errors found")
            
        if self.warnings:
            print(f"\n⚠️  WARNINGS: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  - {warning}")
        else:
            print("✅ No warnings")
            
        return len(self.errors) == 0

if __name__ == '__main__':
    validator = PRDValidator()
    success = validator.run_all_tests()
    exit(0 if success else 1)

