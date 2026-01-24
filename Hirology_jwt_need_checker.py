import os
from Hireology_login.login import get_hireology_token
import jwt
import time

JWT_CACHE_FILE = ".jwt_cache"

def read_cached_jwt():
    if not os.path.exists(JWT_CACHE_FILE):
        return None
    with open(JWT_CACHE_FILE, "r") as f:
        return f.read().strip()
def save_jwt(token):
    with open(JWT_CACHE_FILE, "w") as f:
        f.write(str(token))


EXPIRY_BUFFER_SECONDS = 120  # 2 minutes

def is_jwt_valid(token):
    try:
        # Decode WITHOUT verifying signature (we only need exp)
        payload = jwt.decode(token, options={"verify_signature": False})

        exp = payload.get("exp")
        if not exp:
            return False
        

        current_time = int(time.time())


        # Check expiry with buffer
        if exp - current_time > EXPIRY_BUFFER_SECONDS:
            print("JWT will expire in", exp - current_time, "seconds")
            return True
        return False

    except jwt.DecodeError:
        return False
    except Exception:
        return False
def get_valid_jwt():
    cached_token = read_cached_jwt()

    if cached_token and is_jwt_valid(cached_token):
        print("Using cached JWT")
        return cached_token

    print("JWT expired or missing → generating new one")
    new_token = get_hireology_token()
    save_jwt(new_token)
    return new_token
# if __name__ == "__main__":
#     print("New execution started")
#     jwt_token = get_valid_jwt()
#     print(jwt_token)
