import os
import time
import jwt
from GHL_login.ghl_login_full import get_gohighlevel_token
GHL_TOKEN_FILE = os.path.join("GHL_login", "token_output.txt")
EXPIRY_BUFFER_SECONDS = 120
def read_cached_ghl_token():
    if not os.path.exists(GHL_TOKEN_FILE):
        return None
    with open(GHL_TOKEN_FILE, "r") as f:
        return f.read().strip()
def save_ghl_token(token):
    os.makedirs("GHL_login", exist_ok=True)
    with open(GHL_TOKEN_FILE, "w") as f:
        f.write(str(token))
def is_token_valid(token):
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = payload.get("exp")
        if not exp:
            return False

        current_time = int(time.time())
        print("Token will expire in",exp - current_time,"seconds")
        return (exp - current_time) > EXPIRY_BUFFER_SECONDS

    except Exception:
        return False
def get_valid_ghl_token():
    cached_token = read_cached_ghl_token()

    if cached_token and is_token_valid(cached_token):
        print("Using cached GoHighLevel token")
        return cached_token

    print("GoHighLevel token expired or missing → generating new one")
    new_token = get_gohighlevel_token()
    save_ghl_token(new_token)
    return new_token
# if __name__ == "__main__":
#     print("New execution started")

#     ghl_token_id = get_valid_ghl_token()
#     print(ghl_token_id)
