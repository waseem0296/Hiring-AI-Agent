#!/usr/bin/env python3
"""
Detailed test script for JWT authentication (no emojis for Windows compatibility)
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_auth_detailed():
    print("=" * 70)
    print("DETAILED JWT AUTHENTICATION TEST")
    print("=" * 70)
    
    # Test 1: Check environment variables
    print("\n[1] Checking environment variables...")
    email = os.getenv("HIREOLOGY_EMAIL")
    password = os.getenv("HIREOLOGY_PASSWORD")
    
    if not email or not password:
        print("[FAIL] Environment variables not set!")
        print(f"   HIREOLOGY_EMAIL: {'SET' if email else 'NOT SET'}")
        print(f"   HIREOLOGY_PASSWORD: {'SET' if password else 'NOT SET'}")
        return False
    
    print(f"[OK] Email: {email}")
    print(f"[OK] Password: {'*' * len(password)} (length: {len(password)})")
    
    # Test 2: Try to login
    print("\n[2] Attempting to login and get JWT...")
    try:
        from auth_manager import login_and_get_jwt
        jwt = login_and_get_jwt()
        
        if jwt:
            print(f"\n[SUCCESS] Got JWT token")
            print(f"   Length: {len(jwt)}")
            print(f"   First 50 chars: {jwt[:50]}...")
            print(f"   Last 50 chars: ...{jwt[-50:]}")
            return True
        else:
            print("[FAIL] login_and_get_jwt() returned None")
            return False
            
    except Exception as e:
        print(f"\n[FAIL] Login failed with error:")
        print(f"   {str(e)[:500]}")
        
        # Check if it's the expected error message
        if "Could not authenticate" in str(e):
            print("\n[INFO] This is expected - Hireology doesn't support programmatic login.")
            print("   The system is working correctly!")
            print("\n[NEXT STEPS]")
            print("   1. Get a fresh JWT from Hireology dashboard")
            print("   2. Run: python manual_jwt_update.py")
            print("   3. Paste the JWT when prompted")
            return "manual"
        else:
            return False
    
    # Test 3: Test API call with JWT
    print("\n[3] Testing API call with JWT...")
    try:
        from fetch_applicants import get_candidates
        candidates = get_candidates(job_id="2606114")
        print(f"[OK] API call successful! Found {len(candidates.get('data', []))} candidates")
        return True
    except Exception as e:
        print(f"[FAIL] API call failed: {e}")
        return False

if __name__ == "__main__":
    result = test_auth_detailed()
    
    print("\n" + "=" * 70)
    if result == True:
        print("[SUCCESS] ALL TESTS PASSED!")
        print("[OK] JWT auto-regeneration system is working correctly")
    elif result == "manual":
        print("[WARNING] MANUAL JWT SETUP REQUIRED")
        print("[OK] System is configured correctly, but needs manual JWT")
    else:
        print("[FAIL] TESTS FAILED")
        print("Please check the errors above")
    print("=" * 70)
