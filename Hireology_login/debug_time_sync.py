#!/usr/bin/env python3
"""
Debug OTP time synchronization issue
"""

import os
import time
import pyotp
from dotenv import load_dotenv
import socket

load_dotenv()

def check_time_sync():
    print("🕐 CHECKING TIME SYNCHRONIZATION")
    print("="*50)
    
    secret = os.getenv("TOTP_SECRET", "").replace(" ", "").upper()
    if not secret:
        print("❌ TOTP_SECRET not found")
        return
    
    totp = pyotp.TOTP(secret)
    
    # Get current OTP
    current_otp = totp.now()
    print(f"📱 Your TOTP: {current_otp}")
    
    # Check system time vs NTP servers
    try:
        # Get time from multiple NTP servers
        time_servers = [
            'pool.ntp.org',
            'time.google.com', 
            'time.cloudflare.com',
            'time.apple.com'
        ]
        
        print(f"\n🌐 Checking NTP time servers...")
        for server in time_servers:
            try:
                client = ntplib.NTPClient(server)
                response = client.request()
                if response:
                    ntp_time = response.tx_time
                    local_time = time.time()
                    time_diff = abs(local_time - ntp_time)
                    
                    print(f"   {server}: {time.strftime('%H:%M:%S', time.gmtime(ntp_time))}")
                    print(f"   Local time: {time.strftime('%H:%M:%S', time.localtime(local_time))}")
                    print(f"   Difference: {time_diff:.2f} seconds")
                    
            except Exception as e:
                print(f"   {server}: Error - {e}")
        
        # Show current Unix timestamp
        print(f"\n⏰ Current Unix timestamp: {time.time()}")
        print(f"⏰ TOTP expects: Unix timestamp (30-second window)")
        
    except Exception as e:
        print(f"❌ Time sync check failed: {e}")
    
    print(f"\n💡 If Hireology shows wrong OTP:")
    print(f"   1. Your system time might be off")
    print(f"   2. Hireology servers might be using different time")
    print(f"   3. Try generating OTP at different times")
    print(f"   4. Check if TOTP secret matches Hireology's")

if __name__ == "__main__":
    check_time_sync()
