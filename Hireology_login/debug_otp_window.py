import os
import pyotp
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

secret = os.getenv("TOTP_SECRET")
if secret:
    secret = secret.replace(" ", "").upper()

if not secret:
    print("Error: TOTP_SECRET not found in .env")
    exit(1)

totp = pyotp.TOTP(secret)

current_time = int(time.time())
window_start = current_time - 60
window_end = current_time + 60

print(f"Secret Key: {secret}")
print(f"Checking codes in a 2-minute window around {datetime.fromtimestamp(current_time)} UTC")
print("-" * 50)
print(f"{'Time Offset':<15} | {'OTP Code':<10} | {'Remaining'}")
print("-" * 50)

for t in range(window_start, window_end + 1, 30):
    code = totp.at(t)
    offset = t - current_time
    # Use formatted string to show direction
    offset_str = f"{offset:+}s" if offset != 0 else "0s (Now)"
    remaining = 30 - (t % 30)
    print(f"{offset_str:<15} | {code:<10} | {remaining}s")

print("-" * 50)
print(f"Current System Time: {datetime.now().strftime('%H:%M:%S')}")
print(f"Current UTC Time:    {datetime.fromtimestamp(current_time, tz=None).strftime('%H:%M:%S')}")
