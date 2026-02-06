#!/usr/bin/env python3
"""
Test OTP integration with JWT authentication
"""

import os
import pyotp
from dotenv import load_dotenv
from auth_manager import login_and_get_jwt
from fetch_applicants import get_candidates

load_dotenv()

def test_otp_with_jwt():
    print("🔐 TESTING OTP + JWT INTEGRATION")
    print("="*50)
    
    # Get current OTP
    secret = os.getenv("TOTP_SECRET", "").replace(" ", "").upper()
    if not secret:
        print("❌ TOTP_SECRET not found in .env")
        return
    
    totp = pyotp.TOTP(secret)
    current_otp = totp.now()
    
    print(f"🔑 Current OTP: {current_otp}")
    print(f"🔑 Secret: {secret}")
    
    # Option 1: Try login with OTP as password
    print(f"\n1️⃣ Testing login with OTP as 2FA...")
    try:
        # Temporarily modify auth_manager to use OTP
        import auth_manager
        
        # Store original password
        original_password = auth_manager.PASSWORD
        
        # Try with OTP (if Hireology uses 2FA)
        auth_manager.PASSWORD = current_otp
        
        jwt = login_and_get_jwt()
        print(f"✅ SUCCESS! Got JWT with OTP (length: {len(jwt)})")
        
        # Test API call
        candidates = get_candidates(job_id="2606114")
        print(f"✅ API call successful! Found {len(candidates.get('data', []))} candidates")
        
        # Restore original password
        auth_manager.PASSWORD = original_password
        
    except Exception as e:
        print(f" OTP login failed: {e}")
        
        # Option 2: Try regular login (maybe OTP not needed for API)
        print(f"\n2️⃣ Testing regular login (OTP might be for dashboard only)...")
        try:
            jwt = login_and_get_jwt()
            print(f"✅ SUCCESS! Got JWT with regular password")
            
            candidates = get_candidates(job_id="2606114")
            print(f"✅ API call successful! Found {len(candidates.get('data', []))} candidates")
            
        except Exception as e2:
            print(f"❌ Regular login also failed: {e2}")
            
            print(f"\n💡 RECOMMENDATION:")
            print(f"   OTP might be for dashboard login only")
            print(f"   API might use different authentication method")
            print(f"   Check Hireology API documentation")

if __name__ == "__main__":
    test_otp_with_jwt()
