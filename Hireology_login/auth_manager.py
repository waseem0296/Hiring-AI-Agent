import requests
import os
import base64
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AuthManager:
    # Possible login endpoints to try
    LOGIN_ENDPOINTS = [
        "https://accounts.hireology.com/oauth/token",
        "https://api.hireology.com/v2/auth/login",
        "https://api.hireology.com/v1/auth/login",
        "https://api.hireology.com/oauth/token",
    ]
    
    JWT_CACHE_FILE = ".jwt_cache"

    def __init__(self):
        self._cached_jwt = None
        self.expiry_time = 0
        self.email = os.getenv("HIREOLOGY_EMAIL")
        self.password = os.getenv("HIREOLOGY_PASSWORD")
        self.load_cached_jwt()

    def load_cached_jwt(self):
        """Load JWT from local cache file"""
        if os.path.exists(self.JWT_CACHE_FILE):
            try:
                with open(self.JWT_CACHE_FILE, "r") as f:
                    token = f.read().strip()
                    if token:
                        self._cached_jwt = token
                        # Update expiry_time from the loaded token
                        payload = self.decode_jwt_payload(token)
                        if payload:
                            self.expiry_time = payload.get('exp', 0)
                        print(f"📄 Loaded JWT from {self.JWT_CACHE_FILE}")
                        return self._cached_jwt
            except Exception as e:
                print(f"⚠️  Could not load cached JWT: {e}")
        return None

    def save_jwt_to_cache(self, jwt):
        """Save JWT to local cache file"""
        try:
            with open(self.JWT_CACHE_FILE, "w") as f:
                f.write(jwt)
            print(f"💾 JWT saved to {self.JWT_CACHE_FILE}")
        except Exception as e:
            print(f"⚠️  Could not save JWT to cache: {e}")

    def decode_jwt_payload(self, jwt):
        """Decode JWT payload without verification to check expiration"""
        try:
            parts = jwt.split('.')
            if len(parts) != 3:
                return None
            
            # Add padding if needed
            payload = parts[1]
            padding = '=' * (4 - len(payload) % 4)
            payload += padding
            
            # Decode and parse
            decoded = base64.b64decode(payload)
            return json.loads(decoded)
        except Exception as e:
            print(f"⚠️  Could not decode JWT: {e}")
            return None

    def is_jwt_expired(self, jwt=None):
        """Check if JWT is expired"""
        token = jwt or self._cached_jwt
        if not token:
            return True
        
        # If we have a cached expiry_time, use it (allows simulation)
        if token == self._cached_jwt and self.expiry_time > 0:
            return self.expiry_time <= time.time()
            
        payload = self.decode_jwt_payload(token)
        if not payload:
            return True
        
        exp_timestamp = payload.get('exp', 0)
        return exp_timestamp <= time.time()

    def login_and_get_jwt(self):
        """
        Attempt to login and get a fresh JWT token.
        Tries multiple endpoints and authentication methods.
        """
        print("🔐 Attempting to generate a new JWT...")

        if not self.email or not self.password:
            raise Exception("❌ HIREOLOGY_EMAIL and HIREOLOGY_PASSWORD must be set in .env file")

        # Try different authentication methods
        auth_methods = [
            {
                "name": "OAuth Password Grant",
                "data": {
                    "grant_type": "password",
                    "username": self.email,
                    "password": self.password,
                    "client_id": "api"
                },
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                }
            },
            {
                "name": "OAuth Password Grant (f067e6a3 client)",
                "data": {
                    "grant_type": "password",
                    "username": self.email,
                    "password": self.password,
                    "client_id": "f067e6a3-815d-413d-878e-d223efaa0ca4"
                },
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                }
            },
            {
                "name": "Simple Login",
                "data": {
                    "email": self.email,
                    "password": self.password
                },
                "headers": {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            }
        ]

        last_error = None
        
        # Try each endpoint with each method
        for endpoint in self.LOGIN_ENDPOINTS:
            for method in auth_methods:
                try:
                    print(f"\n🔍 Trying {method['name']} at {endpoint}")
                    
                    if method['headers'].get('Content-Type') == 'application/json':
                        response = requests.post(endpoint, json=method['data'], headers=method['headers'], timeout=10)
                    else:
                        response = requests.post(endpoint, data=method['data'], headers=method['headers'], timeout=10)
                    
                    print(f"   Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        token = (data.get("access_token") or 
                                data.get("token") or 
                                data.get("jwt") or 
                                data.get("id_token"))
                        
                        if token:
                            print(f"✅ Login successful! JWT length: {len(token)}")
                            self._cached_jwt = token
                            payload = self.decode_jwt_payload(token)
                            if payload:
                                self.expiry_time = payload.get('exp', 0)
                            
                            self.save_jwt_to_cache(token)
                            return token
                        else:
                            print(f"   ⚠️  Response didn't contain a token: {list(data.keys())}")
                    
                    elif response.status_code != 404:
                        print(f"   Response: {response.text[:200]}")
                        
                except requests.exceptions.Timeout:
                    print(f"   ⏱️  Timeout")
                    last_error = "Request timeout"
                except requests.exceptions.ConnectionError as e:
                    print(f"   🔌 Connection error")
                    last_error = str(e)
                except Exception as e:
                    print(f"   ❌ Error: {str(e)[:100]}")
                    last_error = str(e)

        error_msg = f"""
❌ Could not authenticate with Hireology API.
Last error: {last_error}

SOLUTION:
1. Get a fresh JWT manually from Hireology dashboard
2. Run: python manual_jwt_update.py
3. Paste the JWT when prompted
"""
        raise Exception(error_msg)

    def get_jwt(self):
        """
        Get JWT token. Uses cached token if available and not expired.
        Otherwise attempts to login and get a fresh token.
        """
        if self._cached_jwt:
            if not self.is_jwt_expired(self._cached_jwt):
                print("✅ Using cached JWT (still valid)")
                return self._cached_jwt
            else:
                print("⚠️  Cached JWT has expired, getting a new one...")
                self._cached_jwt = None

        return self.login_and_get_jwt()

# Backward compatibility functions
_default_manager = AuthManager()

def get_jwt():
    return _default_manager.get_jwt()

def login_and_get_jwt():
    return _default_manager.login_and_get_jwt()

def save_jwt_to_cache(jwt):
    return _default_manager.save_jwt_to_cache(jwt)
