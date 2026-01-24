
import os
import re
import sys
import time
import uuid
import json
import requests
from dotenv import load_dotenv

# Fix Windows console encoding for unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from imap_tools import MailBox, AND

# -----------------------------
# Function: Fetch OTP from Gmail (reliable version)
# -----------------------------
def get_otp_from_gmail(gmail_email, gmail_app_password, wait_time=15):
    """
    Fetch latest 6-digit OTP from Gmail for GHL login.
    """
    print(f"⏳ Waiting {wait_time}s for OTP email...")
    time.sleep(wait_time)
    
    print(f"📨 Connecting to Gmail: {gmail_email}")
    
    try:
        with MailBox("imap.gmail.com").login(gmail_email, gmail_app_password) as mailbox:
            print("✅ Connected to Gmail successfully!")
            
            # First, search by known sender
            messages = list(mailbox.fetch(
                AND(from_="no-reply@gohighlevel.com"),
                reverse=True,
                limit=10
            ))
            
            # If not found, search for subject containing "code" or "verification"
            if not messages:
                messages = list(mailbox.fetch(
                    AND(subject="code"),
                    reverse=True,
                    limit=10
                ))
            
            # Scan messages for 6-digit OTP
            for i, msg in enumerate(messages):
                print(f"\nEmail {i+1}: From {msg.from_}, Subject: {msg.subject}")
                body = msg.text or msg.html or ""
                otp_match = re.search(r"\b\d{6}\b", body)
                if otp_match:
                    otp = otp_match.group()
                    print(f"🎯 OTP FOUND: {otp}")
                    return otp
            
            print("❌ No OTP found in recent emails!")
            raise Exception("OTP not found in email!")

    except Exception as e:
        print(f"⚠ Gmail error: {e}")
        raise Exception(f"Gmail connection error: {e}")


def get_gohighlevel_token():
    """
    Logs into GoHighLevel and returns the authentication token as a string.
    
    Returns:
        str: The authentication token, or None if token could not be retrieved
    """
    # -----------------------------
    # Load environment
    # -----------------------------
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(BASE_DIR, ".env"))

    GHL_EMAIL = os.getenv("GHL_EMAIL")
    GHL_PASSWORD = os.getenv("GHL_PASSWORD")
    GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

    if not GHL_EMAIL or not GHL_PASSWORD or not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        raise ValueError("❌ Missing credentials in .env")

    # -----------------------------
    # Start Chrome for GHL login with network interception
    # -----------------------------
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # Enable performance logging to capture network requests
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 30)

    token = None

    try:
        # 1️⃣ Open GHL login page
        driver.get("https://app.gohighlevel.com/")

        email_input = wait.until(EC.element_to_be_clickable((By.NAME, "email")))
        email_input.send_keys(GHL_EMAIL)

        password_input = wait.until(EC.element_to_be_clickable((By.NAME, "password")))
        password_input.send_keys(GHL_PASSWORD)

        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        login_btn.click()
        print("✅ Login submitted, waiting for OTP page...")
        time.sleep(3)

        # 2️⃣ Click "Send Security Code"
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            btn_text = btn.text.strip().lower()
            if "send" in btn_text or "security" in btn_text or "code" in btn_text:
                btn.click()
                print(f"📨 Clicked OTP button: '{btn.text}'")
                break

        time.sleep(5)

        # # 3️⃣ Fetch OTP from Gmail
        # otp = get_otp_from_gmail(GMAIL_EMAIL, GMAIL_APP_PASSWORD, wait_time=10)
        # print("🔑 OTP fetched:", otp)

        # # 4️⃣ Enter OTP
        # otp_inputs = []
        # for _ in range(30):
        #     time.sleep(1)
        #     inputs = driver.find_elements(By.TAG_NAME, "input")
        #     otp_inputs = [
        #         i for i in inputs
        #         if i.is_displayed() and i.get_attribute("type") in ("text", "tel", "number")
        #     ]
        #     if otp_inputs:
        #         break

        # if not otp_inputs:
        #     raise Exception("❌ OTP input fields not found")

        # if len(otp_inputs) == 1:
        #     otp_inputs[0].send_keys(otp)
        #     otp_inputs[0].send_keys(Keys.ENTER)
        # else:
        #     for i, digit in enumerate(otp):
        #         otp_inputs[i].send_keys(digit)
        #     # After entering all digits, wait a moment and then click verify button
        #     time.sleep(1)
        #     try:
        #         # Look for verify/submit button
        #         verify_btns = driver.find_elements(By.TAG_NAME, "button")
        #         for btn in verify_btns:
        #             btn_text = btn.text.strip().lower()
        #             if any(word in btn_text for word in ['verify', 'submit', 'continue', 'confirm']):
        #                 btn.click()
        #                 print(f"📨 Clicked verify button: '{btn.text}'")
        #                 break
        #     except Exception as e:
        #         print(f"⚠️ Could not click verify button: {e}")
        # print("✅ OTP submitted")
        # -----------------------------
        # 3️⃣ + 4️⃣ OTP Handling with Retry & Network Status Detection
        # -----------------------------

        # Locate OTP input fields ONCE
        otp_inputs = []
        for _ in range(30):
            time.sleep(1)
            inputs = driver.find_elements(By.TAG_NAME, "input")
            otp_inputs = [
                i for i in inputs
                if i.is_displayed() and i.get_attribute("type") in ("text", "tel", "number")
            ]
            if otp_inputs:
                break

        if not otp_inputs:
            raise Exception("❌ OTP input fields not found")

        MAX_RETRIES = 10
        attempt = 0
        otp_verified = False

        while attempt < MAX_RETRIES:
            attempt += 1
            print(f"🔁 OTP Attempt #{attempt}")

            # Fetch new OTP
            otp = get_otp_from_gmail(GMAIL_EMAIL, GMAIL_APP_PASSWORD, wait_time=10)
            print("🔑 OTP fetched:", otp)

            # Clear previous OTP
            for inp in otp_inputs:
                inp.clear()

            # Enter OTP
            if len(otp_inputs) == 1:
                otp_inputs[0].send_keys(otp)
                otp_inputs[0].send_keys(Keys.ENTER)
            else:
                for i, digit in enumerate(otp):
                    otp_inputs[i].send_keys(digit)

            time.sleep(2)

            # Click verify button if present
            for btn in driver.find_elements(By.TAG_NAME, "button"):
                if any(w in btn.text.lower() for w in ['verify', 'submit', 'continue', 'confirm']):
                    btn.click()
                    break

            # ⏳ Wait for backend response
            time.sleep(5)

            # 🔍 Check OTP API response
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    msg = json.loads(entry['message'])['message']

                    if msg.get('method') == 'Network.responseReceived':
                        response = msg.get('params', {}).get('response', {})
                        url = response.get('url', '')
                        status = response.get('status', 0)

                        if '/oauth/2/login/email' in url:
                            print(f"📡 OTP API Status: {status}")

                            if status == 200 or status == 201 or status == 204:
                                print("🎉 OTP VERIFIED SUCCESSFULLY!")
                                otp_verified = True
                                break
                            else:
                                print("❌ OTP INVALID / EXPIRED")

                except Exception:
                    continue

            if otp_verified:
                break

            print("⏳ Waiting 2 minutes before retry...")
            time.sleep(120)

        if not otp_verified:
            raise Exception("❌ OTP verification failed after multiple retries")


        # 5️⃣ Confirm dashboard/app loaded - check for various URL patterns
        print("⏳ Waiting for dashboard to load...")
        time.sleep(5)  # Give extra time for redirect
        
        # Wait for URL to change to any authenticated page
        for attempt in range(30):  # 30 seconds max
            current_url = driver.current_url
            if any(pattern in current_url for pattern in ['/dashboard', '/location/', '/settings', '/v2/', '/launchpad']):
                print(f"🎉 LOGIN SUCCESSFUL! Redirected to: {current_url}")
                break
            time.sleep(1)
        else:
            print(f"⚠️ Current URL: {current_url}")
            # Continue anyway - we might already be logged in

        # -----------------------------
        # 6️⃣ Extract Token-Id from network requests
        # -----------------------------
        time.sleep(3)  # Wait for some API calls to be made
        
        # Navigate to a page that makes API calls to capture the token
        print("🔍 Navigating to trigger API calls...")
        try:
            # Navigate to voice-ai page or any page that makes API calls with token
            current_url = driver.current_url
            location_id = None
            
            # Try to extract location ID from URL if available
            if "/location/" in current_url:
                import re as regex
                match = regex.search(r'/location/([^/]+)', current_url)
                if match:
                    location_id = match.group(1)
            
            # Wait a bit and then capture network logs
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Navigation info: {e}")
        
        # Capture Token-Id from performance logs
        token = None
        print("🔍 Scanning network requests for Token-Id...")
        
        try:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_data = json.loads(entry['message'])
                    message = log_data.get('message', {})
                    
                    # Look for network request headers
                    if message.get('method') == 'Network.requestWillBeSent':
                        request = message.get('params', {}).get('request', {})
                        headers = request.get('headers', {})
                        
                        # Check for Token-Id header (case-insensitive)
                        for header_name, header_value in headers.items():
                            if header_name.lower() == 'token-id':
                                # Validate it looks like a JWT
                                if header_value and header_value.count('.') == 2 and len(header_value) > 100:
                                    print(f"✅ Found Token-Id in network request!")
                                    token = header_value
                                    break
                        
                        if token:
                            break
                            
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error reading performance logs: {e}")
        
        # Method 2: Try to get token from IndexedDB (Firebase auth tokens are often stored there)
        if not token:
            print("🔍 Checking IndexedDB for Firebase token...")
            try:
                # Firebase stores tokens in IndexedDB
                firebase_token = driver.execute_script("""
                    return new Promise((resolve) => {
                        // Check for Firebase auth
                        if (typeof firebase !== 'undefined' && firebase.auth && firebase.auth().currentUser) {
                            firebase.auth().currentUser.getIdToken(true).then(token => {
                                resolve(token);
                            }).catch(err => {
                                resolve(null);
                            });
                        } else {
                            // Try alternative method
                            resolve(null);
                        }
                    });
                """)
                if firebase_token:
                    print("✅ Found Firebase auth token!")
                    token = firebase_token
            except Exception as e:
                print(f"⚠️ Firebase token check error: {e}")
        
        # Method 3: Previous methods (localStorage, sessionStorage, cookies)
        if not token:
            print("🔍 Searching for token in localStorage...")
            token_keys_to_check = [
                'hl-auth-token',
                'auth_token', 
                'authToken',
                'access_token',
                'accessToken',
                'token',
                'jwt',
                'hl_token'
            ]
            
            for key in token_keys_to_check:
                try:
                    value = driver.execute_script(f"return localStorage.getItem('{key}');")
                    if value and value.count('.') == 2 and len(value) > 100:
                        print(f"✅ Found token in localStorage['{key}']")
                        token = value
                        break
                except Exception:
                    continue
        
        # Method 4: Check all localStorage for JWT-like values
        if not token:
            print("🔍 Scanning all localStorage entries...")
            try:
                all_storage = driver.execute_script("""
                    let items = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        items[key] = localStorage.getItem(key);
                    }
                    return items;
                """)
                if all_storage:
                    for key, value in all_storage.items():
                        if value and isinstance(value, str):
                            # Look for JWT-like tokens
                            if value.count('.') == 2 and len(value) > 100:
                                print(f"✅ Found potential JWT token in localStorage['{key}']")
                                token = value
                                break
            except Exception as e:
                print(f"⚠️ Error scanning localStorage: {e}")
        
        # Method 5: Check cookies
        if not token:
            print("🔍 Searching for token in cookies...")
            try:
                cookies = driver.get_cookies()
                for cookie in cookies:
                    name = cookie.get('name', '')
                    value = cookie.get('value', '')
                    
                    # Check for token-like cookies
                    if value and value.count('.') == 2 and len(value) > 100:
                        print(f"✅ Found token in cookie '{name}'")
                        token = value
                        break
            except Exception as e:
                print(f"⚠️ Error checking cookies: {e}")
        
        # Method 6: Intercept by making a request and capturing the header
        if not token:
            print("🔍 Making API call to capture token from headers...")
            try:
                # Execute a fetch request and capture the token from the request
                token = driver.execute_script("""
                    return new Promise((resolve) => {
                        // Store original fetch
                        const originalFetch = window.fetch;
                        let capturedToken = null;
                        
                        // Override fetch to capture token
                        window.fetch = function(...args) {
                            const request = args[1] || {};
                            const headers = request.headers || {};
                            
                            // Check for token in headers
                            for (let key in headers) {
                                if (key.toLowerCase() === 'token-id' || key.toLowerCase() === 'authorization') {
                                    let value = headers[key];
                                    if (value && value.includes('.')) {
                                        capturedToken = value.replace('Bearer ', '');
                                    }
                                }
                            }
                            
                            return originalFetch.apply(this, args);
                        };
                        
                        // Try to get token from existing fetch interceptors or globals
                        if (window.__TOKEN_ID__) {
                            resolve(window.__TOKEN_ID__);
                            return;
                        }
                        
                        // Check for token in various global locations
                        try {
                            // Vue/Nuxt apps
                            if (window.__NUXT__ && window.__NUXT__.state) {
                                const state = window.__NUXT__.state;
                                if (state.auth && state.auth.token) {
                                    resolve(state.auth.token);
                                    return;
                                }
                            }
                            
                            // React apps with Redux
                            if (window.__REDUX_DEVTOOLS_EXTENSION__ || window.__REDUX_STATE__) {
                                // Try to find auth state
                            }
                            
                        } catch(e) {}
                        
                        resolve(capturedToken);
                    });
                """)
            except Exception as e:
                print(f"⚠️ Error in fetch interception: {e}")
        
        if token:
            print(f"🔑 Token extracted successfully!")
            print(f"Token preview: {token[:80]}..." if len(str(token)) > 80 else f"Token: {token}")
        else:
            print("⚠️ Warning: Token not found in browser storage")
            print("📋 Listing available localStorage keys...")
            try:
                keys = driver.execute_script("return Object.keys(localStorage);")
                print(f"localStorage keys: {keys}")
            except:
                pass
            raise Exception("Token extraction failed - no token found in browser storage")

    except Exception as e:
        print(f"❌ Error during login: {e}")
        import traceback
        print("Full error traceback:")
        traceback.print_exc()
        token = None
        
    finally:
        # Close browser
        driver.quit()
    
    return token


# Example usage:
if __name__ == "__main__":
    auth_token = get_gohighlevel_token()
    if auth_token:
        print(f"\n[SUCCESS] Token retrieved successfully!")
        print(f"{auth_token}")
        # Save token to file for verification
        with open("token_output.txt", "w", encoding="utf-8") as f:
            f.write(f"{auth_token}\n")
        print("Token saved to token_output.txt")
    else:
        print("\n[FAILED] Failed to retrieve token")