import os
import pyotp
import time
from dotenv import load_dotenv

load_dotenv()

secret = os.getenv("TOTP_SECRET")
# Clean the secret
if secret:
    secret = secret.replace(" ", "").upper()

if not secret:
    print("Error: TOTP_SECRET not found in .env")
    exit(1)

totp = pyotp.TOTP(secret)

print("-" * 30)
print(f"Secret Key: {secret}")
print(f"Current OTP (System Time): {totp.now()}")
print(f"Time Remaining: {totp.interval - (time.time() % totp.interval):.1f}s")
print("-" * 30)
