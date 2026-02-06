import requests
from auth_manager import get_jwt, login_and_get_jwt

def authorized_request(method, url, **kwargs):
    jwt = get_jwt()
    print("Using JWT for request:", jwt[:30], "...")  # debug

    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {jwt}"
    headers["Accept"] = "application/json"

    response = requests.request(method, url, headers=headers, **kwargs)

    # 🔥 Token expired → re-login → retry once
    if response.status_code == 401:
        print("JWT expired. Re-logging in...")  # debug
        jwt = login_and_get_jwt()
        headers["Authorization"] = f"Bearer {jwt}"
        response = requests.request(method, url, headers=headers, **kwargs)

    response.raise_for_status()
    return response
