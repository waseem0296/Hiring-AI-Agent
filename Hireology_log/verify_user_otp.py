import pyotp
import time

secret = "RNSVPQILCRYTERAO"  # From earlier logs
totp = pyotp.TOTP(secret)

print(f"Current System Time: {time.ctime()}")
print(f"OTP Now: {totp.now()}")

# Check if 773305 was valid in the last 10 minutes or next 10 minutes
target = "773305"
found = False
for i in range(-20, 20):  # 10 mins window (30s steps)
    t = int(time.time()) + (i * 30)
    if totp.at(t) == target:
        print(f"MATCH FOUND! {target} is valid at offset {i*30} seconds from now.")
        found = True
        break

if not found:
    print(f"No match for {target} found in +/- 10 minute window with secret {secret}")
