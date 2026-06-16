#!/usr/bin/env python3
"""
Security Check Module
Validates environment configuration and detects hardcoded secrets
"""
import os
import sys
import re
from pathlib import Path
from typing import List, Tuple

# Patterns that might indicate hardcoded secrets
SECRET_PATTERNS = [
    r'AGNES_MERCHANT_KEY\s*=\s*["\']wk-[A-Za-z0-9]+["\']',
    r'AGNES_PERSONAL_KEY\s*=\s*["\']sk-[A-Za-z0-9]+["\']',
    r'NVIDIA_API_KEY\s*=\s*["\']nvapi-[A-Za-z0-9\-_]+["\']',
    r'AWS_ACCESS_KEY_ID\s*=\s*["\']AKIA[A-Z0-9]+["\']',
    r'AWS_SECRET_ACCESS_KEY\s*=\s*["\'][A-Za-z0-9/+=]+["\']',
    r'LOCAL_AUTH_TOKEN\s*=\s*["\'][A-Za-z0-9\-_]+["\']',
    r'api[_-]?key\s*=\s*["\'][A-Za-z0-9\-_]+["\']',
    r'secret[_-]?key\s*=\s*["\'][A-Za-z0-9\-_]+["\']',
    r'password\s*=\s*["\'][^"\']{8,}["\']',
    r'token\s*=\s*["\'][A-Za-z0-9\-_]{20,}["\']',
]

# Required environment variables
REQUIRED_ENV_VARS = [
    'AGNES_MERCHANT_KEY',
    'AGNES_PERSONAL_KEY', 
    'NVIDIA_API_KEY',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'LOCAL_AUTH_TOKEN'
]

def check_env_file_exists() -> bool:
    """Check if .env file exists"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ SECURITY ERROR: .env file not found!")
        print("Please create a .env file with the required environment variables.")
        print("Use .env.example as a template.")
        return False
    return True

def check_env_file_configured() -> bool:
    """Check if .env file is properly configured"""
    env_path = Path('.env')
    
    try:
        with open(env_path, 'r') as f:
            content = f.read()
        
        missing_vars = []
        for var in REQUIRED_ENV_VARS:
            if var not in content:
                missing_vars.append(var)
        
        if missing_vars:
            print("❌ SECURITY ERROR: .env file is missing required variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print("\nPlease add these variables to your .env file.")
            return False
        
        # Check for placeholder values
        placeholder_patterns = [
            r'your_agnes_merchant_key_here',
            r'your_agnes_personal_key_here',
            r'your_nvidia_api_key_here',
            r'your_aws_access_key_id_here',
            r'your_aws_secret_access_key_here',
            r'your_random_auth_token_here',
            r'PLACEHOLDER',
            r'XXX',
            r'REPLACE_ME'
        ]
        
        for pattern in placeholder_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"❌ SECURITY ERROR: .env file contains placeholder values: {pattern}")
                print("Please replace placeholders with actual values.")
                return False
        
        return True
    except Exception as e:
        print(f"❌ SECURITY ERROR: Failed to read .env file: {str(e)}")
        return False

def scan_for_hardcoded_secrets(file_path: Path) -> List[Tuple[int, str]]:
    """Scan a Python file for hardcoded secrets"""
    secrets_found = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            for pattern in SECRET_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    secrets_found.append((line_num, line.strip()))
                    break  # Only report once per line
    except Exception as e:
        print(f"⚠️  Warning: Could not read {file_path}: {str(e)}")
    
    return secrets_found

def check_python_files_for_secrets() -> bool:
    """Check all Python files for hardcoded secrets"""
    print("🔍 Scanning Python files for hardcoded secrets...")
    
    current_dir = Path('.')
    python_files = list(current_dir.glob('*.py'))
    
    if not python_files:
        print("✅ No Python files found to scan.")
        return True
    
    secrets_found_total = 0
    
    for py_file in python_files:
        # Skip the security check file itself
        if py_file.name == 'security_check.py':
            continue
            
        secrets = scan_for_hardcoded_secrets(py_file)
        
        if secrets:
            print(f"❌ SECURITY ERROR: Found potential secrets in {py_file.name}:")
            for line_num, line in secrets:
                print(f"   Line {line_num}: {line[:80]}...")
            secrets_found_total += len(secrets)
    
    if secrets_found_total > 0:
        print(f"\n❌ Found {secrets_found_total} potential hardcoded secret(s)!")
        print("Please move all secrets to .env file and use os.getenv() to access them.")
        return False
    else:
        print("✅ No hardcoded secrets found in Python files.")
        return True

def check_gitignore_for_env() -> bool:
    """Check if .env is in .gitignore"""
    gitignore_path = Path('.gitignore')
    
    if not gitignore_path.exists():
        print("❌ SECURITY ERROR: .gitignore file not found!")
        return False
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    if '.env' not in content:
        print("❌ SECURITY ERROR: .env is not in .gitignore!")
        print("This could lead to accidental commit of secrets.")
        return False
    
    print("✅ .env is properly excluded in .gitignore.")
    return True

def run_security_checks() -> bool:
    """Run all security checks"""
    print("=" * 60)
    print("🔒 SECURITY AUDIT")
    print("=" * 60)
    print()
    
    all_passed = True
    
    # Check 1: .env file exists
    if not check_env_file_exists():
        all_passed = False
    print()
    
    # Check 2: .env file configured
    if all_passed and not check_env_file_configured():
        all_passed = False
    print()
    
    # Check 3: No hardcoded secrets in Python files
    if not check_python_files_for_secrets():
        all_passed = False
    print()
    
    # Check 4: .gitignore excludes .env
    if not check_gitignore_for_env():
        all_passed = False
    print()
    
    print("=" * 60)
    if all_passed:
        print("✅ ALL SECURITY CHECKS PASSED")
        print("=" * 60)
        return True
    else:
        print("❌ SECURITY CHECKS FAILED")
        print("=" * 60)
        print("\nPlease fix the security issues above before proceeding.")
        return False

if __name__ == "__main__":
    if not run_security_checks():
        sys.exit(1)
    else:
        sys.exit(0)
