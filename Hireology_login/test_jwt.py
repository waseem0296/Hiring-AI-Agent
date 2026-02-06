from auth_manager import AuthManager
import time

# Initialize AuthManager
auth = AuthManager()

print("\n--- TEST 1: Get JWT first time (or from cache) ---")
# Get JWT for the first time
jwt1 = auth.get_jwt()
print(f"JWT 1 length: {len(jwt1)}")

print("\n--- TEST 2: Reuse cached JWT ---")
# Wait a few seconds and get JWT again
time.sleep(2)
jwt2 = auth.get_jwt()

# Check if the token is reused
if jwt1 == jwt2:
    print("✅ JWT is cached and reused.")
else:
    print("⚠️ JWT was refreshed (probably expired).")

print("\n--- TEST 3: Simulate expiration and refresh ---")
# Simulate expiration
auth.expiry_time = time.time() - 1  # expire immediately
print("Simulated expiration: set expiry_time to past.")

try:
    jwt3 = auth.get_jwt()
    print(f"JWT 3 length: {len(jwt3)}")

    if jwt3 != jwt2:
        print("✅ JWT automatically refreshed after expiration")
    else:
        print("❌ JWT was NOT refreshed even after expiration simulation!")
except Exception as e:
    print(f"❌ Refresh failed during simulation: {e}")
    print("This might be expected if programmatic login is failing and there's no working endpoint.")
