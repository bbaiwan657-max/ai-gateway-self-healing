#!/usr/bin/env python3
"""
Manual Security Audit Script
Run this script to perform a comprehensive security check of the project
"""
import sys
import subprocess

def main():
    print("=" * 60)
    print("🔒 MANUAL SECURITY AUDIT")
    print("=" * 60)
    print()
    
    try:
        result = subprocess.run(
            [sys.executable, 'security_check.py'],
            timeout=30
        )
        
        if result.returncode == 0:
            print()
            print("=" * 60)
            print("✅ SECURITY AUDIT PASSED")
            print("=" * 60)
            print()
            print("Your project is secure. No security issues detected.")
            return 0
        else:
            print()
            print("=" * 60)
            print("❌ SECURITY AUDIT FAILED")
            print("=" * 60)
            print()
            print("Please fix the security issues listed above.")
            return 1
            
    except subprocess.TimeoutExpired:
        print("❌ Security audit timed out.")
        return 1
    except Exception as e:
        print(f"❌ Error running security audit: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
